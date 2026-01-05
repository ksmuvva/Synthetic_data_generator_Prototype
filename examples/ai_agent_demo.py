#!/usr/bin/env python3
"""
AI Agent Demo - Multi-Provider LLM-Powered Agent.

Demonstrates the completely LLM-driven AI agent with support for:
- Anthropic Claude
- OpenAI GPT
- Google Gemini

Usage:
    # Set your API key first
    export ANTHROPIC_API_KEY=your_key_here
    # or
    export OPENAI_API_KEY=your_key_here
    # or
    export GOOGLE_API_KEY=your_key_here

    # Run the demo
    python examples/ai_agent_demo.py

    # Or use CLI directly
    synth agent chat
    synth agent chat -p openai
    synth agent chat -p gemini
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.syntax import Syntax

from synth.agent.llm import (
    LLMMessage,
    ClaudeProvider,
    OpenAIProvider,
    GeminiProvider,
    get_llm_provider,
)


def demo_provider_initialization(console: Console):
    """Demonstrate provider initialization."""
    console.print("\n[bold cyan]1. LLM Provider Initialization[/bold cyan]")
    console.print("[dim]Each provider requires its own API key[/dim]\n")

    # Show API key requirements
    table = Table(title="API Key Requirements")
    table.add_column("Provider", style="cyan")
    table.add_column("Environment Variable", style="green")
    table.add_column("Default Model", style="yellow")

    table.add_row("Claude", "ANTHROPIC_API_KEY", "claude-3-5-sonnet-20241022")
    table.add_row("OpenAI", "OPENAI_API_KEY", "gpt-4o")
    table.add_row("Gemini", "GOOGLE_API_KEY", "gemini-1.5-pro")

    console.print(table)

    # Demonstrate initialization with dummy keys
    console.print("\n[dim]Initializing providers with test keys...[/dim]\n")

    try:
        claude = ClaudeProvider(api_key="test_key_claude")
        console.print("  [green]OK] Claude provider initialized[/green]")
    except ImportError:
        console.print("  [yellow]SKIP] anthropic package not installed[/yellow]")

    try:
        openai = OpenAIProvider(api_key="test_key_openai")
        console.print("  [green]OK] OpenAI provider initialized[/green]")
    except ImportError:
        console.print("  [yellow]SKIP] openai package not installed[/yellow]")

    try:
        gemini = GeminiProvider(api_key="test_key_gemini")
        console.print("  [green]OK] Gemini provider initialized[/green]")
    except ImportError:
        console.print("  [yellow]SKIP] google-generativeai package not installed[/yellow]")


def demo_provider_factory(console: Console):
    """Demonstrate provider factory function."""
    console.print("\n[bold cyan]2. Provider Factory Function[/bold cyan]")
    console.print("[dim]get_llm_provider() supports multiple provider names[/dim]\n")

    provider_names = [
        ("claude", "Claude"),
        ("anthropic", "Claude (alias)"),
        ("openai", "OpenAI GPT"),
        ("gpt", "OpenAI GPT (alias)"),
        ("gemini", "Google Gemini"),
        ("google", "Google Gemini (alias)"),
    ]

    for name, description in provider_names:
        try:
            provider = get_llm_provider(provider=name, api_key="test_key")
            console.print(f"  [green]OK] '{name}' -> {description}[/green]")
        except ImportError:
            console.print(f"  [yellow]SKIP] '{name}' -> package not installed[/yellow]")


def demo_custom_parameters(console: Console):
    """Demonstrate custom parameters."""
    console.print("\n[bold cyan]3. Custom Parameters[/bold cyan]")
    console.print("[dim]Providers can be customized with model, temperature, etc.[/dim]\n")

    examples = [
        "Custom model (Claude Opus):",
        "    provider = get_llm_provider('claude', api_key=key, model='claude-3-opus-20240229')",
        "",
        "Custom temperature (more deterministic):",
        "    provider = get_llm_provider('openai', api_key=key, temperature=0.3)",
        "",
        "Custom max tokens:",
        "    provider = get_llm_provider('gemini', api_key=key, max_tokens=8192)",
    ]

    syntax = Syntax("\n".join(examples), "python", theme="monokai")
    console.print(syntax)


def demo_cli_usage(console: Console):
    """Show CLI usage examples."""
    console.print("\n[bold cyan]4. CLI Usage[/bold cyan]\n")

    usage_code = """
# Default: Use Claude
synth agent chat

# Use OpenAI GPT
synth agent chat --provider openai

# Use Google Gemini
synth agent chat -p gemini

# Specify custom model
synth agent chat -p claude -m claude-3-opus-20240229

# Adjust temperature (0.0 = deterministic, 1.0 = creative)
synth agent chat -p openai -t 0.3

# Hide thinking process
synth agent chat --hide-thinking

# Quick mode (non-interactive)
synth agent quick --prompt "50 transactions" --output data.csv
synth agent quick -p "100 customers" -o customers.pdf -f pdf --provider openai
"""

    syntax = Syntax(usage_code, "bash", theme="monokai", line_numbers=True)
    console.print(Panel(syntax, title="[bold]Usage Examples[/bold]", border_style="bright_blue"))


def demo_provider_comparison(console: Console):
    """Compare providers."""
    console.print("\n[bold cyan]5. Provider Comparison[/bold cyan]\n")

    table = Table(title="LLM Provider Features")
    table.add_column("Feature", style="cyan")
    table.add_column("Claude", style="green")
    table.add_column("OpenAI", style="yellow")
    table.add_column("Gemini", style="blue")

    table.add_row("API Library", "anthropic", "openai", "google-generativeai")
    table.add_row("Extended Thinking", "[green]Yes[/green]", "[red]No[/red]", "[red]No[/red]")
    table.add_row("JSON Mode", "Manual", "Manual", "Manual")
    table.add_row("Default Model", "claude-3-5-sonnet", "gpt-4o", "gemini-1.5-pro")
    table.add_row("Fast Models", "claude-3-haiku", "gpt-3.5-turbo", "gemini-1.5-flash")
    table.add_row("Input Context", "200K tokens", "128K tokens", "1M tokens")

    console.print(table)


def demo_architecture(console: Console):
    """Show architecture overview."""
    console.print("\n[bold cyan]6. Architecture Overview[/bold cyan]\n")

    architecture = """
AI Agent Architecture
====================

User Input
    |
    v
LLM Provider (Claude/OpenAI/Gemini)
    |
    +--> LLMIntentParser (extracts intent, entities, fields)
    |
    +--> LLMReasoningEngine (analyzes requirements, generates questions)
    |
    v
Conversation State Management
    |
    v
Schema Builder (builds schema from requirements)
    |
    v
Statistical Sampler (generates synthetic data)
    |
    v
Output Generators (CSV, Excel, PDF, Word)
    |
    v
Generated Data File
"""

    console.print(Panel(architecture.strip(), border_style="bright_cyan"))


def main():
    """Run all demos."""
    console = Console()

    # Print welcome
    welcome_text = """
[bold cyan]AI Agent - Multi-Provider LLM-Powered Agent[/bold cyan]

[dim]Completely LLM-driven synthetic data generation[/dim]

This demo shows:
- Multiple LLM provider support (Claude, OpenAI, Gemini)
- Provider initialization and configuration
- CLI usage examples
- Architecture overview
    """

    console.print(Panel(welcome_text.strip(), border_style="bright_cyan", padding=(1, 2)))

    # Run demos
    demo_provider_initialization(console)
    demo_provider_factory(console)
    demo_custom_parameters(console)
    demo_cli_usage(console)
    demo_provider_comparison(console)
    demo_architecture(console)

    # Print summary
    console.print("\n[bold green]Demo Complete![/bold green]")
    console.print("\n[dim]To use the AI agent:[/dim]")
    console.print("  1. Set your API key as environment variable")
    console.print("     [dim]- Claude: ANTHROPIC_API_KEY[/dim]")
    console.print("     [dim]- OpenAI: OPENAI_API_KEY[/dim]")
    console.print("     [dim]- Gemini: GOOGLE_API_KEY[/dim]")
    console.print("  2. Run: [cyan]synth agent chat[/cyan]")
    console.print("  3. Or specify provider: [cyan]synth agent chat -p openai[/cyan]")
    console.print()


if __name__ == "__main__":
    main()
