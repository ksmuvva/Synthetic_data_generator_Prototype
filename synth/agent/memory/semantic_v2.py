"""
Enhanced Semantic Memory - Advanced semantic context storage and retrieval.

Implements intelligent semantic memory with:
- Context-aware semantic embeddings
- LLM-powered semantic understanding
- Multi-dimensional similarity search
- Automatic memory consolidation
- Context pattern learning
"""

from typing import Dict, Any, List, Optional, Tuple, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import time
import json
from pathlib import Path
import hashlib
import re
from collections import defaultdict

from synth.agent.models.core import Context, ParsedRequest, RequestType


@dataclass
class SemanticContext:
    """Rich semantic context for memory storage."""
    context_id: str
    timestamp: datetime
    request_type: str
    intent: str
    entities: Dict[str, Any]
    semantic_tags: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    domain: str = "general"
    sentiment: str = "neutral"  # positive, negative, neutral
    importance: float = 0.5
    outcome: Optional[str] = None
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SemanticSearchQuery:
    """Semantic search query."""
    query_text: str
    context_filters: Dict[str, Any] = field(default_factory=dict)
    min_similarity: float = 0.3
    min_importance: float = 0.0
    time_window: Optional[timedelta] = None
    max_results: int = 10
    include_metadata: bool = True


@dataclass
class SemanticSearchResult:
    """Result from semantic memory search."""
    context: SemanticContext
    similarity_score: float
    relevance_score: float
    match_reasons: List[str] = field(default_factory=list)
    related_contexts: List[str] = field(default_factory=list)


class SemanticMemory:
    """
    Enhanced semantic memory system.

    Stores and retrieves semantic context with intelligent
    similarity search and pattern recognition.
    """

    def __init__(
        self,
        storage_path: str = ".semantic_memory_v2",
        llm_provider: Optional[Any] = None,
        consolidation_interval_hours: int = 24,
        max_memories: int = 10000,
    ):
        """
        Initialize semantic memory.

        Args:
            storage_path: Path for persistent storage
            llm_provider: Optional LLM for semantic understanding
            consolidation_interval_hours: Hours between memory consolidation
            max_memories: Maximum memories to store
        """
        self.storage_path = Path(storage_path)
        self.llm_provider = llm_provider

        # Memory storage
        self._contexts: Dict[str, SemanticContext] = {}
        self._contexts_by_type: Dict[str, List[str]] = defaultdict(list)
        self._contexts_by_domain: Dict[str, List[str]] = defaultdict(list)
        self._contexts_by_intent: Dict[str, List[str]] = defaultdict(list)

        # Pattern learning
        self._pattern_counts: Dict[str, int] = defaultdict(int)
        self._co_occurrence: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))

        # Configuration
        self.consolidation_interval = consolidation_interval_hours * 3600
        self.max_memories = max_memories
        self._last_consolidation = time.time()

        # Create storage directory
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # Load existing memory
        self._load_memory()

    def store_context(
        self,
        context: Context,
        outcome: Optional[str] = None,
        importance: Optional[float] = None,
    ) -> str:
        """
        Store semantic context with rich metadata.

        Args:
            context: Context to store
            outcome: Optional outcome/result
            importance: Optional importance score (0-1)

        Returns:
            Context ID
        """
        # Extract semantic features
        semantic_tags = self._extract_semantic_tags(context)
        keywords = self._extract_keywords(context)
        domain = self._infer_domain(context)
        sentiment = self._infer_sentiment(context)

        # Calculate importance if not provided
        if importance is None:
            importance = self._calculate_importance(context, outcome)

        # Generate semantic embedding
        embedding = self._generate_embedding(context)

        # Create semantic context
        semantic_ctx = SemanticContext(
            context_id=self._generate_context_id(context),
            timestamp=datetime.now(),
            request_type=context.request.request_type.value,
            intent=context.request.intent,
            entities=context.request.entities.copy(),
            semantic_tags=semantic_tags,
            keywords=keywords,
            domain=domain,
            sentiment=sentiment,
            importance=importance,
            outcome=outcome,
            embedding=embedding,
            metadata={
                "complexity": context.request.complexity,
                "confidence": context.request.confidence,
                "conversation_depth": len(context.conversation_history),
                "has_environment": context.environment is not None,
            },
        )

        # Store in memory
        self._contexts[semantic_ctx.context_id] = semantic_ctx

        # Update indices
        self._contexts_by_type[semantic_ctx.request_type].append(semantic_ctx.context_id)
        self._contexts_by_domain[semantic_ctx.domain].append(semantic_ctx.context_id)
        self._contexts_by_intent[semantic_ctx.intent].append(semantic_ctx.context_id)

        # Update patterns
        self._update_patterns(semantic_ctx)

        # Consolidate if needed
        if len(self._contexts) > self.max_memories:
            self._consolidate_memory()

        return semantic_ctx.context_id

    def _extract_semantic_tags(self, context: Context) -> List[str]:
        """Extract semantic tags from context."""
        tags = []

        request_text = context.request.original_text.lower()

        # Domain tags
        domain_keywords = {
            "data_generation": ["generate", "create", "synthesize", "produce"],
            "data_analysis": ["analyze", "examine", "study", "investigate"],
            "data_validation": ["validate", "verify", "check", "confirm"],
            "data_export": ["export", "save", "output", "write"],
            "privacy": ["privacy", "anonymous", "gdpr", "hipaa"],
            "performance": ["fast", "quick", "optimize", "efficient"],
            "quality": ["quality", "accurate", "realistic", "precise"],
        }

        for tag, keywords in domain_keywords.items():
            if any(keyword in request_text for keyword in keywords):
                tags.append(tag)

        # Entity type tags
        entity_type = context.request.entities.get("entity_type", "")
        if entity_type:
            tags.append(f"entity_{entity_type}")

        # Size tags
        count = context.request.entities.get("count", 0)
        if count > 10000:
            tags.append("large_scale")
        elif count > 1000:
            tags.append("medium_scale")
        elif count > 0:
            tags.append("small_scale")

        return tags

    def _extract_keywords(self, context: Context) -> List[str]:
        """Extract important keywords from context."""
        keywords = []

        # From request text
        request_text = context.request.original_text.lower()

        # Extract nouns and important terms (simplified)
        important_words = [
            "customer", "transaction", "product", "order", "employee",
            "patient", "student", "record", "data", "dataset",
            "generate", "create", "validate", "export", "analyze",
            "quality", "privacy", "performance", "accuracy",
        ]

        for word in important_words:
            if word in request_text:
                keywords.append(word)

        # From entities
        for key, value in context.request.entities.items():
            if isinstance(value, str) and value:
                keywords.append(value)
            elif isinstance(value, list):
                keywords.extend(str(v) for v in value[:3])

        return list(set(keywords))

    def _infer_domain(self, context: Context) -> str:
        """Infer domain from context."""
        request_type = context.request.request_type
        entity_type = context.request.entities.get("entity_type", "")

        # Domain mapping
        if entity_type in ["customer", "transaction", "order"]:
            return "commerce"
        elif entity_type in ["patient", "medical"]:
            return "healthcare"
        elif entity_type in ["employee", "staff"]:
            return "hr"
        elif entity_type in ["student", "course"]:
            return "education"
        else:
            return "general"

    def _infer_sentiment(self, context: Context) -> str:
        """Infer sentiment from context."""
        request_text = context.request.original_text.lower()

        # Positive sentiment indicators
        positive_words = ["good", "great", "excellent", "perfect", "best", "ideal"]
        # Negative sentiment indicators
        negative_words = ["bad", "wrong", "error", "fail", "problem", "issue"]

        positive_count = sum(1 for word in positive_words if word in request_text)
        negative_count = sum(1 for word in negative_words if word in request_text)

        if positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count:
            return "negative"
        else:
            return "neutral"

    def _calculate_importance(self, context: Context, outcome: Optional[str]) -> float:
        """Calculate importance score for context."""
        importance = 0.5  # Base importance

        # Complexity increases importance
        importance += context.request.complexity * 0.2

        # High confidence increases importance
        importance += context.request.confidence * 0.1

        # Large scale operations increase importance
        count = context.request.entities.get("count", 0)
        if count > 10000:
            importance += 0.2
        elif count > 1000:
            importance += 0.1

        # Special domains increase importance
        if context.request.entities.get("entity_type") in ["transaction", "patient"]:
            importance += 0.1

        # Successful outcomes increase importance
        if outcome and "success" in outcome.lower():
            importance += 0.1

        return min(1.0, importance)

    def _generate_embedding(self, context: Context) -> List[float]:
        """
        Generate semantic embedding for context.

        Uses LLM if available, otherwise falls back to hash-based embedding.
        """
        if self.llm_provider:
            try:
                # Try to use LLM for embedding
                embedding = self._llm_embedding(context)
                if embedding:
                    return embedding
            except Exception:
                pass

        # Fallback to feature-based embedding
        return self._feature_embedding(context)

    def _llm_embedding(self, context: Context) -> Optional[List[float]]:
        """Generate embedding using LLM."""
        # This would call the LLM provider's embedding API
        # For now, return None to use fallback
        return None

    def _feature_embedding(self, context: Context) -> List[float]:
        """Generate feature-based embedding."""
        features = []

        # Request type encoding (one-hot)
        request_types = [
            "data_generation", "data_analysis", "data_validation",
            "data_export", "clarification", "multi_objective", "unknown"
        ]
        for rt in request_types:
            features.append(1.0 if context.request.request_type.value == rt else 0.0)

        # Intent encoding (hash-based)
        intent_hash = hashlib.md5(context.request.intent.encode()).hexdigest()
        intent_features = [int(intent_hash[i:i+2], 16) / 255.0 for i in range(0, min(16, len(intent_hash)), 2)]
        features.extend(intent_features)

        # Entity features
        entity_type = context.request.entities.get("entity_type", "")
        entity_hash = hashlib.md5(entity_type.encode()).hexdigest()[:8]
        entity_features = [int(entity_hash[i:i+2], 16) / 255.0 for i in range(0, 8, 2)]
        features.extend(entity_features)

        # Count feature (normalized)
        count = context.request.entities.get("count", 0)
        features.append(min(count / 10000.0, 1.0))

        # Complexity and confidence
        features.append(context.request.complexity)
        features.append(context.request.confidence)

        # Conversation depth
        features.append(min(len(context.conversation_history) / 50.0, 1.0))

        # Pad to fixed size
        target_size = 128
        while len(features) < target_size:
            features.append(0.0)

        return features[:target_size]

    def _generate_context_id(self, context: Context) -> str:
        """Generate unique context ID."""
        hash_val = hashlib.sha256(
            f"{context.request.original_text}{time.time()}".encode()
        ).hexdigest()[:16]
        return f"ctx_{hash_val}_{int(time.time())}"

    def _update_patterns(self, semantic_ctx: SemanticContext):
        """Update pattern learning from new context."""
        # Update tag counts
        for tag in semantic_ctx.semantic_tags:
            self._pattern_counts[f"tag_{tag}"] += 1

        # Update co-occurrence
        for i, tag1 in enumerate(semantic_ctx.semantic_tags):
            for tag2 in semantic_ctx.semantic_tags[i+1:]:
                self._co_occurrence[tag1][tag2] += 1
                self._co_occurrence[tag2][tag1] += 1

    def semantic_search(
        self,
        query: SemanticSearchQuery,
    ) -> List[SemanticSearchResult]:
        """
        Perform semantic search for relevant contexts.

        Args:
            query: Search query with filters and constraints

        Returns:
            List of search results ranked by relevance
        """
        # Generate query embedding
        query_embedding = self._generate_query_embedding(query.query_text)

        # Calculate similarities and filter
        results = []
        for ctx_id, context in self._contexts.items():
            # Apply filters
            if not self._matches_filters(context, query.context_filters):
                continue

            # Check time window
            if query.time_window:
                time_diff = datetime.now() - context.timestamp
                if time_diff > query.time_window:
                    continue

            # Check importance threshold
            if context.importance < query.min_importance:
                continue

            # Calculate similarity
            similarity = self._cosine_similarity(query_embedding, context.embedding or [])

            if similarity >= query.min_similarity:
                # Calculate relevance score
                relevance = self._calculate_relevance(context, similarity, query)

                # Determine match reasons
                match_reasons = self._determine_match_reasons(context, query)

                # Find related contexts
                related = self._find_related_contexts(ctx_id)

                results.append(SemanticSearchResult(
                    context=context,
                    similarity_score=similarity,
                    relevance_score=relevance,
                    match_reasons=match_reasons,
                    related_contexts=related,
                ))

        # Sort by relevance
        results.sort(key=lambda r: r.relevance_score, reverse=True)

        return results[:query.max_results]

    def _generate_query_embedding(self, query_text: str) -> List[float]:
        """Generate embedding for search query."""
        # Use hash-based embedding for query
        query_hash = hashlib.md5(query_text.encode()).hexdigest()

        embedding = []
        for i in range(0, len(query_hash), 2):
            val = int(query_hash[i:i+2], 16) / 255.0
            embedding.append(val)

        # Pad to match context embedding size
        while len(embedding) < 128:
            embedding.append(0.0)

        return embedding[:128]

    def _matches_filters(self, context: SemanticContext, filters: Dict[str, Any]) -> bool:
        """Check if context matches filters."""
        if not filters:
            return True

        # Request type filter
        if "request_type" in filters:
            if context.request_type != filters["request_type"]:
                return False

        # Domain filter
        if "domain" in filters:
            if context.domain != filters["domain"]:
                return False

        # Tag filter
        if "has_tag" in filters:
            if filters["has_tag"] not in context.semantic_tags:
                return False

        # Keyword filter
        if "has_keyword" in filters:
            if filters["has_keyword"] not in context.keywords:
                return False

        return True

    def _calculate_relevance(
        self,
        context: SemanticContext,
        similarity: float,
        query: SemanticSearchQuery,
    ) -> float:
        """Calculate overall relevance score."""
        # Base similarity
        relevance = similarity * 0.6

        # Importance boost
        relevance += context.importance * 0.2

        # Recency boost (more recent = higher relevance)
        age_hours = (datetime.now() - context.timestamp).total_seconds() / 3600
        recency = max(0, 1.0 - age_hours / 168)  # Decay over 1 week
        relevance += recency * 0.2

        return min(1.0, relevance)

    def _determine_match_reasons(
        self,
        context: SemanticContext,
        query: SemanticSearchQuery,
    ) -> List[str]:
        """Determine reasons for match."""
        reasons = []

        query_text = query.query_text.lower()

        # Check keyword matches
        for keyword in context.keywords:
            if keyword.lower() in query_text:
                reasons.append(f"keyword_match:{keyword}")

        # Check tag matches
        for tag in context.semantic_tags:
            if tag.lower() in query_text:
                reasons.append(f"tag_match:{tag}")

        # Check intent similarity
        if context.intent.lower() in query_text:
            reasons.append("intent_match")

        # Check domain match
        if context.domain in query_text:
            reasons.append(f"domain_match:{context.domain}")

        return reasons if reasons else ["semantic_similarity"]

    def _find_related_contexts(
        self,
        context_id: str,
        limit: int = 3,
    ) -> List[str]:
        """Find contexts related to given context."""
        if context_id not in self._contexts:
            return []

        target_context = self._contexts[context_id]
        related = []

        for other_id, other_context in self._contexts.items():
            if other_id == context_id:
                continue

            # Calculate similarity
            similarity = 0.0
            if target_context.embedding and other_context.embedding:
                similarity = self._cosine_similarity(
                    target_context.embedding,
                    other_context.embedding
                )

            # Check tag overlap
            tag_overlap = len(
                set(target_context.semantic_tags) & set(other_context.semantic_tags)
            )

            # Check domain match
            domain_match = 1.0 if target_context.domain == other_context.domain else 0.0

            # Combined score
            score = similarity * 0.6 + (tag_overlap / max(len(target_context.semantic_tags), 1)) * 0.3 + domain_match * 0.1

            if score > 0.4:
                related.append((other_id, score))

        # Sort by score and return IDs
        related.sort(key=lambda x: x[1], reverse=True)
        return [ctx_id for ctx_id, _ in related[:limit]]

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between vectors."""
        if len(vec1) != len(vec2) or len(vec1) == 0:
            return 0.0

        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = sum(a * a for a in vec1) ** 0.5
        magnitude2 = sum(b * b for b in vec2) ** 0.5

        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0

        return dot_product / (magnitude1 * magnitude2)

    def find_similar_contexts(
        self,
        context: Context,
        limit: int = 5,
    ) -> List[SemanticContext]:
        """
        Find contexts similar to given context.

        Args:
            context: Context to find similarities for
            limit: Max results

        Returns:
            List of similar contexts
        """
        # Create search query
        query = SemanticSearchQuery(
            query_text=context.request.original_text,
            max_results=limit,
            min_similarity=0.4,
        )

        # Add type filter
        query.context_filters["request_type"] = context.request.request_type.value

        # Search
        results = self.semantic_search(query)

        return [r.context for r in results]

    def get_context_patterns(self) -> Dict[str, Any]:
        """Get learned context patterns."""
        # Top patterns
        top_patterns = sorted(
            self._pattern_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]

        # Top co-occurrences
        top_cooccurrences = []
        for tag1, co_occs in self._co_occurrence.items():
            for tag2, count in co_occs.items():
                if tag1 < tag2:  # Avoid duplicates
                    top_cooccurrences.append(((tag1, tag2), count))

        top_cooccurrences.sort(key=lambda x: x[1], reverse=True)
        top_cooccurrences = top_cooccurrences[:10]

        return {
            "top_patterns": top_patterns,
            "top_cooccurrences": [(pair, count) for pair, count in top_cooccurrences],
            "total_contexts": len(self._contexts),
            "contexts_by_type": {
                rt: len(ids) for rt, ids in self._contexts_by_type.items()
            },
            "contexts_by_domain": {
                domain: len(ids) for domain, ids in self._contexts_by_domain.items()
            },
        }

    def _consolidate_memory(self):
        """Consolidate memory by removing low-importance, old contexts."""
        now = time.time()

        # Check if consolidation is needed
        if now - self._last_consolidation < self.consolidation_interval:
            return

        contexts_to_remove = []

        for ctx_id, context in self._contexts.items():
            # Calculate retention score
            age_hours = (datetime.now() - context.timestamp).total_seconds() / 3600
            age_score = max(0, 1.0 - age_hours / 168)  # Decay over 1 week

            retention_score = (
                context.importance * 0.6 +
                age_score * 0.4
            )

            # Remove low-scoring contexts
            if retention_score < 0.2:
                contexts_to_remove.append(ctx_id)

        # Remove contexts
        for ctx_id in contexts_to_remove:
            self._remove_context(ctx_id)

        self._last_consolidation = now

        # Save consolidated memory
        self._save_memory()

    def _remove_context(self, ctx_id: str):
        """Remove context from all indices."""
        if ctx_id not in self._contexts:
            return

        context = self._contexts[ctx_id]

        # Remove from type index
        if ctx_id in self._contexts_by_type[context.request_type]:
            self._contexts_by_type[context.request_type].remove(ctx_id)

        # Remove from domain index
        if ctx_id in self._contexts_by_domain[context.domain]:
            self._contexts_by_domain[context.domain].remove(ctx_id)

        # Remove from intent index
        if ctx_id in self._contexts_by_intent[context.intent]:
            self._contexts_by_intent[context.intent].remove(ctx_id)

        # Remove from main storage
        del self._contexts[ctx_id]

    def get_statistics(self) -> Dict[str, Any]:
        """Get memory statistics."""
        total_contexts = len(self._contexts)

        avg_importance = 0.0
        if total_contexts > 0:
            avg_importance = sum(ctx.importance for ctx in self._contexts.values()) / total_contexts

        return {
            "total_contexts": total_contexts,
            "average_importance": avg_importance,
            "unique_request_types": len(self._contexts_by_type),
            "unique_domains": len(self._contexts_by_domain),
            "pattern_count": len(self._pattern_counts),
            "last_consolidation": datetime.fromtimestamp(self._last_consolidation).isoformat(),
        }

    def _save_memory(self):
        """Save memory to disk."""
        # Save contexts
        contexts_data = {}
        for ctx_id, context in self._contexts.items():
            contexts_data[ctx_id] = {
                "context_id": context.context_id,
                "timestamp": context.timestamp.isoformat(),
                "request_type": context.request_type,
                "intent": context.intent,
                "entities": context.entities,
                "semantic_tags": context.semantic_tags,
                "keywords": context.keywords,
                "domain": context.domain,
                "sentiment": context.sentiment,
                "importance": context.importance,
                "outcome": context.outcome,
                "embedding": context.embedding,
                "metadata": context.metadata,
            }

        contexts_file = self.storage_path / "contexts.json"
        with open(contexts_file, "w") as f:
            json.dump(contexts_data, f, indent=2)

        # Save patterns
        patterns_data = {
            "pattern_counts": dict(self._pattern_counts),
            "co_occurrence": {
                k1: dict(v) for k1, v in self._co_occurrence.items()
            },
        }

        patterns_file = self.storage_path / "patterns.json"
        with open(patterns_file, "w") as f:
            json.dump(patterns_data, f, indent=2)

    def _load_memory(self):
        """Load memory from disk."""
        contexts_file = self.storage_path / "contexts.json"
        patterns_file = self.storage_path / "patterns.json"

        # Load contexts
        if contexts_file.exists():
            try:
                with open(contexts_file, "r") as f:
                    data = json.load(f)

                for ctx_id, ctx_data in data.items():
                    context = SemanticContext(
                        context_id=ctx_data["context_id"],
                        timestamp=datetime.fromisoformat(ctx_data["timestamp"]),
                        request_type=ctx_data["request_type"],
                        intent=ctx_data["intent"],
                        entities=ctx_data["entities"],
                        semantic_tags=ctx_data.get("semantic_tags", []),
                        keywords=ctx_data.get("keywords", []),
                        domain=ctx_data.get("domain", "general"),
                        sentiment=ctx_data.get("sentiment", "neutral"),
                        importance=ctx_data.get("importance", 0.5),
                        outcome=ctx_data.get("outcome"),
                        embedding=ctx_data.get("embedding"),
                        metadata=ctx_data.get("metadata", {}),
                    )

                    self._contexts[ctx_id] = context

                    # Rebuild indices
                    self._contexts_by_type[context.request_type].append(ctx_id)
                    self._contexts_by_domain[context.domain].append(ctx_id)
                    self._contexts_by_intent[context.intent].append(ctx_id)

            except Exception as e:
                print(f"Error loading contexts: {e}")

        # Load patterns
        if patterns_file.exists():
            try:
                with open(patterns_file, "r") as f:
                    data = json.load(f)

                self._pattern_counts = defaultdict(int, data.get("pattern_counts", {}))

                co_occurrence_data = data.get("co_occurrence", {})
                for k1, v in co_occurrence_data.items():
                    self._co_occurrence[k1] = defaultdict(float, v)

            except Exception as e:
                print(f"Error loading patterns: {e}")
