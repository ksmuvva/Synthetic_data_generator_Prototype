"""
LLM-based intent parser using Claude.

Replaces rule-based regex parsing with actual natural language understanding.
"""

from typing import Optional, Dict, Any
import json

from synth.agent.llm import LLMMessage, get_llm_provider, LLMProvider
from synth.agent.state import (
    ParsedIntent,
    IntentType,
    FieldSpec,
    Constraint,
)


class LLMIntentParser:
    """
    LLM-powered intent parser using Claude.

    Self-Reflection: Uses Claude's natural language understanding
    to extract structured intent from conversational input, replacing
    brittle regex patterns with semantic comprehension.
    """

    # JSON schema for structured output
    INTENT_SCHEMA = {
        "type": "object",
        "properties": {
            "intent_type": {
                "type": "string",
                "enum": ["generate", "learn", "validate", "inspect", "upload", "use_template", "exit", "help", "unknown"]
            },
            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
            "entity_type": {"type": "string"},
            "record_count": {"type": "integer", "minimum": 1},
            "fields": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "data_type": {"type": "string"},
                        "description": {"type": "string"}
                    }
                }
            },
            "constraints": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "field": {"type": "string"},
                        "type": {"type": "string"},
                        "value": {}
                    }
                }
            },
            "output_format": {"type": "string"},
            "template_id": {"type": "string"},
            "needs_clarification": {"type": "boolean"},
            "missing_info": {"type": "array", "items": {"type": "string"}},
            "user_message_summary": {"type": "string"}
        },
        "required": ["intent_type", "confidence"]
    }

    def __init__(self, llm: Optional[LLMProvider] = None):
        """
        Initialize LLM intent parser.

        Args:
            llm: LLM provider (uses Claude by default)
        """
        self.llm = llm or get_llm_provider(provider="claude")
        self.conversation_history: list[LLMMessage] = []

    def parse(self, user_input: str, context: Optional[Dict] = None) -> ParsedIntent:
        """
        Parse user input into structured intent using LLM.

        Args:
            user_input: Raw user input string
            context: Additional context (previous messages, state, etc.)

        Returns:
            ParsedIntent with extracted information
        """
        # Build system prompt
        system_prompt = self._build_system_prompt()

        # Build user prompt with context
        user_prompt = self._build_user_prompt(user_input, context)

        # Messages for LLM
        messages = [
            LLMMessage(role="system", content=system_prompt),
            LLMMessage(role="user", content=user_prompt),
        ]

        # Get structured response
        try:
            result = self.llm.generate_structured(
                messages=messages,
                schema=self.INTENT_SCHEMA,
                temperature=0.3  # Lower temperature for more deterministic parsing
            )

            # Convert to ParsedIntent
            return self._convert_to_intent(result, user_input)

        except Exception as e:
            # Fallback to basic parsing
            return self._fallback_parse(user_input, str(e))

    def _build_system_prompt(self) -> str:
        """Build system prompt for intent parsing."""
        return """You are an intent parser for Synth, a synthetic data generation tool.

Your task is to analyze user requests and extract structured information about what they want to do.

**Intent Types:**
- generate: User wants to create synthetic data
- learn: User wants to extract patterns from existing data
- validate: User wants to validate data quality
- inspect: User wants to examine patterns
- upload: User is uploading a reference document
- use_template: User wants to use a pre-defined template
- exit: User wants to quit
- help: User wants help
- unknown: Intent is unclear

**Entity Types:**
Common entities: transaction, customer, order, product, user, patient, employee, sales, etc.

**Fields:**
Look for mentions of specific fields the user wants (e.g., "id", "name", "email", "amount", "date").

**Constraints:**
Look for value ranges (e.g., "age 18-80", "amount $10-$1000"), categories, formats.

**Output Format:**
CSV, Excel, PDF, Word, JSON

**Missing Information:**
If the request is incomplete, note what's missing in missing_info array.

Return your analysis as JSON matching the provided schema."""

    def _build_user_prompt(self, user_input: str, context: Optional[Dict]) -> str:
        """Build user prompt with context."""
        prompt = f"Analyze this user request:\n\n\"{user_input}\"\n\n"

        if context:
            prompt += "Context from conversation:\n"
            if "previous_messages" in context:
                prompt += "\nPrevious messages:\n"
                for msg in context["previous_messages"][-3:]:  # Last 3 messages
                    prompt += f"  {msg['role']}: {msg['content'][:100]}...\n"

            if "current_state" in context:
                state = context["current_state"]
                if state.get("entity_type"):
                    prompt += f"\nKnown entity: {state['entity_type']}"
                if state.get("record_count"):
                    prompt += f"\nKnown count: {state['record_count']}"
                if state.get("fields"):
                    prompt += f"\nKnown fields: {', '.join(state['fields'][:5])}"

        prompt += "\n\nProvide structured analysis as JSON."

        return prompt

    def _convert_to_intent(self, result: Dict, raw_input: str) -> ParsedIntent:
        """Convert LLM result to ParsedIntent."""
        # Map intent type string to enum
        intent_type_map = {
            "generate": IntentType.GENERATE,
            "learn": IntentType.LEARN,
            "validate": IntentType.VALIDATE,
            "inspect": IntentType.INSPECT,
            "upload": IntentType.UPLOAD,
            "use_template": IntentType.USE_TEMPLATE,
            "exit": IntentType.EXIT,
            "help": IntentType.HELP,
            "unknown": IntentType.UNKNOWN,
        }

        intent_type = intent_type_map.get(
            result.get("intent_type", "unknown"),
            IntentType.UNKNOWN
        )

        # Build ParsedIntent
        intent = ParsedIntent(
            intent_type=intent_type,
            raw_input=raw_input,
            confidence=result.get("confidence", 1.0),
            entity_type=result.get("entity_type"),
            record_count=result.get("record_count"),
            output_format=result.get("output_format", "csv"),
            template_id=result.get("template_id"),
        )

        # Extract fields
        if "fields" in result:
            for field_info in result["fields"]:
                if isinstance(field_info, dict):
                    name = field_info.get("name")
                    data_type = field_info.get("data_type")
                    if name:
                        intent.fields.append(FieldSpec(
                            name=name,
                            data_type=data_type or "string",
                            description=field_info.get("description", "")
                        ))

        # Extract constraints
        if "constraints" in result:
            for constraint_info in result["constraints"]:
                if isinstance(constraint_info, dict):
                    intent.constraints.append(Constraint(
                        field=constraint_info.get("field", ""),
                        type=constraint_info.get("type", ""),
                        value=constraint_info.get("value")
                    ))

        # Store additional info
        if result.get("needs_clarification"):
            intent.metadata = {
                "missing_info": result.get("missing_info", []),
                "summary": result.get("user_message_summary", "")
            }

        return intent

    def _fallback_parse(self, user_input: str, error: str) -> ParsedIntent:
        """Fallback to basic parsing if LLM fails."""
        # Simple keyword-based fallback
        user_input_lower = user_input.lower()

        # Detect intent type
        if any(word in user_input_lower for word in ["exit", "quit", "bye"]):
            return ParsedIntent(intent_type=IntentType.EXIT, raw_input=user_input)

        if any(word in user_input_lower for word in ["help", "?"]):
            return ParsedIntent(intent_type=IntentType.HELP, raw_input=user_input)

        # Default to generate
        return ParsedIntent(
            intent_type=IntentType.GENERATE,
            raw_input=user_input,
            confidence=0.5,
            metadata={"error": error}
        )


class LLMReasoningEngine:
    """
    LLM-powered reasoning engine using Claude.

    Self-Reflection: Uses Claude's chain-of-thought reasoning to
    dynamically generate questions and guide conversation, replacing
    pre-defined decision trees with contextual understanding.
    """

    def __init__(self, llm: Optional[LLMProvider] = None):
        """
        Initialize LLM reasoning engine.

        Args:
            llm: LLM provider (uses Claude by default)
        """
        self.llm = llm or get_llm_provider(provider="claude", enable_thinking=True)

    def analyze_requirements(
        self,
        user_input: str,
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Analyze user requirements using LLM reasoning.

        Args:
            user_input: Current user input
            context: Conversation context (history, state, etc.)

        Returns:
            Analysis with next question, completeness status, reasoning
        """
        schema = {
            "type": "object",
            "properties": {
                "is_complete": {"type": "boolean"},
                "next_action": {"type": "string", "enum": ["generate", "ask_question", "request_upload", "show_help"]},
                "next_question": {"type": "string"},
                "question_type": {"type": "string"},
                "reasoning": {"type": "string"},
                "suggested_answers": {"type": "array", "items": {"type": "string"}},
                "missing_information": {"type": "array", "items": {"type": "string"}},
                "extracted_info": {
                    "type": "object",
                    "properties": {
                        "entity_type": {"type": "string"},
                        "record_count": {"type": "integer"},
                        "fields": {"type": "array", "items": {"type": "string"}},
                        "constraints": {"type": "array", "items": {"type": "string"}},
                        "output_format": {"type": "string"}
                    }
                }
            }
        }

        system_prompt = """You are an AI assistant for Synth, a synthetic data generation tool.

**Your Role:**
Analyze user requests for synthetic data generation and determine:
1. If we have enough information to proceed
2. What questions to ask if we don't
3. What information has been provided

**Common Information Needed:**
- Entity type (what kind of data: transactions, customers, etc.)
- Record count (how many records to generate)
- Fields (what columns/attributes)
- Constraints (ranges, categories, formats)
- Output format (CSV, Excel, PDF, Word)

**Your Analysis:**
1. Understand what the user wants
2. Extract all provided information
3. Identify what's missing
4. Generate a natural, conversational next question
5. Show your reasoning process

Be conversational and helpful. Ask specific questions based on context."""

        user_prompt = f"User request: \"{user_input}\"\n\n"

        if context:
            user_prompt += "Conversation context:\n"
            if "history" in context:
                user_prompt += "\nPrevious conversation:\n"
                for msg in context["history"][-5:]:  # Last 5 messages
                    role = msg.get("role", "unknown")
                    content = msg.get("content", "")[:150]
                    user_prompt += f"  {role}: {content}...\n"

            if "current_state" in context:
                state = context["current_state"]
                user_prompt += "\nCurrent state:\n"
                if state:
                    for key, value in state.items():
                        if value is not None:
                            user_prompt += f"  {key}: {value}\n"

        user_prompt += "\n\nAnalyze the request and provide your structured response."

        messages = [
            LLMMessage(role="system", content=system_prompt),
            LLMMessage(role="user", content=user_prompt),
        ]

        try:
            result = self.llm.generate_structured(
                messages=messages,
                schema=schema,
                temperature=0.7
            )

            # Add reasoning from extended thinking if available
            if hasattr(self.llm, 'last_response'):
                response = self.llm.last_response
                if response.thinking:
                    result["reasoning"] = response.thinking

            return result

        except Exception as e:
            # Fallback response
            return {
                "is_complete": False,
                "next_action": "ask_question",
                "next_question": "I need more information. Could you provide more details?",
                "reasoning": f"LLM analysis failed: {str(e)}",
                "extracted_info": {}
            }
