def chunk_text(text: str, chunk_size: int = 2000, overlap: int = 200):
    """
    Splits text into chunks, respecting newline boundaries to avoid breaking
    structured data rows (like Excel records).
    """
    if not text:
        return []
        
    chunks = []
    text_len = len(text)
    start = 0
    
    while start < text_len:
        # Calculate end of the chunk
        end = min(start + chunk_size, text_len)
        
        # Try to align 'end' to a newline to avoid splitting a row
        if end < text_len:
            newline_pos = text.rfind('\n', start, end)
            if newline_pos != -1:
                end = newline_pos + 1  # Include the newline
        
        chunks.append(text[start:end])
        
        if end == text_len:
            break
            
        # Align next start to a newline to ensure the next chunk starts cleanly
        target_start = max(start + 1, end - overlap)
        newline_pos = text.rfind('\n', start, target_start)
        if newline_pos != -1:
            start = newline_pos + 1
        else:
            start = target_start
            
    return chunks