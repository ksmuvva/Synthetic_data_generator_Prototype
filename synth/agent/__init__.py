"""
AI Agent components for SYNTH.

Transforms SYNTH from a tool to a True AI Agent with:
- Autonomous decision making
- Persistent memory
- Multi-step planning
- Tool use
- Self-correction
- Proactive behavior
"""

from synth.agent.true_ai_agent import TrueAIAgent
from synth.agent.cognitive import CognitiveLayer
from synth.agent.memory import MemoryLayer
from synth.agent.tools import ToolRegistry

__version__ = "2.0.0"
__all__ = [
    "TrueAIAgent",
    "CognitiveLayer",
    "MemoryLayer",
    "ToolRegistry",
]
