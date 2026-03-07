from rag.embedder import embed
from rag.vector_store import search, get_documents_by_ids
from rag.cog_graph import graph_store
from rag.generator import extract_metadata_from_text

def retrieve_context_with_sources(question: str, top_k: int = 5):
    print(f"DEBUG: Starting retrieval for: '{question}'")
    
    # --- Phase 1: Dense Vector Retrieval (Naive RAG) ---
    q_emb = embed([question])[0]
    vector_results = search(q_emb, top_k)
    
    v_docs = vector_results.get("documents", [[]])[0]
    v_metas = vector_results.get("metadatas", [[]])[0]
    print(f"DEBUG: Phase 1 (Vector) found {len(v_docs)} docs.")

    # --- Phase 2: Cognitive Graph Retrieval (Cog-RAG) ---
    # DISABLED: Reverting to Standard RAG for performance.
    # print("DEBUG: Phase 2 (Graph) starting...")
    g_docs, g_metas = [], []
    
    # try:
    #     # Extract themes/entities from the user's question
    #     q_meta = extract_metadata_from_text(question)
    #     print(f"DEBUG: Extracted query metadata: {q_meta}")
        
    #     # Find chunks in the graph linked to these themes/entities
    #     graph_ids = graph_store.find_related_chunks(q_meta.get("themes", []), q_meta.get("entities", []))
    #     print(f"DEBUG: Found {len(graph_ids)} related chunks in graph.")
        
    #     # Fetch the actual text for these graph-discovered chunks
    #     if graph_ids:
    #         g_docs, g_metas = get_documents_by_ids(graph_ids[:top_k]) # Limit graph results
    # except Exception as e:
    #     print(f"ERROR: Graph Retrieval failed (falling back to Naive RAG): {e}")

    # --- Phase 3: Hybrid Merge ---
    # Combine and deduplicate
    all_docs = v_docs + g_docs
    all_metas = v_metas + g_metas
    
    # Format context
    unique_docs = list(set(all_docs))
    context = "\n\n".join(unique_docs)
    sources = list(set([m.get("source", "Unknown") for m in all_metas]))

    return context, sources