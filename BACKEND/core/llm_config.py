from crewai import LLM


def get_llm(role: str = "manager"):
    model = "ollama/llama3:8b" if role == "manager" else "ollama/deepseek-coder-v2"
    return LLM(model=model)
