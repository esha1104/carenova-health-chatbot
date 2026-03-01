import os
import shutil
import pickle
import numpy as np
import faiss
from pathlib import Path
from pydantic import SecretStr
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
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
            # Use relative path for source metadata
            rel_path = md_file.relative_to(data_dir).as_posix()
            doc = Document(
                page_content=content,
                metadata={"source": rel_path}
            )
            documents.append(doc)
            logger.debug(f"✓ Loaded: {rel_path}")
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
        # Get embeddings for all chunks
        texts = [doc.page_content for doc in chunks]
        embeddings_list = embeddings.embed_documents(texts)
        embeddings_np = np.array(embeddings_list).astype('float32')

        # Create FAISS index
        dimension = embeddings_np.shape[1]
        index = faiss.IndexFlatL2(dimension)
        index.add(embeddings_np)

        # ✅ Save index and chunks
        os.makedirs(FAISS_INDEX_DIR, exist_ok=True)
        faiss.write_index(index, os.path.join(FAISS_INDEX_DIR, "index.faiss"))
        with open(os.path.join(FAISS_INDEX_DIR, "chunks.pkl"), "wb") as f:
            pickle.dump(chunks, f)
            
        logger.info(f"✅ Vector database successfully saved to {FAISS_INDEX_DIR}")

    except Exception as e:
        logger.error(f"❌ Failed to create vector database: {e}")
        raise

if __name__ == "__main__":
    ingest_documents()
