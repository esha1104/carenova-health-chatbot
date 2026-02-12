from langchain_openai import ChatOpenAI
from logger import get_logger
from config import (
    LLM_MODEL,
    LLM_TEMPERATURE,
    LLM_MAX_TOKENS,
    OPENROUTER_API_KEY,
    OPENROUTER_BASE_URL
)

logger = get_logger(__name__)

llm = None

try:
    if not OPENROUTER_API_KEY:
        raise ValueError("OPENROUTER_API_KEY not configured")
    
    # Initialize OpenRouter LLM via OpenAI-compatible API
    llm = ChatOpenAI(
        model=LLM_MODEL,
        api_key=OPENROUTER_API_KEY,
        base_url=OPENROUTER_BASE_URL,
        temperature=LLM_TEMPERATURE,
        max_tokens=LLM_MAX_TOKENS,
        timeout=60
    )
    logger.info(f"✅ LLM initialized with OpenRouter: {LLM_MODEL}")
except Exception as e:
    logger.error(f"❌ Failed to initialize LLM: {e}")
    llm = None


def get_llm():
    """Get LLM instance with error handling."""
    if llm is None:
        raise RuntimeError(
            "LLM not initialized. Check OPENROUTER_API_KEY in .env is set correctly."
        )
    return llm
