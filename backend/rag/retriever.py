"""
retriever.py  —  Hybrid RAG Retrieval (Vector + BM25 → RRF)
=============================================================
2026 Production Upgrade: adds BM25 keyword search alongside the existing
ChromaDB vector search, fused with Reciprocal Rank Fusion (RRF).

Pipeline:
  1. Dense retrieval  — ChromaDB cosine similarity (top-10)
  2. Sparse retrieval — BM25 keyword search (top-10)
  3. RRF fusion       — merges both ranked lists, deduplicates, returns top-10
  4. Context assembly — joins unique docs into a single context string

RRF Formula:
  score(d) = Σ  1 / (k + rank_i(d))
  where k=60 (standard constant) and rank_i is the position in list i.
"""

from rag.embedder import embed
from rag.vector_store import search, get_documents_by_ids
from rag.bm25_store import bm25_store

# RRF constant — 60 is the standard value used in the literature
_RRF_K = 60
# Number of candidates to fetch from each retriever before fusion
_CANDIDATES = 10
# Final top-k to return after fusion
_TOP_K_FINAL = 10


def _reciprocal_rank_fusion(
    vector_ids: list[str],
    bm25_results: list[tuple[str, float]],
    k: int = _RRF_K,
) -> list[str]:
    """
    Fuses two ranked lists using Reciprocal Rank Fusion.

    Parameters
    ----------
    vector_ids   : Ordered list of chunk IDs from vector search (best first).
    bm25_results : List of (chunk_id, bm25_score) from BM25 search (best first).
    k            : RRF smoothing constant (default 60).

    Returns
    -------
    Deduplicated list of chunk IDs, ordered by fused RRF score (best first).
    """
    scores: dict[str, float] = {}

    # Vector search contribution
    for rank, doc_id in enumerate(vector_ids, start=1):
        scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank)

    # BM25 search contribution
    for rank, (doc_id, _) in enumerate(bm25_results, start=1):
        scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank)

    return sorted(scores.keys(), key=lambda d: scores[d], reverse=True)


def retrieve_context_with_sources(question: str, top_k: int = _TOP_K_FINAL):
    """
    Hybrid RAG: runs vector + BM25 retrieval in parallel, fuses with RRF,
    and returns a (context_string, sources) tuple.

    Parameters
    ----------
    question : User query string.
    top_k    : Number of final chunks to include in the context.

    Returns
    -------
    context : str  — Concatenated chunk texts (deduplicated).
    sources : list — Source file names from chunk metadata.
    """
    print(f"[Retriever] Hybrid RAG query: '{question[:80]}'")

    # ── Phase 1: Dense Vector Retrieval ─────────────────────────────
    q_emb = embed([question])[0]
    vector_results = search(q_emb, top_k=_CANDIDATES)

    v_docs  = vector_results.get("documents", [[]])[0]
    v_metas = vector_results.get("metadatas", [[]])[0]
    v_ids   = vector_results.get("ids", [[]])[0]

    print(f"[Retriever] Vector: {len(v_docs)} chunks retrieved.")

    # ── Phase 2: BM25 Keyword Retrieval ─────────────────────────────
    bm25_results = []
    if bm25_store.is_ready:
        bm25_results = bm25_store.search(question, top_k=_CANDIDATES)
        print(f"[Retriever] BM25: {len(bm25_results)} chunks retrieved.")
    else:
        print("[Retriever] BM25 index not ready — using vector-only retrieval.")

    # ── Phase 3: RRF Fusion ──────────────────────────────────────────
    if bm25_results:
        fused_ids = _reciprocal_rank_fusion(v_ids, bm25_results)[:top_k]

        # Fetch texts for any BM25 IDs not already in vector results
        vector_id_set = set(v_ids)
        extra_ids = [cid for cid in fused_ids if cid not in vector_id_set]

        # Map vector results by id for O(1) lookup
        vector_map = {cid: (doc, meta) for cid, doc, meta in zip(v_ids, v_docs, v_metas)}

        if extra_ids:
            extra_docs, extra_metas = get_documents_by_ids(extra_ids)
            for cid, doc, meta in zip(extra_ids, extra_docs, extra_metas):
                vector_map[cid] = (doc, meta)

        # Assemble in fused order
        all_docs  = []
        all_metas = []
        for cid in fused_ids:
            if cid in vector_map:
                doc, meta = vector_map[cid]
                all_docs.append(doc)
                all_metas.append(meta)

        print(f"[Retriever] RRF fused: {len(all_docs)} final chunks.")
    else:
        # Fallback: pure vector results
        all_docs  = v_docs[:top_k]
        all_metas = v_metas[:top_k]

    # ── Phase 4: Build Context ───────────────────────────────────────
    unique_docs = list(dict.fromkeys(all_docs))   # preserve order, deduplicate
    context = "\n\n".join(unique_docs)
    sources = list(dict.fromkeys(
        m.get("source", "Unknown") for m in all_metas
    ))

    return context, sources