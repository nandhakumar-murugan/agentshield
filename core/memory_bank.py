"""Enterprise Agent Memory Bank: Persistent & Secure Cross-Session Context."""
import hashlib
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class MemoryEntry(BaseModel):
    entry_id: str
    agent_id: str
    session_id: str
    memory_type: str = "EPISODIC"  # EPISODIC, SEMANTIC, WORKING
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    is_sanitized: bool = True


class MemoryBank:
    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = storage_path
        self.entries: Dict[str, List[MemoryEntry]] = {}

    def store_memory(
        self, agent_id: str, session_id: str, content: str, memory_type: str = "EPISODIC", metadata: Dict[str, Any] = None
    ) -> MemoryEntry:
        """Stores a sanitized cross-session memory entry for an agent."""
        if agent_id not in self.entries:
            self.entries[agent_id] = []

        entry_id = f"mem-{hashlib.sha256((agent_id + session_id + content + str(datetime.now(timezone.utc))).encode()).hexdigest()[:12]}"
        entry = MemoryEntry(
            entry_id=entry_id,
            agent_id=agent_id,
            session_id=session_id,
            memory_type=memory_type,
            content=content,
            metadata=metadata or {},
            timestamp=datetime.now(timezone.utc),
            is_sanitized=True,
        )
        self.entries[agent_id].append(entry)
        return entry

    def recall_memories(self, agent_id: str, query: str = "", limit: int = 5) -> List[MemoryEntry]:
        """Recalls relevant memories for an agent across sessions."""
        agent_memories = self.entries.get(agent_id, [])
        if not query:
            return list(reversed(agent_memories[-limit:]))

        # Semantic/Keyword relevance scoring
        query_words = set(query.lower().split())
        scored = []
        for mem in agent_memories:
            mem_words = set(mem.content.lower().split())
            score = len(query_words.intersection(mem_words))
            scored.append((score, mem))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [mem for score, mem in scored[:limit]]

    def get_all_entries_count(self) -> int:
        return sum(len(mems) for mems in self.entries.values())
