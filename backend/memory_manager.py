"""Memory management with ChromaDB for semantic search."""
import os
import uuid
from typing import Optional

# Disable telemetry at the environment level to avoid client errors
os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")

import chromadb
from chromadb.config import Settings as ChromaSettings
import httpx


class MemoryManager:
    """Manages semantic memory using ChromaDB and Ollama embeddings."""

    def __init__(
        self,
        chroma_path: str = "./data/chroma",
        ollama_base_url: str = "http://localhost:11434",
        embedding_model: str = "nomic-embed-text"
    ):
        self.ollama_base_url = ollama_base_url
        self.embedding_model = embedding_model

        # Ensure chroma path exists
        os.makedirs(chroma_path, exist_ok=True)

        # Initialize ChromaDB
        self.client = chromadb.PersistentClient(
            path=chroma_path,
            settings=ChromaSettings(anonymized_telemetry=False)
        )

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name="assistant_memories",
            metadata={"hnsw:space": "cosine"}
        )

    async def get_embedding(self, text: str) -> Optional[list[float]]:
        """Get embedding from Ollama. Returns None if Ollama is unreachable."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.ollama_base_url}/api/embeddings",
                    json={"model": self.embedding_model, "prompt": text}
                )
                response.raise_for_status()
                return response.json()["embedding"]
        except Exception:
            return None

    async def add_memory(
        self,
        content: str,
        metadata: Optional[dict] = None,
        memory_id: Optional[str] = None
    ) -> str:
        """Add a memory with semantic embedding."""
        if memory_id is None:
            memory_id = str(uuid.uuid4())

        # Get embedding
        embedding = await self.get_embedding(content)
        if embedding is None:
            # Ollama unavailable: skip storing embedding but don't fail the request
            return memory_id

        # Store in ChromaDB
        self.collection.add(
            ids=[memory_id],
            embeddings=[embedding],
            documents=[content],
            metadatas=[metadata or {}]
        )

        return memory_id

    async def search_memories(
        self,
        query: str,
        top_k: int = 5,
        score_threshold: float = 0.7
    ) -> list[dict]:
        """Search for relevant memories.

        Uses cosine distance from HNSW (range 0–2, where 0 = identical).
        Converts to similarity via ``1 - distance/2`` which maps linearly
        to [0, 1].  A threshold of 0.7 means cosine distance < 0.6.
        """
        # Get query embedding
        query_embedding = await self.get_embedding(query)
        if query_embedding is None:
            return []

        # Search in ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )

        # Format results
        memories = []
        if results["ids"] and results["ids"][0]:
            for i, memory_id in enumerate(results["ids"][0]):
                # ChromaDB with cosine space returns distance in [0, 2]
                distance = results["distances"][0][i]
                similarity = 1 - (distance / 2)  # Linear map to [0, 1]

                if similarity >= score_threshold:
                    memories.append({
                        "id": memory_id,
                        "content": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                        "similarity": similarity
                    })

        return memories

    def delete_memory(self, memory_id: str):
        """Delete a specific memory."""
        try:
            self.collection.delete(ids=[memory_id])
        except Exception as e:
            # Memory might not exist, which is fine
            pass

    def get_memory_count(self) -> int:
        """Get total number of memories stored."""
        return self.collection.count()

    async def build_context(
        self,
        query: str,
        recent_conversations: list[dict],
        max_memories: int = 3
    ) -> str:
        """Build context string from recent conversations and relevant memories."""
        context_parts = []

        # Add relevant memories
        if query:
            memories = await self.search_memories(query, top_k=max_memories)
            if memories:
                context_parts.append("# Relevant Past Context:")
                for mem in memories:
                    context_parts.append(f"- {mem['content']}")
                context_parts.append("")

        # Add recent conversation
        if recent_conversations:
            context_parts.append("# Recent Conversation:")
            for conv in recent_conversations[-10:]:  # Last 10 messages
                role = conv.get("role", "unknown")
                content = conv.get("content", "")
                context_parts.append(f"{role}: {content}")
            context_parts.append("")

        return "\n".join(context_parts)
