"""
Memory layer - unifies short-term and long-term memory.

Provides a single interface for all memory operations.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime

from synth.agent.memory.short_term import ShortTermMemory
from synth.agent.memory.long_term import LongTermMemory
from synth.agent.models.core import (
    ParsedRequest,
    Context,
    Plan,
    Error,
    Diagnosis,
    Correction,
)


class MemoryLayer:
    """
    Unified memory layer.

    Combines short-term and long-term memory into a single interface.
    """

    def __init__(self, storage_path: str = ".agent_memory", max_turns: int = 100):
        """
        Initialize memory layer.

        Args:
            storage_path: Path for persistent storage
            max_turns: Maximum conversation turns to keep in short-term memory
        """
        self.short_term = ShortTermMemory(max_turns=max_turns)
        self.long_term = LongTermMemory(storage_path=storage_path)

    # Conversation Management
    def store_conversation_turn(
        self,
        user_message: str,
        agent_response: str,
        context_state: Dict[str, Any],
    ) -> str:
        """
        Store a conversation turn.

        Args:
            user_message: User's message
            agent_response: Agent's response
            context_state: Current context state

        Returns:
            Turn ID
        """
        return self.short_term.store_turn(user_message, agent_response, context_state)

    def get_conversation_history(self, n: int = 10) -> List[Dict[str, Any]]:
        """
        Get conversation history.

        Args:
            n: Number of recent turns to retrieve

        Returns:
            List of conversation turn dictionaries
        """
        turns = self.short_term.get_recent_turns(n)
        return [turn.to_dict() for turn in turns]

    # Working State
    def set_variable(self, key: str, value: Any) -> None:
        """Set working variable."""
        self.short_term.set_working_variable(key, value)

    def get_variable(self, key: str) -> Optional[Any]:
        """Get working variable."""
        return self.short_term.get_working_variable(key)

    def get_working_state(self) -> Dict[str, Any]:
        """Get all working state."""
        return self.short_term.get_working_state()

    # Pattern Learning
    def learn_pattern(
        self, dataset_id: str, field: str, pattern: Dict[str, Any]
    ) -> None:
        """
        Learn a data pattern.

        Args:
            dataset_id: Dataset identifier
            field: Field name
            pattern: Pattern dictionary
        """
        self.long_term.store_pattern(dataset_id, field, pattern)

    def recall_pattern(self, dataset_id: str, field: str) -> Optional[Dict[str, Any]]:
        """
        Recall a learned pattern.

        Args:
            dataset_id: Dataset identifier
            field: Field name

        Returns:
            Pattern if found, None otherwise
        """
        return self.long_term.get_pattern(dataset_id, field)

    def recall_all_patterns(self, dataset_id: str) -> Dict[str, Any]:
        """
        Recall all patterns for a dataset.

        Args:
            dataset_id: Dataset identifier

        Returns:
            Dictionary of field -> pattern
        """
        return self.long_term.get_all_patterns(dataset_id)

    # Strategy Learning
    def learn_strategy_outcome(
        self,
        strategy: str,
        context: Context,
        success: bool,
        metrics: Dict[str, float],
    ) -> None:
        """
        Learn from strategy outcome.

        Args:
            strategy: Strategy name
            context: Execution context
            success: Whether strategy succeeded
            metrics: Performance metrics
        """
        context_dict = context.to_dict()
        self.long_term.record_strategy_outcome(strategy, context_dict, success, metrics)

    def recall_best_strategy(self, context: Context) -> Optional[str]:
        """
        Recall best strategy for context.

        Args:
            context: Current context

        Returns:
            Best strategy name if found, None otherwise
        """
        context_dict = context.to_dict()
        return self.long_term.get_best_strategy(context_dict)

    def get_strategy_stats(self, strategy: str) -> Optional[Dict[str, Any]]:
        """
        Get strategy statistics.

        Args:
            strategy: Strategy name

        Returns:
            Strategy statistics if found, None otherwise
        """
        return self.long_term.get_strategy_stats(strategy)

    # Error Learning
    def learn_error_solution(self, error: Error, solution: Correction) -> None:
        """
        Learn error solution.

        Args:
            error: Error that occurred
            solution: Correction that worked
        """
        solution_dict = {
            "correction_type": solution.correction_type,
            "description": solution.description,
            "steps": solution.steps,
        }
        self.long_term.store_error_solution(error.error_type, solution_dict)

    def recall_error_solution(self, error_type: str) -> Optional[Dict[str, Any]]:
        """
        Recall solution for error type.

        Args:
            error_type: Type of error

        Returns:
            Solution if found, None otherwise
        """
        return self.long_term.get_error_solution(error_type)

    def record_solution_worked(self, error_type: str, solution: Dict[str, Any]) -> None:
        """
        Record that a solution worked.

        Args:
            error_type: Type of error
            solution: Solution that worked
        """
        self.long_term.record_solution_success(error_type, solution)

    # Similar Situations
    def find_similar_situations(
        self, request: str, max_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find similar past situations.

        Args:
            request: Current request
            max_results: Maximum number of results

        Returns:
            List of similar interactions
        """
        return self.long_term.find_similar_requests(request, max_results)

    # Interaction Recording
    def record_interaction(
        self,
        request: ParsedRequest,
        response: Dict[str, Any],
        metadata: Dict[str, Any],
    ) -> None:
        """
        Record interaction for learning.

        Args:
            request: Parsed request
            response: Agent response
            metadata: Additional metadata
        """
        self.long_term.record_interaction(
            request.original_text,
            response,
            metadata,
        )

    # User Preferences
    def store_preferences(self, user_id: str, preferences: Dict[str, Any]) -> None:
        """
        Store user preferences.

        Args:
            user_id: User identifier
            preferences: User preferences
        """
        self.long_term.store_user_preferences(user_id, preferences)

    def get_preferences(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user preferences.

        Args:
            user_id: User identifier

        Returns:
            User preferences if found, None otherwise
        """
        return self.long_term.get_user_preferences(user_id)

    # Cleanup
    def clear_short_term(self) -> None:
        """Clear short-term memory."""
        self.short_term.clear()

    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics."""
        stats = {
            "short_term": self.short_term.get_stats(),
            "long_term": self.long_term.get_stats(),
        }
        return stats
