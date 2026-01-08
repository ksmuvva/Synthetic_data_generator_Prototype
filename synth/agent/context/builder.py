"""
Context Builder - Dynamic Context Assembly.

Intelligently builds rich context from multiple sources:
- User request analysis
- Environment state
- Conversation history
- Memory retrieval
- User preferences
- Domain knowledge
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import json

from synth.agent.models.core import (
    ParsedRequest,
    Context,
    EnvironmentContext,
    RequestType,
)


class ContextBuilder:
    """
    Builds rich context from multiple sources.

    Gathers and combines information from various sources
    to create comprehensive context for decision making.
    """

    def __init__(
        self,
        memory_layer: Optional[Any] = None,
        enable_environment_sensing: bool = True,
        enable_conversation_tracking: bool = True,
        enable_preference_learning: bool = True,
    ):
        """
        Initialize context builder.

        Args:
            memory_layer: Memory layer for retrieving past interactions
            enable_environment_sensing: Enable environment context sensing
            enable_conversation_tracking: Enable conversation history tracking
            enable_preference_learning: Enable user preference learning
        """
        self.memory_layer = memory_layer
        self.enable_environment_sensing = enable_environment_sensing
        self.enable_conversation_tracking = enable_conversation_tracking
        self.enable_preference_learning = enable_preference_learning

        # Context enrichment caches
        self._conversation_cache: List[Dict] = []
        self._preference_cache: Dict[str, Any] = {}
        self._domain_cache: Dict[str, Any] = {}

    def build_context(
        self,
        request: ParsedRequest,
        additional_context: Optional[Dict[str, Any]] = None,
    ) -> Context:
        """
        Build comprehensive context from multiple sources.

        Args:
            request: Parsed user request
            additional_context: Optional additional context to include

        Returns:
            Rich Context object
        """
        # Build environment context
        environment = self._build_environment_context()

        # Gather conversation history
        conversation_history = self._gather_conversation_history(request)

        # Retrieve user preferences
        user_preferences = self._retrieve_user_preferences(request)

        # Find similar past situations
        similar_situations = self._find_similar_situations(request)

        # Initialize working variables
        working_variables = self._initialize_working_variables(request)

        # Merge additional context
        if additional_context:
            user_preferences.update(additional_context.get("user_preferences", {}))
            working_variables.update(additional_context.get("working_variables", {}))

        return Context(
            request=request,
            environment=environment,
            conversation_history=conversation_history,
            user_preferences=user_preferences,
            similar_past_situations=similar_situations,
            working_variables=working_variables,
        )

    def _build_environment_context(self) -> EnvironmentContext:
        """Build environment context."""
        import psutil
        import os

        environment = EnvironmentContext()

        if self.enable_environment_sensing:
            try:
                # System resources
                environment.available_memory_mb = psutil.virtual_memory().available / (1024 * 1024)
                environment.available_cpu_percent = psutil.cpu_percent(interval=0.1)
                environment.available_disk_gb = psutil.disk_usage('.').free / (1024 * 1024 * 1024)

                # Available data sources
                environment.available_data_sources = self._detect_data_sources()

                # Active sessions (could be enhanced with actual session tracking)
                environment.active_sessions = 1

            except Exception:
                # Fallback if psutil not available or fails
                environment.available_memory_mb = 8000.0
                environment.available_cpu_percent = 50.0
                environment.available_disk_gb = 50.0

        return environment

    def _detect_data_sources(self) -> List[str]:
        """Detect available data sources."""
        sources = []

        # Check for common data directories
        import os
        data_dirs = ["data", "datasets", "synth/input", "synth/patterns"]
        for dir_name in data_dirs:
            if os.path.exists(dir_name):
                sources.append(dir_name)

        return sources

    def _gather_conversation_history(
        self,
        request: ParsedRequest,
        max_turns: int = 10,
    ) -> List[Dict]:
        """
        Gather relevant conversation history.

        Args:
            request: Current request
            max_turns: Maximum number of recent turns to include

        Returns:
            List of conversation turns
        """
        if not self.enable_conversation_tracking:
            return []

        history = []

        # Add recent conversation turns from cache
        for turn in self._conversation_cache[-max_turns:]:
            history.append({
                "turn_id": turn.get("turn_id", ""),
                "user_message": turn.get("user_message", ""),
                "agent_response": turn.get("agent_response", ""),
                "timestamp": turn.get("timestamp", datetime.now().isoformat()),
            })

        # If memory layer available, retrieve relevant history
        if self.memory_layer:
            try:
                # Retrieve recent interactions from memory
                recent = self.memory_layer.get_recent_interactions(limit=max_turns)
                for interaction in recent:
                    if not any(h["turn_id"] == interaction.get("turn_id") for h in history):
                        history.append(interaction)
            except Exception:
                pass

        return history

    def _retrieve_user_preferences(self, request: ParsedRequest) -> Dict[str, Any]:
        """
        Retrieve user preferences based on request and history.

        Args:
            request: Current request

        Returns:
            Dictionary of user preferences
        """
        preferences = self._preference_cache.copy()

        # Analyze request to infer preferences
        entities = request.entities

        # Infer preferred output format
        if "format" in entities:
            preferences["preferred_format"] = entities["format"]

        # Infer preferred strategy
        if "strategy" in entities:
            preferences["preferred_strategy"] = entities["strategy"]

        # Infer privacy preference
        privacy_keywords = ["anonymous", "privacy", "gdpr", "hipaa"]
        if any(keyword in request.original_text.lower() for keyword in privacy_keywords):
            preferences["privacy_level"] = "high"

        # Infer quality preference
        quality_keywords = ["accurate", "realistic", "high quality", "detailed"]
        if any(keyword in request.original_text.lower() for keyword in quality_keywords):
            preferences["quality_preference"] = "high"

        # Infer speed preference
        speed_keywords = ["quick", "fast", "rapid", "asap"]
        if any(keyword in request.original_text.lower() for keyword in speed_keywords):
            preferences["speed_preference"] = "high"

        return preferences

    def _find_similar_situations(self, request: ParsedRequest) -> List[Dict]:
        """
        Find similar past situations from memory.

        Args:
            request: Current request

        Returns:
            List of similar situations
        """
        if not self.memory_layer:
            return []

        try:
            similar = self.memory_layer.find_similar_situations(
                request.original_text,
                max_results=3,
            )
            return similar
        except Exception:
            return []

    def _initialize_working_variables(self, request: ParsedRequest) -> Dict[str, Any]:
        """
        Initialize working variables for the request.

        Args:
            request: Current request

        Returns:
            Dictionary of working variables
        """
        variables = {
            "request_type": request.request_type,
            "intent": request.intent,
            "timestamp": datetime.now().isoformat(),
            "complexity": request.complexity,
            "confidence": request.confidence,
        }

        # Add entity-specific variables
        if "entity_type" in request.entities:
            variables["target_entity"] = request.entities["entity_type"]

        if "count" in request.entities:
            variables["target_count"] = request.entities["count"]

        if "source_file" in request.entities:
            variables["source_data"] = request.entities["source_file"]

        return variables

    def add_conversation_turn(
        self,
        user_message: str,
        agent_response: str,
        turn_id: Optional[str] = None,
    ):
        """
        Add a conversation turn to the cache.

        Args:
            user_message: User's message
            agent_response: Agent's response
            turn_id: Optional turn ID
        """
        if turn_id is None:
            turn_id = f"turn_{len(self._conversation_cache) + 1}"

        self._conversation_cache.append({
            "turn_id": turn_id,
            "user_message": user_message,
            "agent_response": agent_response,
            "timestamp": datetime.now().isoformat(),
        })

        # Keep cache size manageable
        if len(self._conversation_cache) > 50:
            self._conversation_cache = self._conversation_cache[-50:]

    def update_preferences(self, new_preferences: Dict[str, Any]):
        """
        Update user preference cache.

        Args:
            new_preferences: New preferences to add/update
        """
        self._preference_cache.update(new_preferences)

    def clear_conversation_history(self):
        """Clear conversation history cache."""
        self._conversation_cache = []

    def get_context_summary(self, context: Context) -> str:
        """
        Get a text summary of the context.

        Args:
            context: Context to summarize

        Returns:
            Text summary
        """
        lines = [
            "=== Context Summary ===",
            f"Request Type: {context.request.request_type.value}",
            f"Intent: {context.request.intent}",
            f"Complexity: {context.request.complexity:.2f}",
            f"Confidence: {context.request.confidence:.2f}",
            "",
            "Environment:",
            f"  Memory: {context.environment.available_memory_mb:.0f} MB",
            f"  CPU: {context.environment.available_cpu_percent:.0f}%",
            f"  Data Sources: {len(context.environment.available_data_sources)}",
            "",
            f"Conversation History: {len(context.conversation_history)} turns",
            f"Similar Situations: {len(context.similar_past_situations)}",
            f"User Preferences: {len(context.user_preferences)}",
            f"Working Variables: {len(context.working_variables)}",
        ]

        return "\n".join(lines)
