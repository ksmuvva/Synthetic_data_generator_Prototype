"""
Conversation state management for the interactive agent.

Program of Thoughts:
1. Define conversation state data structure
2. Track user inputs and responses
3. Maintain schema building progress
4. Support document uploads and templates
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional, Union
import json


class IntentType(Enum):
    """Types of user intents."""
    GENERATE = "generate"
    LEARN = "learn"
    VALIDATE = "validate"
    INSPECT = "inspect"
    UPLOAD = "upload"
    USE_TEMPLATE = "use_template"
    EXIT = "exit"
    HELP = "help"
    UNKNOWN = "unknown"


class MessageRole(Enum):
    """Roles in conversation."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


@dataclass
class FieldSpec:
    """Field specification from user."""
    name: str
    data_type: str  # integer, float, string, categorical, datetime, boolean
    description: Optional[str] = None
    unique: bool = False
    nullable: bool = True
    constraints: dict[str, Any] = field(default_factory=dict)
    generator: Optional[str] = None  # e.g., "person_name", "email", "uuid"


@dataclass
class Constraint:
    """Constraint specification."""
    field: str
    type: str  # range, enum, pattern, foreign_key
    value: Any


@dataclass
class Message:
    """Conversation message."""
    role: MessageRole
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ParsedIntent:
    """Parsed user intent."""
    intent_type: IntentType
    raw_input: str
    confidence: float = 1.0

    # Entity information
    entity_type: Optional[str] = None
    record_count: Optional[int] = None

    # Fields and constraints
    fields: list[Union[str, FieldSpec]] = field(default_factory=list)
    constraints: list[Constraint] = field(default_factory=list)

    # File/Template references
    file_path: Optional[Path] = None
    template_id: Optional[str] = None
    pattern_id: Optional[str] = None

    # Output preferences
    output_format: str = "csv"
    output_path: Optional[Path] = None


@dataclass
class ConversationState:
    """
    Conversation state for the interactive agent.

    Self-Reflection: Track what information has been collected
    and what's still needed to generate the synthetic data.
    """

    # Intent and entity
    intent: Optional[ParsedIntent] = None
    entity_type: Optional[str] = None
    record_count: Optional[int] = None

    # Schema being built
    fields: dict[str, FieldSpec] = field(default_factory=dict)
    constraints: list[Constraint] = field(default_factory=list)

    # Document uploads
    uploaded_documents: list[Path] = field(default_factory=list)
    loaded_patterns: list[str] = field(default_factory=list)

    # Template usage
    template_id: Optional[str] = None
    template_customizations: dict[str, Any] = field(default_factory=dict)

    # Output preferences
    output_format: str = "csv"
    output_path: Optional[Path] = None

    # Conversation history
    messages: list[Message] = field(default_factory=list)
    current_question_index: int = 0

    # Progress tracking
    questions_asked: list[str] = field(default_factory=list)
    answers_received: dict[str, Any] = field(default_factory=dict)

    # Validation state
    is_validated: bool = False
    validation_errors: list[str] = field(default_factory=list)

    def add_message(self, role: MessageRole, content: str, metadata: dict[str, Any] = None) -> None:
        """Add a message to conversation history."""
        message = Message(role=role, content=content, metadata=metadata or {})
        self.messages.append(message)

    def get_last_user_message(self) -> Optional[Message]:
        """Get the last user message."""
        for msg in reversed(self.messages):
            if msg.role == MessageRole.USER:
                return msg
        return None

    def get_field_names(self) -> list[str]:
        """Get list of field names."""
        return list(self.fields.keys())

    def has_fields(self) -> bool:
        """Check if any fields have been specified."""
        return len(self.fields) > 0

    def get_missing_info(self) -> dict[str, bool]:
        """
        Get information about what's missing from the state.

        Returns dict with keys:
        - entity_type: Is entity type specified?
        - record_count: Is record count specified?
        - fields: Are any fields specified?
        - constraints: Are enough constraints specified?
        - output_format: Is output format specified?
        """
        return {
            "entity_type": self.entity_type is not None,
            "record_count": self.record_count is not None,
            "fields": self.has_fields(),
            "output_format": self.output_format is not None,
        }

    def is_complete(self) -> bool:
        """
        Check if all required information is collected.

        Required for generation:
        - Entity type (or template)
        - Record count
        - At least one field
        - Output format
        """
        has_template = self.template_id is not None
        has_entity = self.entity_type is not None

        # Need either template or entity
        if not (has_template or has_entity):
            return False

        # Need record count
        if self.record_count is None:
            return False

        # Need fields (unless template provides them)
        if not has_template and not self.has_fields():
            return False

        return True

    def to_dict(self) -> dict[str, Any]:
        """Convert state to dictionary for serialization."""
        return {
            "entity_type": self.entity_type,
            "record_count": self.record_count,
            "fields": {
                name: {
                    "name": spec.name,
                    "data_type": spec.data_type,
                    "description": spec.description,
                    "unique": spec.unique,
                    "nullable": spec.nullable,
                    "constraints": spec.constraints,
                    "generator": spec.generator,
                }
                for name, spec in self.fields.items()
            },
            "constraints": [
                {
                    "field": c.field,
                    "type": c.type,
                    "value": c.value,
                }
                for c in self.constraints
            ],
            "uploaded_documents": [str(p) for p in self.uploaded_documents],
            "template_id": self.template_id,
            "output_format": self.output_format,
            "message_count": len(self.messages),
        }

    def summary(self) -> str:
        """Get a human-readable summary of the current state."""
        lines = [
            "Current Conversation State:",
            f"  Entity: {self.entity_type or 'Not specified'}",
            f"  Records: {self.record_count or 'Not specified'}",
            f"  Fields: {len(self.fields)} specified",
        ]

        if self.fields:
            lines.append("  Field list:")
            for name, spec in self.fields.items():
                lines.append(f"    - {name}: {spec.data_type}")

        if self.template_id:
            lines.append(f"  Template: {self.template_id}")

        lines.append(f"  Output format: {self.output_format}")

        return "\n".join(lines)
