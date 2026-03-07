from fastapi import APIRouter
from rag.retriever import retrieve_context_with_sources
from rag.generator import generate_answer

router = APIRouter(prefix="/chat", tags=["Chat"])

@router.post("/ask")
def ask_question(question: str):
    context, sources = retrieve_context_with_sources(question)
    answer = generate_answer(context, question)

    return {
        "question": question,
        "answer": answer,
        "sources": sources
    }