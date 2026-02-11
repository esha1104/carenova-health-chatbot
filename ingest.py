import os
import shutil
from pathlib import Path
from pydantic import SecretStr
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from logger import get_logger
from config import (
    MEDICAL_KNOWLEDGE_PATH,
    FAISS_INDEX_DIR,
    EMBEDDINGS_MODEL,
    OPENROUTER_API_KEY,
    OPENROUTER_BASE_URL,
)

logger = get_logger(__name__)

def load_markdown_files(data_path: str) -> list:
    """Load all markdown files from a directory hierarchy."""
    documents = []
    data_dir = Path(data_path)
    
    if not data_dir.exists():
        logger.warning(f"📁 Data path does not exist: {data_path}")
        return documents
    
    for md_file in data_dir.rglob("*.md"):
        try:
            content = md_file.read_text(encoding="utf-8")
            doc = Document(
                page_content=content,
                metadata={"source": md_file.name}
            )
            documents.append(doc)
            logger.debug(f"✓ Loaded: {md_file.name}")
        except Exception as e:
            logger.warning(f"⚠️  Failed to load {md_file.name}: {e}")
    
    return documents

def ingest_documents():
    """Load documents, chunk, and create FAISS vector DB using OpenRouter embeddings."""
    
    # ✅ Delete OLD DB FIRST
    if os.path.exists(FAISS_INDEX_DIR):
        logger.info(f"🗑️  Deleting old vector database at {FAISS_INDEX_DIR}...")
        shutil.rmtree(FAISS_INDEX_DIR, ignore_errors=True)

    logger.info("📄 Loading markdown files...")
    documents = load_markdown_files(MEDICAL_KNOWLEDGE_PATH)
    
    if not documents:
        logger.error(f"❌ No documents found in {MEDICAL_KNOWLEDGE_PATH}")
        return
    
    logger.info(f"✅ Loaded {len(documents)} documents")

    # ✅ Medical-optimized chunking
    logger.info("✂️  Chunking documents...")
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100,
        separators=["\n## ", "\n### ", "\n- ", "\n", " "],
    )
    chunks = splitter.split_documents(documents)
    logger.info(f"✅ Created {len(chunks)} chunks")

    # Initialize OpenRouter embeddings (via OpenAI-compatible API)
    try:
        if not OPENROUTER_API_KEY:
            raise ValueError("OPENROUTER_API_KEY not set in .env")
        
        logger.info(f"🔑 Using OpenRouter for embeddings: {EMBEDDINGS_MODEL}")
        embeddings = OpenAIEmbeddings(
            api_key=SecretStr(OPENROUTER_API_KEY),
            model=EMBEDDINGS_MODEL,
            base_url=OPENROUTER_BASE_URL
        )

        logger.info("🗄️  Creating FAISS vector database...")
        vectordb = FAISS.from_documents(
            documents=chunks,
            embedding=embeddings
        )

        # ✅ Save FAISS index
        vectordb.save_local(FAISS_INDEX_DIR)
        logger.info(f"✅ Vector database successfully saved to {FAISS_INDEX_DIR}")

    except Exception as e:
        logger.error(f"❌ Failed to create vector database: {e}")
        raise

if __name__ == "__main__":
    ingest_documents()
