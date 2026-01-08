"""
Intent Disambiguation - Advanced context understanding.

Implements:
- Intent clarification for ambiguous requests
- Context windowing for long conversations
- Multi-modal perception support
- Ambiguity resolution
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import re
from datetime import datetime

from synth.agent.models.core import (
    ParsedRequest,
    RequestType,
    Context,
)


class AmbiguityType(str, Enum):
    """Types of ambiguity."""
    MULTIPLE_INTERPRETATIONS = "multiple_interpretations"
    MISSING_CONTEXT = "missing_context"
    VAGUE_QUANTIFIERS = "vague_quantifiers"
    UNCLEAR_REFERENCE = "unclear_reference"
    CONFLICTING_CONSTRAINTS = "conflicting_constraints"


@dataclass
class AmbiguityDetection:
    """Detected ambiguity."""
    ambiguity_type: AmbiguityType
    ambiguous_text: str
    possible_interpretations: List[Dict[str, Any]]
    confidence: float
    clarification_needed: bool
    suggested_questions: List[str]


@dataclass
class DisambiguatedRequest:
    """Disambiguated request."""
    original_request: str
    resolved_intent: str
    request_type: RequestType
    confidence: float
    assumptions_made: List[str]
    context_used: List[str]


class IntentDisambiguator:
    """
    Advanced intent disambiguation system.

    Handles:
    - Ambiguous request interpretation
    - Context-aware understanding
    - Multi-conversation tracking
    - Clarification question generation
    """

    def __init__(self, context_window_size: int = 10):
        """
        Initialize intent disambiguator.

        Args:
            context_window_size: Number of conversation turns to track
        """
        self.context_window_size = context_window_size
        self._conversation_history: List[Dict[str, Any]] = []
        self._user_preferences: Dict[str, Any] = {}
        self._context_embeddings: Dict[str, List[float]] = {}

    def analyze_request(
        self,
        request: str,
        context: Optional[Context] = None,
    ) -> Tuple[DisambiguatedRequest, List[AmbiguityDetection]]:
        """
        Analyze and disambiguate request.

        Args:
            request: User request string
            context: Optional current context

        Returns:
            Tuple of (disambiguated_request, ambiguities_detected)
        """
        # 1. Detect ambiguities
        ambiguities = self._detect_ambiguities(request, context)

        # 2. Resolve ambiguities using context
        resolved_request = self._resolve_ambiguities(request, ambiguities, context)

        # 3. Extract intent
        intent = self._extract_intent(resolved_request, context)

        # 4. Determine request type
        request_type = self._determine_request_type(resolved_request, context)

        # 5. Track in conversation history
        self._update_conversation_history(request, intent, request_type)

        return (
            DisambiguatedRequest(
                original_request=request,
                resolved_intent=intent,
                request_type=request_type,
                confidence=self._calculate_confidence(ambiguities),
                assumptions_made=self._extract_assumptions(ambiguities),
                context_used=self._get_context_keys_used(context),
            ),
            ambiguities,
        )

    def _detect_ambiguities(
        self,
        request: str,
        context: Optional[Context],
    ) -> List[AmbiguityDetection]:
        """Detect ambiguities in request."""
        ambiguities = []
        request_lower = request.lower()

        # Check for vague quantifiers
        vague_quantifiers = {
            "some": (1, 50),
            "few": (1, 10),
            "many": (50, 500),
            "lot of": (100, 1000),
            "couple": (2, 5),
        }

        for quantifier, (min_val, max_val) in vague_quantifiers.items():
            if quantifier in request_lower:
                ambiguities.append(AmbiguityDetection(
                    ambiguity_type=AmbiguityType.VAGUE_QUANTIFIERS,
                    ambiguous_text=quantifier,
                    possible_interpretations=[
                        {"interpretation": f"Use minimum ({min_val})", "value": min_val},
                        {"interpretation": f"Use maximum ({max_val})", "value": max_val},
                        {"interpretation": f"Use average ({(min_val + max_val) // 2})", "value": (min_val + max_val) // 2},
                    ],
                    confidence=0.6,
                    clarification_needed=True,
                    suggested_questions=[
                        f"How many records do you mean by '{quantifier}'?",
                        f"Should I use between {min_val} and {max_val} records?",
                    ],
                ))

        # Check for unclear references
        pronouns = ["it", "that", "this", "they", "those"]
        if any(pronoun in request_lower.split() for pronoun in pronouns):
            # Check if pronoun refers to something specific
            if not context or not self._resolve_pronoun_reference(request_lower, context):
                ambiguities.append(AmbiguityDetection(
                    ambiguity_type=AmbiguityType.UNCLEAR_REFERENCE,
                    ambiguous_text=request,
                    possible_interpretations=[
                        {"interpretation": "Refers to last generated data"},
                        {"interpretation": "Refers to original input data"},
                        {"interpretation": "Refers to validation results"},
                    ],
                    confidence=0.5,
                    clarification_needed=True,
                    suggested_questions=[
                        "What does 'it' refer to?",
                        "Are you referring to the original data or the generated data?",
                    ],
                ))

        # Check for missing context
        action_keywords = ["validate", "analyze", "export"]
        if any(keyword in request_lower for keyword in action_keywords):
            if not context or not context.working_variables.get("data"):
                ambiguities.append(AmbiguityDetection(
                    ambiguity_type=AmbiguityType.MISSING_CONTEXT,
                    ambiguous_text=request,
                    possible_interpretations=[
                        {"interpretation": "Use original data if available"},
                        {"interpretation": "Ask user to provide data"},
                        {"interpretation": "Use previously generated data"},
                    ],
                    confidence=0.8,
                    clarification_needed=True,
                    suggested_questions=[
                        "Which data should I use?",
                        "Do you want to use the original or generated data?",
                    ],
                ))

        # Check for multiple interpretations
        multiple_action_patterns = [
            (["generate", "validate"], "generate_and_validate"),
            (["validate", "export"], "validate_and_export"),
            (["analyze", "export"], "analyze_and_export"),
        ]

        for keywords, combined_intent in multiple_action_patterns:
            if all(keyword in request_lower for keyword in keywords):
                # Could be separate actions or combined
                ambiguities.append(AmbiguityDetection(
                    ambiguity_type=AmbiguityType.MULTIPLE_INTERPRETATIONS,
                    ambiguous_text=request,
                    possible_interpretations=[
                        {"interpretation": f"Do all actions as a combined workflow", "intent": combined_intent},
                        {"interpretation": f"Ask which action to perform first", "intent": "clarify_order"},
                        {"interpretation": f"Perform actions in sequence", "intent": "sequential"},
                    ],
                    confidence=0.4,
                    clarification_needed=False,  # Default to sequential
                    suggested_questions=[
                        "Should I perform these actions in sequence?",
                        "Do you want all actions completed or just one?",
                    ],
                ))

        return ambiguities

    def _resolve_ambiguities(
        self,
        request: str,
        ambiguities: List[AmbiguityDetection],
        context: Optional[Context],
    ) -> str:
        """Resolve ambiguities using context and preferences."""
        resolved = request

        for ambiguity in ambiguities:
            if ambiguity.ambiguity_type == AmbiguityType.VAGUE_QUANTIFIERS:
                # Use average value
                interpretations = ambiguity.possible_interpretations
                if interpretations:
                    # Use the average (middle) interpretation
                    avg_interpretation = interpretations[len(interpretations) // 2]
                    value = avg_interpretation.get("value", 100)
                    resolved = re.sub(
                        ambiguity.ambiguous_text,
                        str(value),
                        resolved,
                        flags=re.IGNORECASE,
                    )

            elif ambiguity.ambiguity_type == AmbiguityType.UNCLEAR_REFERENCE:
                # Resolve to most recent data
                if context and context.working_variables.get("data"):
                    # Assume they mean the working data
                    pass  # Keep original, will be resolved in execution

            elif ambiguity.ambiguity_type == AmbiguityType.MULTIPLE_INTERPRETATIONS:
                # Default to sequential execution
                pass  # Already handled in planning

        return resolved

    def _resolve_pronoun_reference(self, request_lower: str, context: Context) -> bool:
        """Try to resolve pronoun reference."""
        if not context:
            return False

        # Check conversation history
        recent_turns = self._conversation_history[-5:]
        for turn in reversed(recent_turns):
            if turn.get("data_generated"):
                return True  # Pronoun likely refers to generated data
            if turn.get("original_data"):
                return True  # Pronoun likely refers to original data

        return False

    def _extract_intent(self, request: str, context: Optional[Context]) -> str:
        """Extract clear intent from request."""
        # Remove ambiguity markers
        intent = request.strip()

        # Use conversation context to clarify
        if self._conversation_history:
            last_action = self._conversation_history[-1].get("action")
            if last_action:
                intent = f"{intent} (following: {last_action})"

        return intent

    def _determine_request_type(self, request: str, context: Optional[Context]) -> RequestType:
        """Determine request type with context awareness."""
        request_lower = request.lower()

        # Collect all detected types
        detected_types = []

        if any(word in request_lower for word in ["generate", "create", "synthetic"]):
            detected_types.append(RequestType.DATA_GENERATION)
        if any(word in request_lower for word in ["analyze", "examine", "study"]):
            detected_types.append(RequestType.DATA_ANALYSIS)
        if any(word in request_lower for word in ["validate", "check", "verify"]):
            detected_types.append(RequestType.DATA_VALIDATION)
        if any(word in request_lower for word in ["export", "save", "write"]):
            detected_types.append(RequestType.DATA_EXPORT)

        # Determine final type
        if len(detected_types) > 1:
            return RequestType.MULTI_OBJECTIVE
        elif len(detected_types) == 1:
            return detected_types[0]
        else:
            return RequestType.UNKNOWN

    def _calculate_confidence(self, ambiguities: List[AmbiguityDetection]) -> float:
        """Calculate confidence in disambiguation."""
        if not ambiguities:
            return 1.0

        # Start with base confidence
        confidence = 0.8

        # Reduce confidence for each ambiguity
        for ambiguity in ambiguities:
            if ambiguity.clarification_needed:
                confidence -= 0.15
            else:
                confidence -= 0.05

        return max(confidence, 0.3)

    def _extract_assumptions(self, ambiguities: List[AmbiguityDetection]) -> List[str]:
        """Extract assumptions made during disambiguation."""
        assumptions = []

        for ambiguity in ambiguities:
            if not ambiguity.clarification_needed:
                # We made an assumption
                if ambiguity.possible_interpretations:
                    chosen = ambiguity.possible_interpretations[
                        len(ambiguity.possible_interpretations) // 2
                    ]
                    assumptions.append(f"Assumed: {chosen.get('interpretation', 'unknown')}")

        return assumptions

    def _get_context_keys_used(self, context: Optional[Context]) -> List[str]:
        """Get list of context keys used."""
        if not context:
            return []

        used = []
        if context.working_variables.get("data"):
            used.append("working_data")
        if self._conversation_history:
            used.append("conversation_history")
        if context.request.entities:
            used.append("request_entities")

        return used

    def _update_conversation_history(
        self,
        request: str,
        intent: str,
        request_type: RequestType,
    ):
        """Update conversation history with context windowing."""
        turn = {
            "timestamp": str(datetime.now()),
            "request": request,
            "intent": intent,
            "request_type": request_type.value,
            "action": intent.split()[0] if intent else "unknown",
        }

        self._conversation_history.append(turn)

        # Maintain context window
        if len(self._conversation_history) > self.context_window_size:
            self._conversation_history = self._conversation_history[-self.context_window_size:]

    def generate_clarification_questions(
        self,
        ambiguities: List[AmbiguityDetection],
    ) -> List[str]:
        """Generate clarification questions for user."""
        questions = []

        for ambiguity in ambiguities:
            if ambiguity.clarification_needed:
                questions.extend(ambiguity.suggested_questions)

        return questions

    def learn_user_preference(self, preference: str, value: Any):
        """Learn user preference for future disambiguation."""
        self._user_preferences[preference] = value

    def get_context_summary(self) -> Dict[str, Any]:
        """Get summary of conversation context."""
        return {
            "total_turns": len(self._conversation_history),
            "recent_actions": [t.get("action") for t in self._conversation_history[-5:]],
            "user_preferences": self._user_preferences,
            "context_window_size": self.context_window_size,
        }
