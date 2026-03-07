import torch # Force PyTorch to load its DLLs immediately

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database.db import Base, engine
from auth.auth_routes import router as auth_router
from routes.upload_routes import router as upload_router
from routes.chat_routes import router as chat_router
from routes.admin_routes import router as admin_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="College RAG Chatbot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(upload_router)
app.include_router(chat_router)
app.include_router(admin_router)