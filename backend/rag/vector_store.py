import chromadb
import uuid
from rag.cog_graph import graph_store
from rag.generator import extract_metadata_from_text
from rag.bm25_store import bm25_store

# Use PersistentClient to ensure data is saved to disk and survives server restarts
client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection("college_docs")

def add_texts(texts, metadatas):
    ids = [str(uuid.uuid4()) for _ in texts]

    # 1. Add to Vector Store (Chroma)
    collection.add(documents=texts, ids=ids, metadatas=metadatas)

    # 2. Add to BM25 Keyword Index (Option A: Hybrid RAG)
    bm25_store.add_texts(texts, ids)
    # print(f"DEBUG: Starting Graph Ingestion for {len(texts)} chunks. This may take a while...")
    # for i, text in enumerate(texts):
    #     if i % 5 == 0:
    #         print(f"DEBUG: Ingesting chunk {i+1}/{len(texts)} into Graph...")
    #     meta = extract_metadata_from_text(text)
    #     graph_store.add_entry(ids[i], meta.get("themes", []), meta.get("entities", []))
    # print("DEBUG: Graph Ingestion Complete.")

def search(query_embedding, top_k=3):
    if collection.count() == 0:
        return {"documents": [[]], "metadatas": [[]], "ids": [[]]}
    return collection.query(
        query_embeddings=[query_embedding.tolist()],
        n_results=min(top_k, collection.count()),
        include=["documents", "metadatas"]
    )

def advanced_search(query_embedding, top_k=3, where_document=None):
    if collection.count() == 0:
        return {"documents": [[]], "metadatas": [[]], "ids": [[]], "distances": [[]]}
    kwargs = {
        "query_embeddings": [query_embedding.tolist()],
        "n_results": top_k,
        "include": ["documents", "metadatas", "distances"]
    }
    if where_document:
        kwargs["where_document"] = where_document
    return collection.query(**kwargs)

def get_documents_by_ids(ids):
    """Fetches actual text content for specific IDs (used by Graph retrieval)."""
    if not ids:
        return [], []
    results = collection.get(ids=ids, include=["documents", "metadatas"])
    return results["documents"], results["metadatas"]

def delete_docs(filename: str):
    """Deletes all vectors associated with a specific filename."""
    collection.delete(where={"source": filename})