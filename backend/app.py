import torch  # Force PyTorch to load its DLLs immediately
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import ALLOWED_ORIGINS
from database.db import Base, engine
from auth.auth_routes import router as auth_router
from routes.upload_routes import router as upload_router
from routes.chat_routes import router as chat_router
from routes.admin_routes import router as admin_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting College RAG Chatbot API...")
    
    # Create database tables on startup
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized.")
    
    yield
    
    logger.info("Shutting down College RAG Chatbot API...")

# Initialize FastAPI app
app = FastAPI(
    title="College RAG Chatbot API",
    description="RAG-based chatbot for college document analysis",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS with restricted origins
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=".*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests."""
    logger.info(f"{request.method} {request.url.path}")
    response = await call_next(request)
    logger.info(f"Response status: {response.status_code}")
    return response

# Include routers
app.include_router(auth_router)
app.include_router(upload_router)
app.include_router(chat_router)
app.include_router(admin_router)

# Health check endpoints
@app.get("/")
async def root():
    return {"status": "ok", "message": "College RAG Chatbot API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
