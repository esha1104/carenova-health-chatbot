"""
Centralized configuration management.
Reads from .env file and environment variables.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
ENV_FILE = Path(__file__).parent / ".env"
if ENV_FILE.exists():
    load_dotenv(ENV_FILE)

# ============= SERVER CONFIG =============
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 8000))
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# ============= LLM CONFIG (OpenRouter) =============
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", "meta-llama/llama-3-8b-instruct:free")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.1"))
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "512"))
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# ============= EMBEDDINGS CONFIG =============
# Using OpenRouter/OpenAI compatible API for embeddings
EMBEDDINGS_MODEL = os.getenv("EMBEDDINGS_MODEL", "text-embedding-3-small")

# ============= DATABASE CONFIG =============
FAISS_INDEX_DIR = os.getenv("FAISS_INDEX_DIR", "faiss_index")
MEDICAL_KNOWLEDGE_PATH = os.getenv("MEDICAL_KNOWLEDGE_PATH", "medical_knowledge")

# ============= RAG CONFIG =============
RAG_SCORE_THRESHOLD = float(os.getenv("RAG_SCORE_THRESHOLD", "0.55"))
RAG_K_RESULTS = int(os.getenv("RAG_K_RESULTS", "5"))
RAG_CACHE_ENABLED = os.getenv("RAG_CACHE_ENABLED", "True").lower() == "true"

# ============= SESSION CONFIG =============
SESSION_TIMEOUT_MINUTES = int(os.getenv("SESSION_TIMEOUT_MINUTES", "30"))
MAX_FOLLOWUP_QUESTIONS = int(os.getenv("MAX_FOLLOWUP_QUESTIONS", "3"))

# ============= API CONFIG =============
ENABLE_CORS = os.getenv("ENABLE_CORS", "True").lower() == "true"
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8000").split(",")
RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "10"))

# ============= VALIDATION =============
def validate_config():
    """Verify critical settings are configured."""
    errors = []
    
    # Check OpenRouter API key (required for all LLM + embeddings)
    if not OPENROUTER_API_KEY:
        errors.append("❌ OPENROUTER_API_KEY not set in .env")
    else:
        print(f"✅ OpenRouter API key configured")
    
    # Check vector DB exists
    if not Path(FAISS_INDEX_DIR).exists():
        print(f"⚠️  Vector database not found at {FAISS_INDEX_DIR}. Run: python ingest.py")
    else:
        print(f"✅ Vector database found")
    
    # Check medical docs
    if not Path(MEDICAL_KNOWLEDGE_PATH).exists():
        errors.append(f"❌ Medical knowledge path does not exist: {MEDICAL_KNOWLEDGE_PATH}")
    else:
        print(f"✅ Medical knowledge directory found")
    
    if errors:
        print("\n".join(errors))
        if "OPENROUTER_API_KEY" in "\n".join(errors):
            raise ValueError("Missing critical configuration. See .env.example for setup instructions.")
    
    return len(errors) == 0

# Run validation on import
try:
    validate_config()
except ValueError as e:
    print(f"⚠️  Configuration error: {e}")
