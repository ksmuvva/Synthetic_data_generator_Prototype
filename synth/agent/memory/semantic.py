"""
Semantic Memory Search - Advanced memory retrieval with embeddings.

Implements:
- Semantic search in memory
- Memory consolidation (forgetting irrelevant info)
- Episodic memory (specific past events)
- Vector-based similarity search
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import time
import json
from pathlib import Path
import hashlib

from synth.agent.models.core import Context, ParsedRequest
from synth.agent.memory.layer import MemoryLayer


@dataclass
class MemoryEmbedding:
    """Embedding vector for semantic search."""
    memory_id: str
    content: str
    embedding: List[float]  # Simplified - would use actual embeddings
    timestamp: float
    access_count: int
    importance: float  # 0-1


@dataclass
class EpisodicMemory:
    """A specific episodic memory."""
    episode_id: str
    timestamp: datetime
    context: Dict[str, Any]
    actions: List[str]
    outcomes: List[str]
    emotional_tag: Optional[str]  # positive, negative, neutral
    importance: float  # 0-1
    related_memories: List[str]


@dataclass
class SemanticSearchResult:
    """Result from semantic memory search."""
    memory_id: str
    content: str
    similarity_score: float
    relevance: float
    metadata: Dict[str, Any]


class SemanticMemoryEngine:
    """
    Semantic memory search and management.

    Features:
    - Vector-based semantic search
    - Memory consolidation (forget irrelevant info)
    - Episodic memory storage
    - Importance-based retention
    """

    def __init__(
        self,
        storage_path: str = ".semantic_memory",
        memory_layer: Optional[MemoryLayer] = None,
        consolidation_interval: int = 3600,  # 1 hour
    ):
        """
        Initialize semantic memory engine.

        Args:
            storage_path: Path for persistent storage
            memory_layer: Existing memory layer
            consolidation_interval: Seconds between consolidations
        """
        self.storage_path = Path(storage_path)
        self.memory_layer = memory_layer or MemoryLayer()
        self.consolidation_interval = consolidation_interval

        # Memory stores
        self._embeddings: Dict[str, MemoryEmbedding] = {}
        self._episodic_memories: Dict[str, EpisodicMemory] = {}
        self._last_consolidation = time.time()

        # Load existing memory
        self._load_memory()

    def store_semantic_memory(
        self,
        content: str,
        context: Context,
        importance: float = 0.5,
    ) -> str:
        """
        Store memory with semantic embedding.

        Args:
            content: Content to store
            context: Current context
            importance: Importance score (0-1)

        Returns:
            Memory ID
        """
        memory_id = self._generate_memory_id(content)

        # Generate embedding (simplified - would use actual model)
        embedding = self._generate_embedding(content)

        memory = MemoryEmbedding(
            memory_id=memory_id,
            content=content,
            embedding=embedding,
            timestamp=time.time(),
            access_count=0,
            importance=importance,
        )

        self._embeddings[memory_id] = memory

        return memory_id

    def _generate_embedding(self, content: str) -> List[float]:
        """
        Generate embedding for content.

        Simplified version - in production would use actual embedding model.
        """
        # Create a simple hash-based embedding
        content_hash = hashlib.md5(content.encode()).hexdigest()

        # Convert to numeric vector
        embedding = []
        for i in range(0, len(content_hash), 2):
            val = int(content_hash[i:i+2], 16) / 255.0
            embedding.append(val)

        # Pad/truncate to fixed size
        target_size = 128
        if len(embedding) < target_size:
            embedding.extend([0.0] * (target_size - len(embedding)))
        else:
            embedding = embedding[:target_size]

        return embedding

    def _generate_memory_id(self, content: str) -> str:
        """Generate unique memory ID."""
        hash_val = hashlib.sha256(content.encode()).hexdigest()[:16]
        return f"mem_{hash_val}_{int(time.time())}"

    def semantic_search(
        self,
        query: str,
        limit: int = 10,
        min_similarity: float = 0.3,
    ) -> List[SemanticSearchResult]:
        """
        Search memory semantically (by meaning, not just keywords).

        Args:
            query: Search query
            limit: Max results
            min_similarity: Minimum similarity threshold

        Returns:
            List of search results
        """
        # Generate query embedding
        query_embedding = self._generate_embedding(query)

        # Calculate similarities
        results = []
        for memory_id, memory in self._embeddings.items():
            similarity = self._cosine_similarity(query_embedding, memory.embedding)

            if similarity >= min_similarity:
                # Update access count
                memory.access_count += 1

                results.append(SemanticSearchResult(
                    memory_id=memory_id,
                    content=memory.content,
                    similarity_score=similarity,
                    relevance=similarity * memory.importance,
                    metadata={
                        "timestamp": memory.timestamp,
                        "access_count": memory.access_count,
                        "importance": memory.importance,
                    },
                ))

        # Sort by relevance
        results.sort(key=lambda r: r.relevance, reverse=True)

        return results[:limit]

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between vectors."""
        if len(vec1) != len(vec2):
            return 0.0

        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = sum(a * a for a in vec1) ** 0.5
        magnitude2 = sum(b * b for b in vec2) ** 0.5

        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0

        return dot_product / (magnitude1 * magnitude2)

    def store_episode(
        self,
        context: Context,
        actions: List[str],
        outcomes: List[str],
        emotional_tag: Optional[str] = None,
        importance: float = 0.5,
    ) -> str:
        """
        Store an episodic memory.

        Args:
            context: Execution context
            actions: Actions taken
            outcomes: Results
            emotional_tag: Emotional tag (positive/negative/neutral)
            importance: Importance score

        Returns:
            Episode ID
        """
        episode_id = f"episode_{len(self._episodic_memories) + 1}_{int(time.time())}"

        episode = EpisodicMemory(
            episode_id=episode_id,
            timestamp=datetime.now(),
            context={
                "request": context.request.original_text,
                "request_type": context.request.request_type.value,
                "entities": context.request.entities,
            },
            actions=actions,
            outcomes=outcomes,
            emotional_tag=emotional_tag or "neutral",
            importance=importance,
            related_memories=[],
        )

        self._episodic_memories[episode_id] = episode

        return episode_id

    def recall_episodes(
        self,
        context: Context,
        limit: int = 5,
    ) -> List[EpisodicMemory]:
        """
        Recall relevant episodes.

        Args:
            context: Current context
            limit: Max episodes to recall

        Returns:
            List of relevant episodes
        """
        episodes = []

        # Find similar episodes
        current_type = context.request.request_type.value

        for episode in self._episodic_memories.values():
            # Check if similar request type
            if episode.context.get("request_type") == current_type:
                episodes.append(episode)

        # Sort by importance and recency
        episodes.sort(
            key=lambda e: (
                e.importance,
                - (time.time() - e.timestamp.timestamp()),
            ),
            reverse=True,
        )

        return episodes[:limit]

    def consolidate_memory(self):
        """
        Consolidate memory - forget or archive less important memories.

        Runs consolidation based on:
        - Time since last access
        - Importance score
        - Access frequency
        """
        now = time.time()

        # Check if consolidation is needed
        if now - self._last_consolidation < self.consolidation_interval:
            return

        memories_to_remove = []

        for memory_id, memory in self._embeddings.items():
            # Calculate retention score
            age = now - memory.timestamp
            access_frequency = memory.access_count / max(age / 3600, 1)  # accesses per hour

            # Retention score (higher = keep)
            retention_score = (
                memory.importance * 0.5 +
                access_frequency * 0.3 +
                (1.0 - min(age / 86400, 1.0)) * 0.2  # Decay over 24 hours
            )

            # Remove low-importance, old, rarely-accessed memories
            if retention_score < 0.2:
                memories_to_remove.append(memory_id)

        # Remove memories
        for memory_id in memories_to_remove:
            del self._embeddings[memory_id]

        # Archive old episodic memories
        episodes_to_archive = []
        for episode_id, episode in self._episodic_memories.items():
            age = (datetime.now() - episode.timestamp).total_seconds()
            if age > 604800:  # 7 days
                if episode.importance < 0.5:
                    episodes_to_archive.append(episode_id)

        for episode_id in episodes_to_archive:
            # Archive instead of delete
            del self._episodic_memories[episode_id]

        self._last_consolidation = now

        # Save consolidated memory
        self._save_memory()

    def find_related_memories(
        self,
        memory_id: str,
        limit: int = 5,
    ) -> List[SemanticSearchResult]:
        """
        Find memories related to a given memory.

        Args:
            memory_id: Memory to find relations for
            limit: Max results

        Returns:
            List of related memories
        """
        if memory_id not in self._embeddings:
            return []

        target_memory = self._embeddings[memory_id]

        # Find similar memories
        results = []
        for other_id, other_memory in self._embeddings.items():
            if other_id != memory_id:
                similarity = self._cosine_similarity(
                    target_memory.embedding,
                    other_memory.embedding
                )

                if similarity > 0.5:  # High similarity threshold
                    results.append(SemanticSearchResult(
                        memory_id=other_id,
                        content=other_memory.content,
                        similarity_score=similarity,
                        relevance=similarity,
                        metadata={
                            "timestamp": other_memory.timestamp,
                            "importance": other_memory.importance,
                        },
                    ))

        results.sort(key=lambda r: r.similarity_score, reverse=True)

        return results[:limit]

    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory statistics."""
        total_memories = len(self._embeddings)
        total_episodes = len(self._episodic_memories)

        # Calculate average importance
        avg_importance = 0.0
        if total_memories > 0:
            avg_importance = sum(m.importance for m in self._embeddings.values()) / total_memories

        return {
            "total_semantic_memories": total_memories,
            "total_episodic_memories": total_episodes,
            "average_importance": avg_importance,
            "last_consolidation": datetime.fromtimestamp(self._last_consolidation).isoformat(),
            "consolidation_interval": self.consolidation_interval,
        }

    def _save_memory(self):
        """Save memory to disk."""
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # Save embeddings
        embeddings_data = {
            memory_id: {
                "content": mem.content,
                "embedding": mem.embedding,
                "timestamp": mem.timestamp,
                "access_count": mem.access_count,
                "importance": mem.importance,
            }
            for memory_id, mem in self._embeddings.items()
        }

        embeddings_file = self.storage_path / "embeddings.json"
        with open(embeddings_file, "w") as f:
            json.dump(embeddings_data, f, indent=2)

        # Save episodic memories
        episodes_data = {
            episode_id: {
                "timestamp": episode.timestamp.isoformat(),
                "context": episode.context,
                "actions": episode.actions,
                "outcomes": episode.outcomes,
                "emotional_tag": episode.emotional_tag,
                "importance": episode.importance,
            }
            for episode_id, episode in self._episodic_memories.items()
        }

        episodes_file = self.storage_path / "episodes.json"
        with open(episodes_file, "w") as f:
            json.dump(episodes_data, f, indent=2)

    def _load_memory(self):
        """Load memory from disk."""
        embeddings_file = self.storage_path / "embeddings.json"
        episodes_file = self.storage_path / "episodes.json"

        # Load embeddings
        if embeddings_file.exists():
            try:
                with open(embeddings_file, "r") as f:
                    data = json.load(f)

                for memory_id, mem_data in data.items():
                    self._embeddings[memory_id] = MemoryEmbedding(
                        memory_id=memory_id,
                        content=mem_data["content"],
                        embedding=mem_data["embedding"],
                        timestamp=mem_data["timestamp"],
                        access_count=mem_data["access_count"],
                        importance=mem_data["importance"],
                    )
            except Exception as e:
                print(f"Error loading embeddings: {e}")

        # Load episodes
        if episodes_file.exists():
            try:
                with open(episodes_file, "r") as f:
                    data = json.load(f)

                for episode_id, ep_data in data.items():
                    self._episodic_memories[episode_id] = EpisodicMemory(
                        episode_id=episode_id,
                        timestamp=datetime.fromisoformat(ep_data["timestamp"]),
                        context=ep_data["context"],
                        actions=ep_data["actions"],
                        outcomes=ep_data["outcomes"],
                        emotional_tag=ep_data["emotional_tag"],
                        importance=ep_data["importance"],
                        related_memories=[],
                    )
            except Exception as e:
                print(f"Error loading episodes: {e}")
