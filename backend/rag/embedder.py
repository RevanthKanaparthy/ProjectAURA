"""
embedder.py  —  Sentence Embedding Model
=========================================
Uses all-MiniLM-L6-v2 (384-dim) for fast, lightweight embedding.
Compatible with existing ChromaDB collection.
"""

from sentence_transformers import SentenceTransformer

# ---------------------------------------------------------------------------
# Model — loaded once at import time (singleton pattern)
# ---------------------------------------------------------------------------
MODEL_NAME = "all-MiniLM-L6-v2"

print(f"[Embedder] Loading {MODEL_NAME} ...")
model = SentenceTransformer(MODEL_NAME)
print(f"[Embedder] {MODEL_NAME} loaded. Output dim: {model.get_sentence_embedding_dimension()}")


def embed(texts: list[str]):
    """
    Embeds a list of text strings into 384-dim vectors.

    Parameters
    ----------
    texts : List of strings to embed.

    Returns
    -------
    numpy.ndarray of shape (len(texts), 1024), L2-normalized.
    """
    return model.encode(
        texts,
        normalize_embeddings=True,   # enables cosine similarity in ChromaDB
        show_progress_bar=False,
    )