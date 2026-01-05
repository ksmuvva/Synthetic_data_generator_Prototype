#!/usr/bin/env python3
"""
CLI UI Demo - Visualize the AI Agent interface.

Shows what the CLI looks like without requiring API keys.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.text import Text
from rich.table import Table


def show_welcome_screen(provider_name="Claude (Anthropic)"):
    """Show the welcome screen."""
    console = Console()

    welcome_text = f"""
[bold cyan]AI Agent[/bold cyan] :robot:

[dim]Powered by {provider_name} with intelligent reasoning[/dim]

[dim]I'll help you create synthetic data through natural conversation.[/dim]

[dim]Type your request naturally, or 'help' for examples.[/dim]
[dim]Type 'exit' to quit.[/dim]
    """

    console.print(Panel(
        Markdown(welcome_text.strip()),
        border_style="bright_cyan",
        padding=(1, 2)
    ))


def show_conversation_example():
    """Show an example conversation."""
    console = Console()

    console.print("\n[bold cyan]Example Conversation:[/bold cyan]\n")

    # Simulated conversation
    messages = [
        ("User", "create 50 transactions"),
        ("AI", "I'll help you create 50 transaction records.\n\nLet me ask a few questions:\n\n1. What type of transactions? (financial, sales, inventory, etc.)"),
        ("User", "financial transactions"),
        ("AI", "Got it. Financial transactions.\n\n2. What fields do you need?\n   Common fields: transaction_id, amount, currency, date, merchant, category"),
        ("User", "transaction_id, amount, currency, date, merchant"),
        ("AI", "Perfect. Last question:\n\n3. What amount range? (min, max)"),
        ("User", "10 to 1000 USD"),
        ("AI", "[green]OK] All set![/green]\n\nGenerating 50 financial transactions...\n\nGenerated 50 records\nSaved to: transactions_20250105.csv"),
    ]

    for role, message in messages:
        if role == "User":
            console.print(f"[dim]>[/dim] {message}")
        else:
            console.print(f"[cyan]{message}[/cyan]")
        console.print()


def show_help_screen(provider_name="Claude (Anthropic)"):
    """Show the help screen."""
    console = Console()

    help_text = f"""
[bold]AI Agent - Commands:[/bold]

Just describe what you want naturally! Examples:
  "Create 50 customer records with name, email, age"
  "Generate financial transactions with amounts between $10 and $1000"
  "I need 100 user profiles for testing"
  "Use the ecommerce template and output to PDF"

[dim](Powered by {provider_name})[/dim]

[dim]Commands:[/dim]
  [dim]help[/dim]  - Show this help message
  [dim]exit[/dim]  - Exit the agent
    """

    console.print(Panel(
        Markdown(help_text.strip()),
        title="[bold]Help[/bold]",
        border_style="bright_blue",
        padding=(1, 2)
    ))


def show_provider_comparison():
    """Show provider options."""
    console = Console()

    table = Table(title="Available LLM Providers")
    table.add_column("Provider", style="cyan")
    table.add_column("CLI Command", style="green")
    table.add_column("Environment Variable", style="yellow")
    table.add_column("Features", style="blue")

    table.add_row(
        "Claude",
        "synth agent chat",
        "ANTHROPIC_API_KEY",
        "Extended thinking, 200K context"
    )
    table.add_row(
        "OpenAI GPT",
        "synth agent chat -p openai",
        "OPENAI_API_KEY",
        "GPT-4o, fast response"
    )
    table.add_row(
        "Gemini",
        "synth agent chat -p gemini",
        "GOOGLE_API_KEY",
        "1M context window"
    )

    console.print(table)


def main():
    """Run the UI demo."""
    console = Console()

    # Title
    console.print("\n[bold cyan]AI Agent - CLI UI Demo[/bold cyan]\n")

    # Show different provider options
    show_provider_comparison()
    console.print()

    # Show welcome screens for different providers
    providers = [
        ("Claude (Anthropic)", "Default - Claude with extended thinking"),
        ("GPT (OpenAI)", "OpenAI - GPT-4o"),
        ("Gemini (Google)", "Google - Gemini 1.5 Pro"),
    ]

    for provider, description in providers:
        console.print(f"\n[bold]{description}[/bold]")
        show_welcome_screen(provider)

    # Show help
    console.print()
    show_help_screen()

    # Show conversation example
    show_conversation_example()

    # Instructions
    console.print("\n[bold green]To use the AI Agent:[/bold green]")
    console.print("""
1. Set your API key:
   [dim]export ANTHROPIC_API_KEY=your_key[/dim]
   [dim]export OPENAI_API_KEY=your_key[/dim]
   [dim]export GOOGLE_API_KEY=your_key[/dim]

2. Start the agent:
   [cyan]synth agent chat[/cyan]

3. Or specify provider:
   [cyan]synth agent chat -p openai[/cyan]
   [cyan]synth agent chat -p gemini[/cyan]
    """)


if __name__ == "__main__":
    main()
