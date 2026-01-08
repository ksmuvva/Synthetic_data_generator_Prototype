"""
Vector-based similarity search for memory.

Uses sentence embeddings to find semantically similar past interactions.
"""

import json
import threading
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, field


@dataclass
class EmbeddedInteraction:
    """Interaction with embedded vector."""
    request: str
    response: Dict[str, Any]
    metadata: Dict[str, Any]
    timestamp: str
    embedding: Optional[List[float]] = None
    request_type: Optional[str] = None
    entities: Dict[str, Any] = field(default_factory=dict)


class VectorStore:
    """
    Vector-based similarity search for memory.

    Uses sentence embeddings to find semantically similar past interactions.
    Falls back to keyword matching if embeddings unavailable.
    """

    def __init__(
        self,
        storage_path: str = ".agent_memory",
        embedding_model: Optional[str] = None,
        use_llm_embeddings: bool = False,
        llm_provider: Optional[Any] = None,
    ):
        """
        Initialize vector store.

        Args:
            storage_path: Directory for storing vector data
            embedding_model: Sentence transformer model name
            use_llm_embeddings: Whether to use LLM for embeddings
            llm_provider: LLM provider for embeddings (if use_llm_embeddings=True)
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()

        # Embedding backend
        self.embedding_model = None
        self.use_llm_embeddings = use_llm_embeddings
        self.llm_provider = llm_provider
        self.embedding_dim = 384  # Default for small models

        # Initialize embedding backend
        self._init_embeddings(embedding_model)

        # Storage
        self._vectors_file = self.storage_path / "vectors.json"
        self._interactions: List[EmbeddedInteraction] = []
        self._load_vectors()

    def _init_embeddings(self, model_name: Optional[str]) -> None:
        """Initialize embedding backend."""
        # Try sentence-transformers first (best for semantic search)
        if not self.use_llm_embeddings:
            try:
                from sentence_transformers import SentenceTransformer
                model_name = model_name or "all-MiniLM-L6-v2"
                self.embedding_model = SentenceTransformer(model_name)
                self.embedding_dim = self.embedding_model.get_sentence_embedding_dimension()
                return
            except ImportError:
                pass

        # Fall back to LLM embeddings if available
        if self.use_llm_embeddings and self.llm_provider:
            self.embedding_dim = 1536  # OpenAI embedding dimension
            return

        # No embeddings available, will use keyword matching
        self.embedding_model = None

    def _get_embedding(self, text: str) -> Optional[List[float]]:
        """Get embedding for text."""
        if self.embedding_model is not None and not self.use_llm_embeddings:
            # Use sentence-transformers
            import numpy as np
            embedding = self.embedding_model.encode(text, convert_to_numpy=True)
            return embedding.tolist()

        elif self.use_llm_embeddings and self.llm_provider:
            # Use LLM for embeddings (simplified approach)
            # In production, use dedicated embedding API
            try:
                # Generate a simple hash-based embedding as fallback
                import hashlib
                import numpy as np

                # Create a deterministic embedding from text hash
                hash_obj = hashlib.sha256(text.encode())
                hash_bytes = hash_obj.digest()

                # Expand to desired dimension
                embedding = np.zeros(self.embedding_dim, dtype=np.float32)
                for i, byte in enumerate(hash_bytes):
                    if i < self.embedding_dim:
                        embedding[i] = byte / 255.0

                return embedding.tolist()
            except Exception:
                return None

        return None

    def add_interaction(
        self,
        request: str,
        response: Dict[str, Any],
        metadata: Dict[str, Any],
        request_type: Optional[str] = None,
        entities: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Add interaction to vector store.

        Args:
            request: User request
            response: Agent response
            metadata: Interaction metadata
            request_type: Type of request
            entities: Extracted entities
        """
        with self._lock:
            # Get embedding
            embedding = self._get_embedding(request)

            interaction = EmbeddedInteraction(
                request=request,
                response=response,
                metadata=metadata,
                timestamp=datetime.now().isoformat(),
                embedding=embedding,
                request_type=request_type,
                entities=entities or {},
            )

            self._interactions.append(interaction)

            # Keep only last 1000 interactions
            if len(self._interactions) > 1000:
                self._interactions = self._interactions[-1000:]

            self._save_vectors()

    def find_similar(
        self,
        query: str,
        max_results: int = 5,
        min_similarity: float = 0.1,
        request_type_filter: Optional[str] = None,
    ) -> List[Tuple[float, Dict[str, Any]]]:
        """
        Find similar interactions.

        Args:
            query: Query text
            max_results: Maximum number of results
            min_similarity: Minimum similarity threshold
            request_type_filter: Optional filter by request type

        Returns:
            List of (similarity, interaction) tuples
        """
        with self._lock:
            if not self._interactions:
                return []

            # Get query embedding
            query_embedding = self._get_embedding(query)

            if query_embedding is None:
                # Fall back to keyword matching
                return self._keyword_search(query, max_results, min_similarity, request_type_filter)

            # Vector similarity search
            similarities = []

            for interaction in self._interactions:
                # Filter by request type if specified
                if request_type_filter and interaction.request_type != request_type_filter:
                    continue

                if interaction.embedding is None:
                    continue

                # Calculate cosine similarity
                similarity = self._cosine_similarity(query_embedding, interaction.embedding)

                if similarity >= min_similarity:
                    similarities.append((similarity, interaction))

            # Sort by similarity and return top N
            similarities.sort(key=lambda x: x[0], reverse=True)
            return similarities[:max_results]

    def _keyword_search(
        self,
        query: str,
        max_results: int,
        min_similarity: float,
        request_type_filter: Optional[str] = None,
    ) -> List[Tuple[float, Dict[str, Any]]]:
        """Fallback keyword-based search."""
        query_words = set(query.lower().split())
        similarities = []

        for interaction in self._interactions:
            # Filter by request type if specified
            if request_type_filter and interaction.request_type != request_type_filter:
                continue

            past_request = interaction.request
            past_words = set(past_request.lower().split())

            # Jaccard similarity
            intersection = query_words & past_words
            union = query_words | past_words
            similarity = len(intersection) / len(union) if union else 0.0

            if similarity >= min_similarity:
                similarities.append((similarity, interaction))

        # Sort by similarity and return top N
        similarities.sort(key=lambda x: x[0], reverse=True)
        return similarities[:max_results]

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        import math

        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(b * b for b in vec2))

        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0

        return dot_product / (magnitude1 * magnitude2)

    def _load_vectors(self) -> None:
        """Load vectors from storage."""
        if self._vectors_file.exists():
            try:
                with open(self._vectors_file, "r") as f:
                    data = json.load(f)

                self._interactions = [
                    EmbeddedInteraction(
                        request=item["request"],
                        response=item["response"],
                        metadata=item["metadata"],
                        timestamp=item["timestamp"],
                        embedding=item.get("embedding"),
                        request_type=item.get("request_type"),
                        entities=item.get("entities", {}),
                    )
                    for item in data
                ]
            except Exception:
                self._interactions = []

    def _save_vectors(self) -> None:
        """Save vectors to storage."""
        data = [
            {
                "request": i.request,
                "response": i.response,
                "metadata": i.metadata,
                "timestamp": i.timestamp,
                "embedding": i.embedding,
                "request_type": i.request_type,
                "entities": i.entities,
            }
            for i in self._interactions
        ]

        with open(self._vectors_file, "w") as f:
            json.dump(data, f, indent=2, default=str)

    def get_stats(self) -> Dict[str, Any]:
        """Get vector store statistics."""
        with self._lock:
            embedded_count = sum(1 for i in self._interactions if i.embedding is not None)

            return {
                "total_interactions": len(self._interactions),
                "embedded_interactions": embedded_count,
                "embedding_available": self.embedding_model is not None or self.use_llm_embeddings,
                "embedding_type": "llm" if self.use_llm_embeddings else ("sentence_transformer" if self.embedding_model else "none"),
            }
