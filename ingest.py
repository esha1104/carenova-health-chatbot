import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import Chroma

PDF_DIR = "medical_knowledge"
CHROMA_DIR = "chroma_db"

def ingest_documents():
    documents = []

    # Load all PDFs
    for file in os.listdir(PDF_DIR):
        if file.endswith(".pdf"):
            file_path = os.path.join(PDF_DIR, file)
            print(f"Loading {file}...")
            loader = PyPDFLoader(file_path)
            documents.extend(loader.load())

    print(f"Total pages loaded: {len(documents)}")

    # Split into chunks
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=100)

    chunks = splitter.split_documents(documents)
    print(f"Total chunks created: {len(chunks)}")

    # Create embeddings using Ollama
    embeddings = OllamaEmbeddings(model="llama3.2:1b")

    # Store in ChromaDB
    vectordb = Chroma.from_documents(
        chunks,
        embedding=embeddings,
        persist_directory=CHROMA_DIR
    )

    vectordb.persist()
    print("✅ Ingestion completed. Vector DB created.")

if __name__ == "__main__":
    ingest_documents()
