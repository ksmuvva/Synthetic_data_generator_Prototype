"""
Context Manager - Lifecycle Management.

Orchestrates context creation, enrichment, and lifecycle:
- Builds context from multiple sources
- Enriches with semantic understanding
- Updates context throughout request lifecycle
- Manages context persistence
- Provides context-based insights
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import json
from pathlib import Path

from synth.agent.models.core import (
    ParsedRequest,
    Context,
    RequestType,
)


class ContextManager:
    """
    Manages context lifecycle for AI agent.

    Orchestrates the creation, enrichment, and maintenance
    of rich context throughout the request lifecycle.
    """

    def __init__(
        self,
        memory_layer: Optional[Any] = None,
        llm_provider: Optional[Any] = None,
        storage_path: str = ".agent_context",
        enable_persistence: bool = True,
        enable_enrichment: bool = True,
    ):
        """
        Initialize context manager.

        Args:
            memory_layer: Memory layer for retrieving past interactions
            llm_provider: Optional LLM provider for semantic analysis
            storage_path: Path for context persistence
            enable_persistence: Enable context persistence to disk
            enable_enrichment: Enable context enrichment
        """
        self.memory_layer = memory_layer
        self.llm_provider = llm_provider
        self.storage_path = Path(storage_path)
        self.enable_persistence = enable_persistence
        self.enable_enrichment = enable_enrichment

        # Import builder and enricher
        from synth.agent.context.builder import ContextBuilder
        from synth.agent.context.enricher import ContextEnricher

        # Initialize components
        self.builder = ContextBuilder(
            memory_layer=memory_layer,
            enable_environment_sensing=True,
            enable_conversation_tracking=True,
            enable_preference_learning=True,
        )

        self.enricher = ContextEnricher(
            llm_provider=llm_provider,
            enable_semantic_analysis=True,
            enable_domain_knowledge=True,
            enable_pattern_recognition=True,
        ) if enable_enrichment else None

        # Context cache
        self._context_cache: Dict[str, Context] = {}
        self._active_context_id: Optional[str] = None

        # Statistics
        self._stats = {
            "contexts_created": 0,
            "contexts_enriched": 0,
            "contexts_updated": 0,
        }

        # Create storage directory if needed
        if self.enable_persistence:
            self.storage_path.mkdir(parents=True, exist_ok=True)

    def create_context(
        self,
        request: ParsedRequest,
        additional_context: Optional[Dict[str, Any]] = None,
        enrich: bool = None,
    ) -> Context:
        """
        Create and optionally enrich context for a request.

        Args:
            request: Parsed user request
            additional_context: Optional additional context
            enrich: Whether to enrich context (default: based on init setting)

        Returns:
            Rich context object
        """
        # Build base context
        context = self.builder.build_context(request, additional_context)

        # Generate context ID
        context_id = f"context_{request.request_id}"
        context.working_variables["context_id"] = context_id
        context.working_variables["created_at"] = datetime.now().isoformat()

        # Enrich if enabled
        should_enrich = enrich if enrich is not None else self.enable_enrichment
        if should_enrich and self.enricher:
            context = self.enricher.enrich(context)
            self._stats["contexts_enriched"] += 1

        # Cache context
        self._context_cache[context_id] = context
        self._active_context_id = context_id

        # Persist if enabled
        if self.enable_persistence:
            self._persist_context(context_id, context)

        self._stats["contexts_created"] += 1

        return context

    def update_context(
        self,
        context_id: str,
        updates: Dict[str, Any],
    ) -> Optional[Context]:
        """
        Update existing context with new information.

        Args:
            context_id: ID of context to update
            updates: Dictionary of updates to apply

        Returns:
            Updated context if found, None otherwise
        """
        context = self._context_cache.get(context_id)
        if not context:
            return None

        # Update working variables
        if "working_variables" in updates:
            context.working_variables.update(updates["working_variables"])

        # Update user preferences
        if "user_preferences" in updates:
            context.user_preferences.update(updates["user_preferences"])

        # Update conversation history
        if "conversation_turn" in updates:
            context.conversation_history.append(updates["conversation_turn"])

        # Add update timestamp
        context.working_variables["last_updated"] = datetime.now().isoformat()

        # Re-enrich if enricher available
        if self.enricher:
            context = self.enricher.enrich(context)

        # Persist updates
        if self.enable_persistence:
            self._persist_context(context_id, context)

        self._stats["contexts_updated"] += 1

        return context

    def get_context(self, context_id: str) -> Optional[Context]:
        """
        Retrieve cached context.

        Args:
            context_id: ID of context to retrieve

        Returns:
            Context if found, None otherwise
        """
        return self._context_cache.get(context_id)

    def get_active_context(self) -> Optional[Context]:
        """
        Get the currently active context.

        Returns:
            Active context if available, None otherwise
        """
        if self._active_context_id:
            return self._context_cache.get(self._active_context_id)
        return None

    def add_conversation_turn(
        self,
        user_message: str,
        agent_response: str,
        context_id: Optional[str] = None,
    ):
        """
        Add a conversation turn to context.

        Args:
            user_message: User's message
            agent_response: Agent's response
            context_id: Context ID (uses active if not specified)
        """
        ctx_id = context_id or self._active_context_id
        if not ctx_id:
            return

        # Add to builder's conversation cache
        turn_id = f"turn_{len(self._context_cache[ctx_id].conversation_history) + 1}"
        self.builder.add_conversation_turn(user_message, agent_response, turn_id)

        # Update context
        turn = {
            "turn_id": turn_id,
            "user_message": user_message,
            "agent_response": agent_response,
            "timestamp": datetime.now().isoformat(),
        }

        self.update_context(ctx_id, {"conversation_turn": turn})

    def update_preferences(
        self,
        new_preferences: Dict[str, Any],
        context_id: Optional[str] = None,
    ):
        """
        Update user preferences in context.

        Args:
            new_preferences: New preferences to add
            context_id: Context ID (uses active if not specified)
        """
        ctx_id = context_id or self._active_context_id
        if not ctx_id:
            return

        self.builder.update_preferences(new_preferences)
        self.update_context(ctx_id, {"user_preferences": new_preferences})

    def get_context_insights(
        self,
        context_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get insights from context.

        Args:
            context_id: Context ID (uses active if not specified)

        Returns:
            Dictionary of insights
        """
        ctx_id = context_id or self._active_context_id
        context = self._context_cache.get(ctx_id) if ctx_id else None

        if not context:
            return {}

        insights = {
            "request_analysis": {
                "type": context.request.request_type.value,
                "intent": context.request.intent,
                "complexity": context.request.complexity,
                "confidence": context.request.confidence,
            },
            "environment": {
                "available_memory_mb": context.environment.available_memory_mb,
                "cpu_available": 100 - context.environment.available_cpu_percent,
                "data_sources": len(context.environment.available_data_sources),
            },
            "conversation_depth": len(context.conversation_history),
            "user_preference_count": len(context.user_preferences),
            "similar_situations_found": len(context.similar_past_situations),
        }

        # Add enrichment insights if available
        if "semantic_concepts" in context.working_variables:
            insights["semantic_concepts"] = context.working_variables["semantic_concepts"]

        if "patterns" in context.working_variables:
            insights["detected_patterns"] = context.working_variables["patterns"]

        if "relationships" in context.working_variables:
            insights["entity_relationships"] = context.working_variables["relationships"]

        return insights

    def get_context_summary(
        self,
        context_id: Optional[str] = None,
    ) -> str:
        """
        Get text summary of context.

        Args:
            context_id: Context ID (uses active if not specified)

        Returns:
            Text summary
        """
        ctx_id = context_id or self._active_context_id
        context = self._context_cache.get(ctx_id) if ctx_id else None

        if not context:
            return "No context available."

        # Get base summary from builder
        summary = self.builder.get_context_summary(context)

        # Add enrichment summary if available
        if self.enricher:
            summary += "\n\n" + self.enricher.get_enrichment_summary(context)

        return summary

    def clear_context(self, context_id: Optional[str] = None):
        """
        Clear a context from cache.

        Args:
            context_id: Context ID to clear (active if not specified)
        """
        ctx_id = context_id or self._active_context_id
        if not ctx_id:
            return

        if ctx_id in self._context_cache:
            del self._context_cache[ctx_id]

        if ctx_id == self._active_context_id:
            self._active_context_id = None

        # Remove persisted file
        if self.enable_persistence:
            context_file = self.storage_path / f"{ctx_id}.json"
            if context_file.exists():
                context_file.unlink()

    def clear_all_contexts(self):
        """Clear all cached contexts."""
        self._context_cache.clear()
        self._active_context_id = None
        self.builder.clear_conversation_history()

    def get_statistics(self) -> Dict[str, int]:
        """
        Get context manager statistics.

        Returns:
            Dictionary of statistics
        """
        stats = self._stats.copy()
        stats["cached_contexts"] = len(self._context_cache)
        stats["cached_conversations"] = len(self._conversation_cache)
        return stats

    def _persist_context(self, context_id: str, context: Context):
        """
        Persist context to disk.

        Args:
            context_id: ID of context
            context: Context to persist
        """
        try:
            context_file = self.storage_path / f"{context_id}.json"
            with open(context_file, 'w') as f:
                json.dump(context.to_dict(), f, indent=2, default=str)
        except Exception as e:
            # Log but don't fail on persistence errors
            print(f"Warning: Could not persist context: {e}")

    def _load_context(self, context_id: str) -> Optional[Context]:
        """
        Load context from disk.

        Args:
            context_id: ID of context to load

        Returns:
            Loaded context if available, None otherwise
        """
        try:
            context_file = self.storage_path / f"{context_id}.json"
            if not context_file.exists():
                return None

            with open(context_file, 'r') as f:
                data = json.load(f)

            # Reconstruct Context from dict
            # This would need proper reconstruction logic
            return self._dict_to_context(data)

        except Exception as e:
            print(f"Warning: Could not load context: {e}")
            return None

    def _dict_to_context(self, data: Dict[str, Any]) -> Context:
        """Convert dictionary to Context object."""
        # Simplified reconstruction
        # In practice, you'd need full deserialization logic
        from synth.agent.models.core import ParsedRequest, EnvironmentContext

        request_data = data.get("request", {})
        request = ParsedRequest(
            request_id=request_data.get("request_id"),
            original_text=request_data.get("original_text", ""),
            intent=request_data.get("intent", ""),
            request_type=RequestType(request_data.get("request_type", "unknown")),
            entities=request_data.get("entities", {}),
        )

        env_data = data.get("environment", {})
        environment = EnvironmentContext(
            available_memory_mb=env_data.get("available_memory_mb", 0.0),
            available_cpu_percent=env_data.get("available_cpu_percent", 0.0),
        )

        return Context(
            request=request,
            environment=environment,
            conversation_history=data.get("conversation_history", []),
            user_preferences=data.get("user_preferences", {}),
            similar_past_situations=data.get("similar_past_situations", []),
            working_variables=data.get("working_variables", {}),
        )

    @property
    def _conversation_cache(self) -> List[Dict]:
        """Get conversation cache from builder."""
        return self.builder._conversation_cache

    def export_context(
        self,
        context_id: Optional[str] = None,
        format: str = "json",
    ) -> Optional[str]:
        """
        Export context to string.

        Args:
            context_id: Context ID (uses active if not specified)
            format: Export format ("json" or "summary")

        Returns:
            Exported context as string
        """
        ctx_id = context_id or self._active_context_id
        context = self._context_cache.get(ctx_id) if ctx_id else None

        if not context:
            return None

        if format == "json":
            return json.dumps(context.to_dict(), indent=2, default=str)
        elif format == "summary":
            return self.get_context_summary(ctx_id)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def import_context(
        self,
        context_data: str,
        format: str = "json",
    ) -> Optional[str]:
        """
        Import context from string.

        Args:
            context_data: Context data as string
            format: Import format ("json")

        Returns:
            Context ID if successful, None otherwise
        """
        if format != "json":
            raise ValueError(f"Unsupported format: {format}")

        try:
            data = json.loads(context_data)
            context = self._dict_to_context(data)

            context_id = context.working_variables.get("context_id")
            if not context_id:
                context_id = f"imported_{datetime.now().timestamp()}"

            self._context_cache[context_id] = context
            self._active_context_id = context_id

            return context_id

        except Exception as e:
            print(f"Error importing context: {e}")
            return None
