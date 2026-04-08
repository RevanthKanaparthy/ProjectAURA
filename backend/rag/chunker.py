"""
chunker.py  —  Recursive Character Text Splitter
==================================================
2026 Production Upgrade: replaces fixed-size char split with LangChain's
RecursiveCharacterTextSplitter, which respects natural text boundaries
(paragraph → sentence → row separator → word).

Chunk size targets ~512 tokens using the heuristic 1 token ≈ 4 chars:
  chunk_size   = 2048 chars  ≈ 512 tokens
  chunk_overlap =  205 chars  ≈ 10% overlap

The separator list is ordered from coarsest to finest, and includes " | "
to respect the "key: value | key: value" row format produced by loader.py.
"""

from langchain_text_splitters import RecursiveCharacterTextSplitter

# ---------------------------------------------------------------------------
# Default splitter — used by loader pipeline and ingest routes
# ---------------------------------------------------------------------------
_SEPARATORS = ["\n\n", "\n", " | ", ". ", " ", ""]

_DEFAULT_SPLITTER = RecursiveCharacterTextSplitter(
    chunk_size=2048,       # ≈ 512 tokens (4 chars/token heuristic)
    chunk_overlap=205,     # ≈ 10% overlap
    separators=_SEPARATORS,
    length_function=len,
    is_separator_regex=False,
)


def chunk_text(text: str, chunk_size: int = 2048, overlap: int = 205) -> list[str]:
    """
    Splits text into overlapping chunks using recursive character splitting.

    Parameters
    ----------
    text        : Raw text to split.
    chunk_size  : Maximum chunk size in characters (default 2048 ≈ 512 tokens).
    overlap     : Overlap between consecutive chunks in characters (default 205 ≈ 10%).

    Returns
    -------
    List of non-empty chunk strings.
    """
    if not text or not text.strip():
        return []

    # Use default splitter if default params are requested (avoids re-building)
    if chunk_size == 2048 and overlap == 205:
        splitter = _DEFAULT_SPLITTER
    else:
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=overlap,
            separators=_SEPARATORS,
            length_function=len,
            is_separator_regex=False,
        )

    chunks = splitter.split_text(text)
    # Filter out whitespace-only chunks that occasionally appear after splitting
    return [c for c in chunks if c.strip()]