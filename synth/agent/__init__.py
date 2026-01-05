"""
AI Agent for Synth - LLM-Powered.

Provides conversational interface for synthetic data generation
using LLM providers (Claude, OpenAI, Gemini).
"""

# State management (shared)
from synth.agent.state import (
    ConversationState,
    Message,
    MessageRole,
    ParsedIntent,
    IntentType,
    FieldSpec,
    Constraint,
)

# LLM components
from synth.agent.llm.session import TrueAIAgent
from synth.agent.llm.parser import LLMIntentParser, LLMReasoningEngine
from synth.agent.llm.wizard import run_setup_wizard, SetupWizard
from synth.agent.llm import (
    LLMMessage,
    LLMResponse,
    LLMProvider,
    ClaudeProvider,
    OpenAIProvider,
    GeminiProvider,
    get_llm_provider,
)

# Schema builder (shared)
from synth.agent.schema_builder import SchemaBuilder

# Templates (shared)
from synth.agent.templates.base import get_template_library

__all__ = [
    # LLM Agent
    "TrueAIAgent",
    # Setup Wizard
    "run_setup_wizard",
    "SetupWizard",
    # LLM Components
    "LLMIntentParser",
    "LLMReasoningEngine",
    "LLMMessage",
    "LLMResponse",
    "LLMProvider",
    "ClaudeProvider",
    "OpenAIProvider",
    "GeminiProvider",
    "get_llm_provider",
    # State
    "ConversationState",
    "Message",
    "MessageRole",
    "ParsedIntent",
    "IntentType",
    "FieldSpec",
    "Constraint",
    # Schema & Templates
    "SchemaBuilder",
    "get_template_library",
]
