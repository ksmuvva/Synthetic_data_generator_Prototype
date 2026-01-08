"""Proactive behavior components for the AI Agent."""

from synth.agent.proactive.engine import ProactiveEngine
from synth.agent.proactive.enhanced import (
    EnhancedProactiveEngine,
    Opportunity,
    OpportunityType,
)
from synth.agent.proactive.smart_agent import (
    SmartProactiveAgent,
    ProactiveSuggestion,
    SuggestionUrgency,
    SuggestionCategory,
)

__all__ = [
    "ProactiveEngine",
    "EnhancedProactiveEngine",
    "Opportunity",
    "OpportunityType",
    "SmartProactiveAgent",
    "ProactiveSuggestion",
    "SuggestionUrgency",
    "SuggestionCategory",
]
