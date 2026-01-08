"""
Conversation Manager - Manage multi-turn conversations.

Implements:
- Turn tracking
- Topic change detection
- Context maintenance
- Reference resolution
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime

from synth.agent.models.core import ParsedRequest
from synth.agent.memory.short_term import ShortTermMemory, ConversationTurn


@dataclass
class ConversationContext:
    """Context for a conversation."""
    conversation_id: str
    user_id: Optional[str]
    started_at: datetime
    current_topic: Optional[str] = None
    previous_topics: List[str] = field(default_factory=list)
    reference_map: Dict[str, Any] = field(default_factory=dict)
    turns_count: int = 0


class ConversationManager:
    """
    Manage multi-turn conversations.

    Handles:
    1. Turn tracking
    2. Topic change detection
    3. Context maintenance
    4. Reference resolution (pronouns, etc.)
    """

    def __init__(self, short_term_memory: ShortTermMemory):
        """
        Initialize conversation manager.

        Args:
            short_term_memory: Short-term memory for storing turns
        """
        self.memory = short_term_memory
        self._conversations: Dict[str, ConversationContext] = {}

    def create_conversation(
        self,
        conversation_id: str,
        user_id: Optional[str] = None,
    ) -> ConversationContext:
        """
        Create a new conversation.

        Args:
            conversation_id: Unique conversation ID
            user_id: Optional user ID

        Returns:
            ConversationContext object
        """
        context = ConversationContext(
            conversation_id=conversation_id,
            user_id=user_id,
            started_at=datetime.now(),
        )

        self._conversations[conversation_id] = context
        return context

    def add_turn(
        self,
        conversation_id: str,
        user_message: str,
        agent_response: str,
        parsed_request: Optional[ParsedRequest] = None,
        context_state: Optional[Dict[str, Any]] = None,
    ) -> ConversationTurn:
        """
        Add a turn to a conversation.

        Args:
            conversation_id: Conversation ID
            user_message: User's message
            agent_response: Agent's response
            parsed_request: Optional parsed request
            context_state: Optional context state

        Returns:
            ConversationTurn object
        """
        # Get conversation context
        conv_context = self._conversations.get(conversation_id)
        if conv_context is None:
            # Create if doesn't exist
            conv_context = self.create_conversation(conversation_id)

        # Store turn in memory
        turn = self.memory.store_turn(
            user_message,
            agent_response,
            context_state or {},
        )

        # Update conversation context
        conv_context.turns_count += 1

        # Detect topic change
        if parsed_request:
            new_topic = self._detect_topic(parsed_request)
            if new_topic and new_topic != conv_context.current_topic:
                if conv_context.current_topic:
                    conv_context.previous_topics.append(conv_context.current_topic)
                conv_context.current_topic = new_topic

        return turn

    def get_history(
        self,
        conversation_id: str,
        max_turns: int = 10,
    ) -> List[ConversationTurn]:
        """
        Get conversation history.

        Args:
            conversation_id: Conversation ID
            max_turns: Maximum number of turns to return

        Returns:
            List of ConversationTurn objects
        """
        return self.memory.get_recent_turns(max_turns)

    def detect_topic_change(
        self,
        conversation_id: str,
        parsed_request: ParsedRequest,
    ) -> bool:
        """
        Detect if topic has changed.

        Args:
            conversation_id: Conversation ID
            parsed_request: Current parsed request

        Returns:
            True if topic changed, False otherwise
        """
        conv_context = self._conversations.get(conversation_id)
        if conv_context is None:
            return False

        current_topic = conv_context.current_topic
        new_topic = self._detect_topic(parsed_request)

        return new_topic is not None and new_topic != current_topic

    def get_context(
        self,
        conversation_id: str,
    ) -> Optional[ConversationContext]:
        """
        Get conversation context.

        Args:
            conversation_id: Conversation ID

        Returns:
            ConversationContext if found, None otherwise
        """
        return self._conversations.get(conversation_id)

    def resolve_references(
        self,
        text: str,
        conversation_id: str,
    ) -> str:
        """
        Resolve references in text (pronouns, etc.).

        Args:
            text: Text with potential references
            conversation_id: Conversation ID

        Returns:
            Text with resolved references
        """
        conv_context = self._conversations.get(conversation_id)
        if conv_context is None:
            return text

        # Simple reference resolution
        # In a real system, this would use NLP
        resolved = text

        # Replace "it" with last mentioned object
        if "it" in text.lower():
            # Get from reference map
            for key, value in conv_context.reference_map.items():
                resolved = resolved.replace(f"it {key}", f"{value} {key}")
                resolved = resolved.replace(f"it.{key}", f"{value}.{key}")

        return resolved

    def update_reference_map(
        self,
        conversation_id: str,
        references: Dict[str, Any],
    ):
        """
        Update reference map for conversation.

        Args:
            conversation_id: Conversation ID
            references: New references to add
        """
        conv_context = self._conversations.get(conversation_id)
        if conv_context is None:
            return

        conv_context.reference_map.update(references)

    def maintain_context(
        self,
        conversation_id: str,
    ) -> Dict[str, Any]:
        """
        Get current context for conversation.

        Args:
            conversation_id: Conversation ID

        Returns:
            Context dict with relevant info
        """
        conv_context = self._conversations.get(conversation_id)
        if conv_context is None:
            return {}

        # Get recent turns
        recent_turns = self.memory.get_recent_turns(5)

        return {
            "conversation_id": conversation_id,
            "user_id": conv_context.user_id,
            "current_topic": conv_context.current_topic,
            "previous_topics": conv_context.previous_topics,
            "turns_count": conv_context.turns_count,
            "recent_turns": [
                {
                    "user": turn.user_message,
                    "agent": turn.agent_response,
                    "timestamp": turn.timestamp.isoformat() if turn.timestamp else None,
                }
                for turn in recent_turns
            ],
            "references": conv_context.reference_map,
        }

    def _detect_topic(self, parsed_request: ParsedRequest) -> Optional[str]:
        """Detect topic from parsed request."""
        # Simple topic detection based on request type
        request_type = parsed_request.request_type

        topic_map = {
            "data_generation": "data_generation",
            "data_analysis": "data_analysis",
            "data_validation": "data_validation",
            "data_export": "data_export",
        }

        return topic_map.get(request_type.value)

    def end_conversation(
        self,
        conversation_id: str,
    ):
        """
        End a conversation.

        Args:
            conversation_id: Conversation ID
        """
        self._conversations.pop(conversation_id, None)

    def get_all_conversations(self) -> List[str]:
        """
        Get all active conversation IDs.

        Returns:
            List of conversation IDs
        """
        return list(self._conversations.keys())
