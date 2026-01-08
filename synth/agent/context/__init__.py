"""
Context Management for AI Agent.

Provides intelligent context management with:
- Dynamic context building from multiple sources
- Semantic enrichment with LLM support
- Lifecycle management and persistence
- Pattern recognition and insights

## Quick Start

```python
from synth.agent.context import ContextManager

# Initialize context manager
context_manager = ContextManager(
    memory_layer=memory,
    llm_provider=llm,
    enable_persistence=True,
)

# Create context for request
context = context_manager.create_context(request)

# Get insights
insights = context_manager.get_context_insights()

# Update context with new information
context_manager.update_context(context_id, updates)
```
"""

from synth.agent.context.builder import ContextBuilder
from synth.agent.context.enricher import ContextEnricher
from synth.agent.context.manager import ContextManager

__all__ = [
    "ContextBuilder",
    "ContextEnricher",
    "ContextManager",
]
