import json
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from llm import llm


CHROMA_DIR = "chroma_db"

# MUST match ingest.py
embeddings = OllamaEmbeddings(
    model="nomic-embed-text"
)

vectordb = Chroma(
    persist_directory=CHROMA_DIR,
    embedding_function=embeddings
)

retriever = vectordb.as_retriever(
    search_type="similarity_score_threshold",
    search_kwargs={
        "score_threshold": 0.55,
        "k": 5
    }
)


def rag_answer(query: str):

    docs = retriever.invoke(query)

    print("\n========== RETRIEVED DOCS ==========\n")
    for d in docs:
        print(d.metadata)
        print(d.page_content[:300])
        print("\n------------------\n")

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

    raw_response = llm.invoke(prompt)

    # ⭐ CLEAN RESPONSE
    raw_response = raw_response.strip()

    # ⭐ AUTO FIX — small models often forget last bracket
    if not raw_response.endswith("}"):
        raw_response += "}"

    try:
        return json.loads(raw_response)

    except json.JSONDecodeError:

        print("⚠️ STILL invalid JSON:")
        print(raw_response)

        return {
            "possible_conditions": ["Medical evaluation recommended"],
            "explanation": ["The system could not confidently match symptoms."],
            "home_care_tips": ["Rest", "Stay hydrated", "Monitor symptoms"],
            "when_to_see_doctor": ["If symptoms worsen or persist."],
            "disclaimer": "This is not a medical diagnosis."
        }
