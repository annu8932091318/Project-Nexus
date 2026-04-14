import chromadb

class NexusMemory:
    def __init__(self):
        self.client = chromadb.PersistentClient(path="./workspace/memory")
        self.project_context = self.client.get_or_create_collection("project_context")
        self.skills_memory = self.client.get_or_create_collection("skills_memory")
        self.user_profile = self.client.get_or_create_collection("user_profile")

    def store_context(self, key, value, metadata=None):
        self.project_context.add(
            documents=[value],
            metadatas=[metadata] if metadata else [{}],
            ids=[key]
        )

    def store_skill(self, key, value, metadata=None):
        self.skills_memory.upsert(
            documents=[value],
            metadatas=[metadata] if metadata else [{}],
            ids=[key],
        )

    def store_user_preference(self, key, value, metadata=None):
        self.user_profile.upsert(
            documents=[value],
            metadatas=[metadata] if metadata else [{}],
            ids=[key],
        )

    def query_skills(self, query_text, n_results=3):
        return self.skills_memory.query(
            query_texts=[query_text],
            n_results=n_results
        )

    def query_project_context(self, query_text, n_results=3):
        return self.project_context.query(
            query_texts=[query_text],
            n_results=n_results,
        )
