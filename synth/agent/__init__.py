"""
AI Agent components for SYNTH.

Transforms SYNTH from a tool to a True AI Agent with:
- Autonomous decision making
- Persistent memory
- Multi-step planning
- Tool use
- Self-correction
- Proactive behavior

## Quick Start

```python
# For programmatic use (API, automation, batch processing)
from synth.agent.factory import create_orchestrator_agent
agent = create_orchestrator_agent()
response = await agent.process_request("Generate 100 records")

# For interactive use (CLI, chat, exploration)
from synth.agent.factory import create_conversation_agent
agent = create_conversation_agent()
agent.run()  # Starts REPL

# Quick one-off requests
from synth.agent.factory import quick_start
result = quick_start("Generate 100 customer records")
```
"""

from synth.agent.true_ai_agent import TrueAIAgent
from synth.agent.cognitive import CognitiveLayer
from synth.agent.memory import MemoryLayer
from synth.agent.tools import ToolRegistry
from synth.agent.config import AgentConfig, get_config
from synth.agent.factory import (
    create_orchestrator_agent,
    create_conversation_agent,
    create_agent,
    quick_start,
)
from synth.agent.context import (
    ContextManager,
    ContextBuilder,
    ContextEnricher,
)

__version__ = "2.0.0"
__all__ = [
    # Main components
    "TrueAIAgent",
    "CognitiveLayer",
    "MemoryLayer",
    "ToolRegistry",

    # Configuration
    "AgentConfig",
    "get_config",

    # Factory functions (recommended)
    "create_orchestrator_agent",
    "create_conversation_agent",
    "create_agent",
    "quick_start",

    # Context management
    "ContextManager",
    "ContextBuilder",
    "ContextEnricher",
]
