"""
bm25_store.py  —  In-Memory BM25 Keyword Index
================================================
Provides fast keyword-based retrieval alongside the ChromaDB vector search.
Used by retriever.py to implement Hybrid RAG with Reciprocal Rank Fusion (RRF).

The BM25Store is a singleton that is built during document ingestion and
persisted in memory for the lifetime of the server process.

Usage:
    from rag.bm25_store import bm25_store

    # During ingestion (called from vector_store.add_texts):
    bm25_store.add_texts(texts, ids)

    # During retrieval:
    results = bm25_store.search("ECE faculty publications 2025", top_k=10)
    # → [("chunk-uuid-1", 4.21), ("chunk-uuid-2", 3.87), ...]
"""

import re
from typing import Optional

try:
    from rank_bm25 import BM25Plus
    _BM25_AVAILABLE = True
except ImportError:
    _BM25_AVAILABLE = False
    print("[BM25Store] WARNING: rank-bm25 not installed. BM25 retrieval disabled.")
    print("            Run: pip install rank-bm25")


def _tokenize(text: str) -> list[str]:
    """Simple whitespace + lowercase tokenizer, strips punctuation."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return [tok for tok in text.split() if len(tok) > 1]


class BM25Store:
    """
    In-memory BM25 index over all ingested document chunks.

    Thread-safety: Not thread-safe for concurrent writes. Since ingestion
    is typically a single-user admin operation, this is acceptable.
    """

    def __init__(self):
        self._texts: list[str] = []
        self._ids: list[str] = []
        self._index: Optional[object] = None  # BM25Okapi instance

    # ──────────────────────────────────────────────
    # Build / Update
    # ──────────────────────────────────────────────
    def add_texts(self, texts: list[str], ids: list[str]) -> None:
        """
        Add new texts+ids to the store and rebuild the BM25 index.
        Called from vector_store.add_texts() during every ingestion.
        """
        if not _BM25_AVAILABLE:
            return

        self._texts.extend(texts)
        self._ids.extend(ids)
        self._rebuild_index()
        print(f"[BM25Store] Index rebuilt with {len(self._texts)} total chunks.")

    def build(self, texts: list[str], ids: list[str]) -> None:
        """
        Replaces the entire index. Used for full re-ingestion / migration.
        """
        if not _BM25_AVAILABLE:
            return

        self._texts = list(texts)
        self._ids = list(ids)
        self._rebuild_index()
        print(f"[BM25Store] Full index built with {len(self._texts)} chunks.")

    def clear(self) -> None:
        """Resets the index. Call before re-ingesting all documents."""
        self._texts = []
        self._ids = []
        self._index = None
        print("[BM25Store] Index cleared.")

    def _rebuild_index(self) -> None:
        tokenized = [_tokenize(t) for t in self._texts]
        self._index = BM25Plus(tokenized)

    # ──────────────────────────────────────────────
    # Search
    # ──────────────────────────────────────────────
    def search(self, query: str, top_k: int = 10) -> list[tuple[str, float]]:
        """
        Returns top-k (chunk_id, bm25_score) pairs for the query.
        Returns empty list if index is not built or bm25 is unavailable.
        """
        if not _BM25_AVAILABLE or self._index is None or not self._texts:
            return []

        tokens = _tokenize(query)
        if not tokens:
            return []

        scores = self._index.get_scores(tokens)

        # Pair ids with scores, sort descending, return top-k
        ranked = sorted(
            zip(self._ids, scores),
            key=lambda x: x[1],
            reverse=True
        )
        # Filter out zero-score results (no keyword overlap)
        return [(cid, float(score)) for cid, score in ranked[:top_k] if score > 0]

    @property
    def is_ready(self) -> bool:
        """True if the index has been built and is ready to search."""
        return _BM25_AVAILABLE and self._index is not None and len(self._texts) > 0

    @property
    def size(self) -> int:
        """Number of chunks currently indexed."""
        return len(self._texts)


# ──────────────────────────────────────────────
# Module-level singleton — imported everywhere
# ──────────────────────────────────────────────
bm25_store = BM25Store()
