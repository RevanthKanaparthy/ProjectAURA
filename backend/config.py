import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv()

# ==================== REQUIRED CONFIGURATION ====================
# These must be set in environment variables or .env file

def _get_required_env(var_name: str) -> str:
    """Get required environment variable or raise error if not set."""
    value = os.getenv(var_name)
    if not value:
        raise ValueError(f"Required environment variable {var_name} is not set. Please configure it in .env file.")
    return value

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL must be set in environment variables")

# Security
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("SECRET_KEY must be set in environment variables")

ALGORITHM = "HS256"

# File Storage
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "storage/uploads")

# LLM Configuration
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openrouter")

# Ollama (Local LLM)
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")

# OpenRouter (Alternative LLM Provider)
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "stepfun/step-3.5-flash:free")

# Google Gemini (Primary LLM Provider)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

# Nebius AI (Advanced Hybrid RAG Provider)
NEBIUS_API_KEY = os.getenv("NEBIUS_API_KEY")
LLM_CHAT_MODEL = os.getenv("LLM_CHAT_MODEL", "meta-llama/Llama-3.3-70B-Instruct")
TOP_K_RESULTS = int(os.getenv("TOP_K_RESULTS", "5"))

# ==================== CORS CONFIGURATION ====================
# Define allowed origins - customize for your deployment
ALLOWED_ORIGINS = [origin.strip() for origin in os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:5500").split(",")]

# ==================== RATE LIMITING ====================
RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
RATE_LIMIT_LOGIN_PER_MINUTE = int(os.getenv("RATE_LIMIT_LOGIN_PER_MINUTE", "10"))

# ==================== EXCEL HANDLER CONFIG ====================
DATA_DIR = Path(os.getenv("DATA_DIR", "storage/data"))
EXCEL_STORE_PATH = DATA_DIR / "canonical_store.xlsx"
CANONICAL_SHEET_NAME = "All"
COLUMN_TYPO_FIXES = {
    "title_of_publicaion": "title_of_publication",
    "dept.": "department",
}
