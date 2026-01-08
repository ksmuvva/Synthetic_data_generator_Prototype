"""
Session Manager - Manage user sessions across requests.

Implements:
- Session creation
- Session state management
- Session expiration
- Session cleanup
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import time

from synth.agent.agent.conversation import ConversationManager, ConversationContext


@dataclass
class Session:
    """User session."""
    session_id: str
    user_id: Optional[str]
    created_at: datetime
    last_activity: datetime
    conversation_id: str
    state: Dict[str, Any] = field(default_factory=dict)
    is_active: bool = True

    @property
    def age_seconds(self) -> float:
        """Get session age in seconds."""
        return (datetime.now() - self.created_at).total_seconds()

    @property
    def idle_seconds(self) -> float:
        """Get session idle time in seconds."""
        return (datetime.now() - self.last_activity).total_seconds()


class SessionManager:
    """
    Manage user sessions across requests.

    Handles:
    1. Session creation
    2. Session state management
    3. Session expiration
    4. Session cleanup
    """

    # Default session timeout (30 minutes)
    DEFAULT_SESSION_TIMEOUT = 1800

    def __init__(
        self,
        conversation_manager: ConversationManager,
        session_timeout: int = DEFAULT_SESSION_TIMEOUT,
    ):
        """
        Initialize session manager.

        Args:
            conversation_manager: Conversation manager for conversations
            session_timeout: Session timeout in seconds
        """
        self.conversation_manager = conversation_manager
        self.session_timeout = session_timeout
        self._sessions: Dict[str, Session] = {}
        self._user_sessions: Dict[str, str] = {}  # user_id -> session_id

    def create_session(
        self,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> Session:
        """
        Create a new session.

        Args:
            user_id: Optional user ID
            session_id: Optional session ID (auto-generated if not provided)

        Returns:
            Session object
        """
        if session_id is None:
            session_id = f"session_{int(time.time())}_{id(self)}"

        # Create conversation for this session
        conversation_id = f"conv_{session_id}"
        self.conversation_manager.create_conversation(
            conversation_id,
            user_id,
        )

        now = datetime.now()
        session = Session(
            session_id=session_id,
            user_id=user_id,
            created_at=now,
            last_activity=now,
            conversation_id=conversation_id,
        )

        self._sessions[session_id] = session

        # Track by user ID if provided
        if user_id:
            self._user_sessions[user_id] = session_id

        return session

    def get_session(
        self,
        session_id: str,
    ) -> Optional[Session]:
        """
        Get a session by ID.

        Args:
            session_id: Session ID

        Returns:
            Session if found and active, None otherwise
        """
        session = self._sessions.get(session_id)

        if session is None:
            return None

        # Check if session is expired
        if not session.is_active or session.idle_seconds > self.session_timeout:
            return None

        return session

    def get_session_by_user(
        self,
        user_id: str,
    ) -> Optional[Session]:
        """
        Get active session for a user.

        Args:
            user_id: User ID

        Returns:
            Session if found and active, None otherwise
        """
        session_id = self._user_sessions.get(user_id)

        if session_id is None:
            return None

        return self.get_session(session_id)

    def update_session(
        self,
        session_id: str,
        state_updates: Optional[Dict[str, Any]] = None,
    ) -> Optional[Session]:
        """
        Update a session.

        Args:
            session_id: Session ID
            state_updates: Optional state updates to apply

        Returns:
            Updated session if found, None otherwise
        """
        session = self.get_session(session_id)

        if session is None:
            return None

        # Update last activity
        session.last_activity = datetime.now()

        # Apply state updates
        if state_updates:
            session.state.update(state_updates)

        return session

    def get_or_create_session(
        self,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> Session:
        """
        Get existing session or create new one.

        Args:
            user_id: Optional user ID
            session_id: Optional session ID

        Returns:
            Session object (existing or new)
        """
        # Try to get existing session
        if session_id:
            session = self.get_session(session_id)
            if session:
                return session

        if user_id:
            session = self.get_session_by_user(user_id)
            if session:
                return session

        # Create new session
        return self.create_session(user_id, session_id)

    def cleanup_expired(self) -> int:
        """
        Clean up expired sessions.

        Returns:
            Number of sessions cleaned up
        """
        expired = []

        for session_id, session in self._sessions.items():
            if not session.is_active or session.idle_seconds > self.session_timeout:
                expired.append(session_id)

        for session_id in expired:
            self._sessions.pop(session_id, None)

        # Clean up user_sessions mapping
        self._user_sessions = {
            user_id: sess_id
            for user_id, sess_id in self._user_sessions.items()
            if sess_id in self._sessions
        }

        return len(expired)

    def end_session(
        self,
        session_id: str,
    ):
        """
        End a session.

        Args:
            session_id: Session ID
        """
        session = self._sessions.get(session_id)

        if session:
            # Mark as inactive
            session.is_active = False

            # End conversation
            self.conversation_manager.end_conversation(session.conversation_id)

            # Remove from active sessions
            self._sessions.pop(session_id, None)

            # Remove from user_sessions
            if session.user_id:
                self._user_sessions.pop(session.user_id, None)

    def get_active_sessions(self) -> list[Session]:
        """
        Get all active sessions.

        Returns:
            List of active sessions
        """
        active = []

        for session in self._sessions.values():
            if session.is_active and session.idle_seconds <= self.session_timeout:
                active.append(session)

        return active

    def get_session_stats(self) -> Dict[str, Any]:
        """
        Get session statistics.

        Returns:
            Statistics dict
        """
        active_sessions = self.get_active_sessions()

        return {
            "total_sessions": len(self._sessions),
            "active_sessions": len(active_sessions),
            "unique_users": len(self._user_sessions),
            "session_timeout": self.session_timeout,
        }
