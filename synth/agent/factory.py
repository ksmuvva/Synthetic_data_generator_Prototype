"""
Unified Agent Factory.

Provides a single entry point for creating agents with the right configuration.
Resolves the "dual configuration" issue by providing a clear factory interface.

## Which Agent Should I Use?

1. **TrueAIAgent (synth.agent.true_ai_agent)** - Main orchestrator
   - Use for: Programmatic API, complex workflows, multi-step planning
   - Features: Full cognitive architecture, tool use, memory, learning
   - Best for: Integration into applications, batch processing, automation

2. **LLMSessionAgent (synth.agent.llm.session)** - Conversational REPL
   - Use for: Interactive CLI, chat interfaces, question-answering
   - Features: Natural language conversation, dynamic questioning, rich output
   - Best for: User interaction, exploration, setup wizards

## Quick Start

```python
from synth.agent.factory import create_agent

# Create agent with auto-detection based on use case
agent = create_agent(purpose="orchestration")  # or "conversation"

# Or use the shortcut for orchestration (most common)
from synth.agent.factory import create_orchestrator_agent
agent = create_orchestrator_agent()

# Or for conversation
from synth.agent.factory import create_conversation_agent
agent = create_conversation_agent()
```
"""

from typing import Optional, Any, Union
from pathlib import Path

from synth.agent.config import AgentConfig, get_config
from synth.agent.models.core import RequestType


def create_orchestrator_agent(
    config: Optional[AgentConfig] = None,
    storage_path: str = ".agent_memory",
    llm_provider: Optional[str] = None,
    enable_llm: bool = True,
) -> Any:
    """
    Create the main orchestrator agent for programmatic use.

    This is the agent you want for:
    - API integration
    - Complex workflows
    - Multi-step planning
    - Batch processing
    - Automation tasks

    Args:
        config: Agent configuration (uses default if None)
        storage_path: Path for memory storage
        llm_provider: LLM provider ("claude", "openai", "gemini")
        enable_llm: Enable LLM features

    Returns:
        TrueAIAgent instance

    Example:
        ```python
        from synth.agent.factory import create_orchestrator_agent

        agent = create_orchestrator_agent(llm_provider="claude")
        response = await agent.process_request("Generate 100 customer records")
        ```
    """
    from synth.agent.true_ai_agent import TrueAIAgent

    # Use provided config or get default
    if config is None:
        config = get_config()

    # Create agent
    agent = TrueAIAgent(
        storage_path=storage_path or config.memory.storage_path,
        llm_provider=llm_provider or config.llm.provider.value,
        enable_llm=enable_llm,
    )

    return agent


def create_conversation_agent(
    config: Optional[AgentConfig] = None,
    llm_provider: Optional[str] = None,
    show_thinking: bool = True,
    console: Optional[Any] = None,
) -> Any:
    """
    Create the conversational agent for interactive use.

    This is the agent you want for:
    - Interactive CLI
    - Chat interfaces
    - Question-answering
    - Setup wizards
    - Exploration

    Args:
        config: Agent configuration (uses default if None)
        llm_provider: LLM provider ("claude", "openai", "gemini")
        show_thinking: Show LLM thinking process
        console: Rich console instance

    Returns:
        LLMSessionAgent instance

    Example:
        ```python
        from synth.agent.factory import create_conversation_agent

        agent = create_conversation_agent(llm_provider="claude")
        agent.run()  # Starts REPL loop
        ```
    """
    from synth.agent.llm.session import TrueAIAgent as LLMSessionAgent
    from synth.agent.llm import get_llm_provider

    # Use provided config or get default
    if config is None:
        config = get_config()

    # Get LLM provider
    provider_name = llm_provider or config.llm.provider.value
    if provider_name == "anthropic":
        provider_name = "claude"

    llm = get_llm_provider(provider=provider_name, enable_thinking=show_thinking)

    # Create agent
    agent = LLMSessionAgent(
        llm=llm,
        show_thinking=show_thinking,
        console=console,
    )

    return agent


def create_agent(
    purpose: str = "orchestration",
    **kwargs
) -> Any:
    """
    Create an agent based on the intended purpose.

    This factory function automatically selects the right agent class
    based on your use case.

    Args:
        purpose: Type of agent ("orchestration" or "conversation")
        **kwargs: Additional arguments passed to the agent constructor

    Returns:
        Agent instance appropriate for the purpose

    Example:
        ```python
        from synth.agent.factory import create_agent

        # For programmatic use
        agent = create_agent(purpose="orchestration", llm_provider="claude")

        # For interactive use
        agent = create_agent(purpose="conversation", show_thinking=True)
        agent.run()
        ```
    """
    purpose_lower = purpose.lower()

    if purpose_lower in ["orchestration", "orchestrator", "api", "programmatic", "batch"]:
        return create_orchestrator_agent(**kwargs)
    elif purpose_lower in ["conversation", "conversational", "chat", "interactive", "repl"]:
        return create_conversation_agent(**kwargs)
    else:
        raise ValueError(
            f"Unknown purpose: {purpose}. "
            f"Use 'orchestration' or 'conversation'."
        )


def quick_start(
    request: str,
    llm_provider: Optional[str] = None,
) -> dict:
    """
    Quick start: Process a single request and return the result.

    This is the simplest way to use the agent for one-off requests.

    Args:
        request: Natural language request
        llm_provider: LLM provider (optional)

    Returns:
        Response dictionary with results

    Example:
        ```python
        from synth.agent.factory import quick_start

        result = quick_start("Generate 100 customer records with age, income, and segment")
        print(result["message"])
        ```
    """
    import asyncio

    agent = create_orchestrator_agent(llm_provider=llm_provider)

    # Run the async process
    try:
        response = asyncio.run(agent.process_request(request))
        return response.to_dict()
    except Exception as e:
        return {
            "success": False,
            "message": str(e),
            "data": None,
        }


# Convenience exports
__all__ = [
    "create_orchestrator_agent",
    "create_conversation_agent",
    "create_agent",
    "quick_start",
]
