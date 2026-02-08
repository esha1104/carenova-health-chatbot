import os
import shutil
from functools import partial

from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import Chroma


DATA_PATH = "medical_knowledge"
CHROMA_PATH = "chroma_db"


def ingest_documents():

    # ✅ Delete OLD DB FIRST
    if os.path.exists(CHROMA_PATH):
        print("Deleting old vector database...")
        shutil.rmtree(CHROMA_PATH, ignore_errors=True)

    print("Loading markdown files...")

    loader = DirectoryLoader(
        DATA_PATH,
        glob="**/*.md",
        loader_cls=partial(TextLoader, encoding="utf-8", autodetect_encoding=True)
    )

    documents = loader.load()
    print(f"Total documents loaded: {len(documents)}")

    # Attach metadata
    for doc in documents:
        doc.metadata["source"] = os.path.basename(doc.metadata["source"])

    # ✅ Medical-optimized chunking (very good choice btw)
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=350,
        chunk_overlap=120,
        separators=[
            "\n## ",
            "\n### ",
            "\n- ",
            "\n",
            " "
        ]
    )

    chunks = splitter.split_documents(documents)
    print(f"Total chunks created: {len(chunks)}")

    embeddings = OllamaEmbeddings(
        model="nomic-embed-text"
    )

    vectordb = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=CHROMA_PATH
    )

    # ✅ VERY IMPORTANT (prevents Windows lock)
    vectordb.persist()
    del vectordb

    print("✅ Vector database created successfully!")


if __name__ == "__main__":
    ingest_documents()
