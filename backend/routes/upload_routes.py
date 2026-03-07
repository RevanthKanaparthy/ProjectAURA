from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
import os

from config import UPLOAD_DIR
from database.db import SessionLocal
from database.models import Document, User
from auth.auth_utils import get_current_user
from rag.loader import load_document
from rag.chunker import chunk_text
from rag.embedder import embed
from rag.vector_store import add_texts

router = APIRouter(prefix="/upload", tags=["Upload"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/")
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    file_path = os.path.join(UPLOAD_DIR, file.filename)

    # Check if a document with the same name already exists
    if db.query(Document).filter(Document.filename == file.filename).first():
        raise HTTPException(status_code=400, detail="A document with this name already exists.")

    with open(file_path, "wb") as f:
        f.write(await file.read())

    try:
        text = load_document(file_path)
        if not text or not text.strip():
            raise HTTPException(status_code=400, detail="Document is empty or could not be read.")

        chunks = chunk_text(text)
        if not chunks:
            raise HTTPException(status_code=400, detail="Document could not be chunked.")
            
        metadatas = [{"source": file.filename} for _ in chunks]

        add_texts(chunks, metadatas)

        # Add document to the database
        db_document = Document(filename=file.filename, uploaded_by=current_user.id)
        db.add(db_document)
        db.commit()

        return {"message": "File uploaded and indexed successfully", "chunks": len(chunks)}
    
    except Exception as e:
        # Clean up the uploaded file if any step fails
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"An error occurred during processing: {e}")
