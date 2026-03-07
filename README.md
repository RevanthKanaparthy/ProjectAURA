# College RAG-Based Chatbot

This project implements a Retrieval-Augmented Generation (RAG) based chatbot for a college website.
Faculty can upload documents, and users can query information using natural language.

## Tech Stack
- Backend: FastAPI (Python)
- Database: PostgreSQL
- Vector DB: ChromaDB
- LLM: Ollama (Llama3)
- Frontend: HTML, CSS, JavaScript

## Features
- Faculty/Admin login
- Faculty document upload
- Admin control
- RAG-based question answering
- Simple web chat UI

## How to Run
1. Start PostgreSQL and create database `college_rag`
2. Start Ollama: `ollama run llama3`
3. Run backend: `uvicorn app:app --reload`
4. Open `frontend/login.html` in browser