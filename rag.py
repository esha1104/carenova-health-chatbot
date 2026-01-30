import json
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from llm import llm

CHROMA_DIR = "chroma_db"

# Embeddings
embeddings = OllamaEmbeddings(model="llama3.2:1b")

# Vector DB
vectordb = Chroma(
    persist_directory=CHROMA_DIR,
    embedding_function=embeddings
)

def rag_answer(query: str):
    # Retrieve relevant medical chunks
    docs = vectordb.similarity_search(query, k=5)
    context = "\n\n".join(doc.page_content for doc in docs)

    prompt = f"""
You are Carenova, an empathetic healthcare assistant.

STRICT RULES:
- Use ONLY the medical context below
- Do NOT confirm a diagnosis
- Possible conditions must be real illness names (e.g. Common cold, Viral infection)
- Do NOT prescribe medicines
- Follow the JSON structure exactly

Medical Context:
{context}

User Symptoms:
{query}

Return ONLY valid JSON with these keys:
- possible_conditions (list of illness names)
- explanation (list of reasons)
- home_care_tips (list of tips)
- when_to_see_doctor (list of situations)
- disclaimer (single sentence)

Do NOT use placeholder text.
Do NOT use examples.
Fill the fields with real content based on context.
"""


    raw_response = llm.invoke(prompt)

    try:
        return json.loads(raw_response)
    except json.JSONDecodeError:
        # Fallback (very rare)
        return {
            "possible_conditions": [],
            "explanation": [],
            "home_care_tips": [],
            "when_to_see_doctor": [],
            "disclaimer": "This is not a medical diagnosis."
        }
