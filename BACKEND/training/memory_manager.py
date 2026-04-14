from datetime import datetime
from typing import Optional

from core.memory import NexusMemory


class TrainingMemoryManager:
    def __init__(self):
        self.memory = NexusMemory()

    def save_knowledge_card(
        self,
        key: str,
        value: str,
        project_type: str = "general",
        user_approval_rating: Optional[int] = None,
    ) -> None:
        metadata = {
            "saved_at": datetime.utcnow().isoformat(),
            "project_type": project_type,
            "user_approval_rating": user_approval_rating,
        }
        self.memory.store_skill(key=key, value=value, metadata=metadata)

    def retrieve_similar_solutions(self, query_text: str, n_results: int = 3):
        return self.memory.query_skills(query_text=query_text, n_results=n_results)
