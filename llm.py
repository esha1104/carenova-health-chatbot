from langchain_ollama import OllamaLLM

llm = OllamaLLM(
    model="llama3.2:1b",
    temperature=0.2,
    num_ctx=1024,
    num_predict=200
)
