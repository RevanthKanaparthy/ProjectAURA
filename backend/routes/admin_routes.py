from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import os

from database.db import SessionLocal
from database.models import Document, User
from auth.auth_utils import get_current_user
from config import UPLOAD_DIR
from rag.vector_store import delete_docs

router = APIRouter(prefix="/admin", tags=["Admin"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def require_admin(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admins only")

@router.get("/docs", dependencies=[Depends(require_admin)])
def list_docs(db: Session = Depends(get_db)):
    docs = db.query(Document).all()
    return [{"id": d.id, "filename": d.filename} for d in docs]

@router.delete("/docs/{doc_id}", dependencies=[Depends(require_admin)])
def delete_doc(doc_id: int, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # delete file from disk
    file_path = os.path.join(UPLOAD_DIR, doc.filename)
    if os.path.exists(file_path):
        os.remove(file_path)

    # Remove embeddings from vector store so the chatbot forgets this document
    try:
        delete_docs(doc.filename)
    except Exception as e:
        print(f"Error deleting from vector store: {e}")

    db.delete(doc)
    db.commit()
    return {"message": "Document deleted"}
