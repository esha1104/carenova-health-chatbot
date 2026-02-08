from langchain_ollama import OllamaLLM

llm = OllamaLLM(
    model="llama3.2:1b",
    temperature=0.1,     # lower = more structured
    num_ctx=2048,       # more thinking space
    num_predict=512     # ⭐ THIS FIXES YOUR JSON CUTTING
)
