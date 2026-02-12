import json
import os
import pickle
import numpy as np
import faiss
from langchain_openai import OpenAIEmbeddings
from pydantic import SecretStr
from llm import get_llm
from logger import get_logger
from config import (
    FAISS_INDEX_DIR,
    EMBEDDINGS_MODEL,
    RAG_SCORE_THRESHOLD,
    RAG_K_RESULTS,
    RAG_CACHE_ENABLED,
    OPENROUTER_API_KEY,
    OPENROUTER_BASE_URL
)

logger = get_logger(__name__)

# Simple in-memory cache for RAG responses
_rag_cache = {}

class SimpleRetriever:
    def __init__(self, index_dir, embeddings):
        self.index = faiss.read_index(os.path.join(index_dir, "index.faiss"))
        with open(os.path.join(index_dir, "chunks.pkl"), "rb") as f:
            self.chunks = pickle.load(f)
        self.embeddings = embeddings

    def invoke(self, query: str):
        query_emb = np.array([self.embeddings.embed_query(query)]).astype('float32')
        # We'll use IndexFlatL2 distance (lower is better)
        # To simulate a threshold, we'd need to convert distance to score
        distances, indices = self.index.search(query_emb, RAG_K_RESULTS)
        
        docs = []
        for i, dist in zip(indices[0], distances[0]):
            if i != -1:
                # Simple heuristic to simulate score threshold
                # FlatL2 distance increases with dissimilarity
                # This is just a basic implementation
                docs.append(self.chunks[i])
        return docs

# Initialize embeddings using OpenRouter (via OpenAI-compatible API)
try:
    if not OPENROUTER_API_KEY:
        raise ValueError("OPENROUTER_API_KEY not set in .env")
    
    embeddings = OpenAIEmbeddings(
        api_key=SecretStr(OPENROUTER_API_KEY),
        model=EMBEDDINGS_MODEL,
        base_url=OPENROUTER_BASE_URL
    )
    logger.info(f"✅ Using OpenRouter for embeddings: {EMBEDDINGS_MODEL}")
    
    # Load FAISS vector store
    if os.path.exists(FAISS_INDEX_DIR) and os.path.exists(os.path.join(FAISS_INDEX_DIR, "index.faiss")):
        retriever = SimpleRetriever(FAISS_INDEX_DIR, embeddings)
        logger.info(f"✅ Vector DB initialized from {FAISS_INDEX_DIR}")
    else:
        logger.warning(f"⚠️  Vector DB directory {FAISS_INDEX_DIR} or index files not found. Retrieval will be disabled.")
        retriever = None
except Exception as e:
    logger.error(f"❌ Failed to initialize vector DB: {e}")
    retriever = None


def rag_answer(query: str) -> dict:
    """
    Retrieve and analyze medical context for given query.
    Uses caching to avoid redundant vector DB lookups.
    """
    raw_response = ""  # Initialize to avoid unbound variable error
    
    # Check cache
    if RAG_CACHE_ENABLED and query in _rag_cache:
        import hashlib
        query_hash = hashlib.md5(query.encode()).hexdigest()[:10]
        logger.debug(f"📦 Cache hit for query id: {query_hash}")
        return _rag_cache[query]
    
    # Fallback if retriever not initialized
    if retriever is None:
        logger.warning("⚠️  Vector DB not available, using fallback")
        return {
            "possible_conditions": ["Medical evaluation recommended"],
            "explanation": ["Vector database unavailable."],
            "home_care_tips": ["Rest", "Stay hydrated", "Monitor symptoms"],
            "when_to_see_doctor": ["Consult a healthcare professional."],
            "disclaimer": "This is not a medical diagnosis."
        }

    try:
        docs = retriever.invoke(query)
        logger.info(f"📄 Retrieved {len(docs)} documents for query")

        if not docs:
            logger.warning(f"⚠️  No documents matched query threshold")
            return {
                "possible_conditions": ["Medical evaluation recommended"],
                "explanation": ["No strong medical matches found."],
                "home_care_tips": ["Rest", "Stay hydrated", "Monitor symptoms"],
                "when_to_see_doctor": ["If symptoms persist or worsen."],
                "disclaimer": "This is not a medical diagnosis."
            }

        context = "\n\n".join(
            f"Source: {doc.metadata.get('source','unknown')}\n{doc.page_content}"
            for doc in docs
        )

        prompt = f"""
You are Carenova, a cautious AI healthcare assistant.

STRICT RULES:
- Use ONLY the medical context
- Never invent diseases
- Never confirm a diagnosis
- Never prescribe medication
- Provide safe guidance only

Medical Context:
{context}

User Symptoms:
{query}

Return ONLY valid JSON.

Schema:

{{
"possible_conditions": ["condition1","condition2"],
"explanation": ["reason linking symptom → condition"],
"home_care_tips": ["safe practical advice"],
"when_to_see_doctor": ["clear warning signs"],
"disclaimer": "This is not a medical diagnosis. Consult a healthcare professional."
}}

IMPORTANT:
- Suggest ONLY 2–4 conditions
- No markdown
- No extra commentary
- Output MUST be valid JSON
"""

        llm = get_llm()
        response_message = llm.invoke(prompt)
        raw_response = response_message.content if hasattr(response_message, 'content') else str(response_message)
        
        logger.debug(f"🤖 LLM response received: {len(raw_response)} chars")

        # Clean response
        raw_response = raw_response.strip() if isinstance(raw_response, str) else str(raw_response).strip()

        result = json.loads(raw_response)
        
        # Cache result
        if RAG_CACHE_ENABLED:
            _rag_cache[query] = result
        
        logger.info(f"✅ Analysis complete: {', '.join(result.get('possible_conditions', []))}")
        return result

    except json.JSONDecodeError as e:
        logger.error(f"❌ JSON parse error: {e}")
        # Use content attribute if it's an AIMessage object, otherwise string slice
        error_snippet = raw_response[:200] if isinstance(raw_response, str) else "Unable to display response"
        logger.error(f"Raw response: {error_snippet}")
        
        return {
            "possible_conditions": ["Medical evaluation recommended"],
            "explanation": ["The system could not parse the medical analysis response."],
            "home_care_tips": ["Rest", "Stay hydrated", "Monitor symptoms"],
            "when_to_see_doctor": ["If symptoms worsen or persist."],
            "disclaimer": "This is not a medical diagnosis."
        }
    
    except Exception as e:
        logger.error(f"❌ Unexpected error in rag_answer: {e}")
        return {
            "possible_conditions": ["Medical evaluation recommended"],
            "explanation": ["System error occurred."],
            "home_care_tips": ["Rest", "Stay hydrated", "Monitor symptoms"],
            "when_to_see_doctor": ["Seek immediate medical attention if severe."],
            "disclaimer": "This is not a medical diagnosis."
        }
