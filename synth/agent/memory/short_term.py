"""
Short-term memory for the AI Agent.

Maintains conversation context and working state within a session.
"""

from collections import deque
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import uuid

from synth.agent.models.core import ConversationTurn


class ShortTermMemory:
    """
    Short-term conversation memory.

    Stores:
    - Recent conversation turns (max 100)
    - Current working state
    - Temporary variables with TTL
    """

    def __init__(self, max_turns: int = 100):
        """
        Initialize short-term memory.

        Args:
            max_turns: Maximum number of conversation turns to store
        """
        self.max_turns = max_turns
        self._turns: deque[ConversationTurn] = deque(maxlen=max_turns)
        self._working_state: Dict[str, Any] = {}
        self._temporary_variables: Dict[str, Dict[str, Any]] = {}

    def store_turn(
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
        turn = ConversationTurn(
            turn_id=str(uuid.uuid4()),
            user_message=user_message,
            agent_response=agent_response,
            context_state=context_state.copy(),
            timestamp=datetime.now(),
        )
        self._turns.append(turn)
        return turn.turn_id

    def get_recent_turns(self, n: int = 10) -> List[ConversationTurn]:
        """
        Get N most recent turns.

        Args:
            n: Number of turns to retrieve

        Returns:
            List of conversation turns
        """
        turns = list(self._turns)
        return turns[-n:] if n < len(turns) else turns

    def get_all_turns(self) -> List[ConversationTurn]:
        """Get all stored turns."""
        return list(self._turns)

    def get_turn(self, turn_id: str) -> Optional[ConversationTurn]:
        """
        Get a specific turn by ID.

        Args:
            turn_id: Turn ID

        Returns:
            Conversation turn if found, None otherwise
        """
        for turn in self._turns:
            if turn.turn_id == turn_id:
                return turn
        return None

    def set_working_variable(self, key: str, value: Any) -> None:
        """
        Set a working variable.

        Args:
            key: Variable key
            value: Variable value
        """
        self._working_state[key] = value

    def get_working_variable(self, key: str) -> Optional[Any]:
        """
        Get a working variable.

        Args:
            key: Variable key

        Returns:
            Variable value if exists, None otherwise
        """
        return self._working_state.get(key)

    def get_working_state(self) -> Dict[str, Any]:
        """Get all working state."""
        return self._working_state.copy()

    def clear_working_state(self) -> None:
        """Clear working state."""
        self._working_state.clear()

    def set_temporary(
        self, key: str, value: Any, ttl_seconds: int = 300
    ) -> None:
        """
        Set temporary variable with TTL.

        Args:
            key: Variable key
            value: Variable value
            ttl_seconds: Time to live in seconds
        """
        self._temporary_variables[key] = {
            "value": value,
            "expires_at": datetime.now().timestamp() + ttl_seconds,
        }

    def get_temporary(self, key: str) -> Optional[Any]:
        """
        Get temporary variable if not expired.

        Args:
            key: Variable key

        Returns:
            Variable value if exists and not expired, None otherwise
        """
        if key not in self._temporary_variables:
            return None

        entry = self._temporary_variables[key]
        if datetime.now().timestamp() > entry["expires_at"]:
            # Expired, remove it
            del self._temporary_variables[key]
            return None

        return entry["value"]

    def clear(self) -> None:
        """Clear all memory."""
        self._turns.clear()
        self._working_state.clear()
        self._temporary_variables.clear()

    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics."""
        return {
            "total_turns": len(self._turns),
            "working_vars": len(self._working_state),
            "temporary_vars": len(self._temporary_variables),
        }
