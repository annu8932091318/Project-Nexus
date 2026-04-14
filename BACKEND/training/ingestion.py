from pathlib import Path

from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_community.vectorstores import Chroma
from langchain_ollama import OllamaEmbeddings


DEFAULT_KNOWLEDGE_DIR = Path("data/knowledge_base")
DEFAULT_VECTOR_DIR = Path("data/vector_store")


def _load_documents(knowledge_dir: Path):
    documents = []
    for pattern in ("**/*.md", "**/*.txt"):
        loader = DirectoryLoader(
            str(knowledge_dir),
            glob=pattern,
            loader_cls=TextLoader,
            show_progress=False,
        )
        documents.extend(loader.load())
    return documents


def bootstrap_knowledge(
    knowledge_dir: Path = DEFAULT_KNOWLEDGE_DIR,
    vector_dir: Path = DEFAULT_VECTOR_DIR,
    embedding_model: str = "llama3:8b",
) -> int:
    knowledge_dir.mkdir(parents=True, exist_ok=True)
    vector_dir.mkdir(parents=True, exist_ok=True)

    docs = _load_documents(knowledge_dir)
    if not docs:
        return 0

    embeddings = OllamaEmbeddings(model=embedding_model)
    vectorstore = Chroma.from_documents(
        documents=docs,
        embedding=embeddings,
        persist_directory=str(vector_dir),
    )
    vectorstore.persist()
    return len(docs)
