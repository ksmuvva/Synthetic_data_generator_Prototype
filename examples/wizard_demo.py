#!/usr/bin/env python3
"""
Interactive Setup Wizard Demo.

Shows the complete user flow for setting up and using the AI Agent.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.layout import Layout
from rich.text import Text


def show_welcome_banner():
    """Show the welcome banner."""
    console = Console()

    banner = """
===============================================================================
                    Synthetic Data AI Agent Setup
===============================================================================

I'll guide you through setting up your AI-powered data generation agent.

Powered by state-of-the-art LLMs (Claude, GPT-4, Gemini) with advanced
natural language understanding and reasoning capabilities.
    """

    console.print(Panel(banner.strip(), border_style="bright_cyan", padding=(0, 2)))


def show_provider_selection():
    """Show provider selection screen."""
    console = Console()
    console.print("\n[bold cyan]Step 1: Select Your AI Provider\n")

    table = Table(title="Available LLM Providers", show_header=True, header_style="bold magenta")
    table.add_column("Option", style="cyan", width=8)
    table.add_column("Provider", style="green")
    table.add_column("Features", style="dim")

    table.add_row("1", "Claude (Anthropic)", "Extended thinking, 200K context, best reasoning")
    table.add_row("2", "GPT (OpenAI)", "GPT-4o, fast response, widely adopted")
    table.add_row("3", "Gemini (Google)", "1M context window, multimodal")

    console.print(table)
    console.print("\n[dim]User selects: 1[/dim]")
    console.print("[green]Selected: Claude (Anthropic)[/green]\n")


def show_model_selection():
    """Show model selection screen."""
    console = Console()
    console.print("\n[bold cyan]Step 2: Select Your Model\n")

    table = Table(title="Available Claude (Anthropic) Models", show_header=True, header_style="bold magenta")
    table.add_column("Option", style="cyan", width=8)
    table.add_column("Model", style="green")
    table.add_column("Description", style="dim")

    table.add_row("1", "Claude 3.5 Sonnet", "Best balance, intelligent reasoning")
    table.add_row("2", "Claude 3.5 Haiku", "Fastest, good for simple tasks")
    table.add_row("3", "Claude 3 Opus", "Most capable, highest quality")

    console.print(table)
    console.print("\n[dim]User selects: 1[/dim]")
    console.print("[green]Selected: Claude 3.5 Sonnet (claude-3-5-sonnet-20241022)[/green]\n")


def show_api_key_entry():
    """Show API key entry screen."""
    console = Console()
    console.print("\n[bold cyan]Step 3: Enter API Key\n")

    console.print("[dim]Get your API key from: https://console.anthropic.com/[/dim]\n")
    console.print("[dim]Enter your Claude (Anthropic) API key: ********************[/dim]")
    console.print("[green]API key accepted![/green]\n")


def show_requirements_gathering():
    """Show requirements gathering screen."""
    console = Console()
    console.print("\n[bold cyan]Step 4: Describe Your Data Needs\n")

    console.print("[dim]Tell me what kind of synthetic data you need.[/dim]")
    console.print("[dim]Be as specific as you like - the AI will understand!\n")

    console.print("[dim]Example prompts:[/dim]")
    console.print("  [dim]1.[/dim] Create 50 financial transactions with amounts between $10 and $1000")
    console.print("  [dim]2.[/dim] Generate 1000 customer records with names, emails, and addresses")
    console.print("  [dim]3.[/dim] I need user profiles for testing: 500 records with age, location, and preferences")

    console.print("\n[dim]User enters:[/dim] [cyan]Create 50 financial transactions with amounts between $10 and $1000, including transaction_id, amount, currency, date, and merchant fields[/cyan]")
    console.print()


def show_document_upload():
    """Show document upload screen."""
    console = Console()
    console.print("\n[bold cyan]Step 5: Upload Reference Documents (Optional)\n")

    console.print("[dim]You can upload existing data files as reference.[/dim]")
    console.print("[dim]The AI will analyze them to match structure and patterns.[/dim]")
    console.print("[dim]Supported formats: CSV, Excel, JSON, PDF\n")

    console.print("[dim]Do you want to upload any reference documents? [y/n]: n[/dim]")
    console.print()


def show_configuration_summary():
    """Show configuration summary."""
    console = Console()
    console.print("\n" + "="*70)
    console.print("[bold cyan]Configuration Summary\n")

    console.print("[cyan]Provider:[/cyan] Claude (Anthropic)")
    console.print("[cyan]Model:[/cyan] Claude 3.5 Sonnet (claude-3-5-sonnet-20241022)")
    console.print("[cyan]API Key:[/cyan] ********************")

    console.print("\n[cyan]Requirements:[/cyan]")
    console.print("  Create 50 financial transactions with amounts between $10 and $1000, including transaction_id, amount, currency, date, and merchant fields")

    console.print("\n[cyan]Uploaded Files:[/cyan] None")

    console.print("\n" + "="*70)

    console.print("\n[green]Setup complete![/green]")
    console.print("[dim]The AI will now analyze your requirements and begin generating data.[/dim]\n")


def show_ai_clarification_conversation():
    """Show the AI clarification conversation."""
    console = Console()
    console.print("[bold cyan]AI Agent is analyzing your requirements...[bold cyan]\n")

    console.print("[dim]AI: I understand you want 50 financial transactions. Let me clarify a few details:[/dim]\n")

    messages = [
        ("AI", "1. What currency should be used for the transactions?"),
        ("User", "USD"),
        ("AI", "2. What date range should the transactions cover?"),
        ("User", "January 2024 to December 2024"),
        ("AI", "3. Any specific merchant categories or types to include?"),
        ("User", "Retail, restaurants, and gas stations"),
        ("AI", "[green]Perfect! I have all the information needed.[/green]"),
        ("AI", "Generating 50 financial transactions..."),
        ("AI", ""),
        ("AI", "[green]Generated 50 records[/green]"),
        ("AI", "[green]Saved to: transactions_20250105.csv[/green]"),
    ]

    for role, message in messages:
        if role == "User":
            console.print(f"[dim]>[/dim] {message}")
        else:
            console.print(f"[cyan]{message}[/cyan]")
        console.print()


def show_complete_flow():
    """Show the complete flow."""
    console = Console()

    console.print("\n[bold cyan]=============================================================================[/bold cyan]")
    console.print("[bold cyan]         Synthetic Data AI Agent - Complete User Flow              [/bold cyan]")
    console.print("[bold cyan]=============================================================================[/bold cyan]\n")

    show_welcome_banner()
    show_provider_selection()
    show_model_selection()
    show_api_key_entry()
    show_requirements_gathering()
    show_document_upload()
    show_configuration_summary()
    show_ai_clarification_conversation()

    console.print("[bold green]=============================================================================[/bold green]")
    console.print("[bold green]                    Data Generation Complete!                      [/bold green]")
    console.print("[bold green]=============================================================================[/bold green]\n")


def show_usage_instructions():
    """Show usage instructions."""
    console = Console()

    console.print("\n[bold cyan]How to Use:[/bold cyan]\n")

    usage = """
# Interactive Setup (Recommended for first-time users)
[bright_cyan]synth agent chat[/bright_cyan]

# Quick Mode (Skip setup, use environment variables)
[dim]export ANTHROPIC_API_KEY=your_key[/dim]
[bright_cyan]synth agent chat --skip-setup[/bright_cyan]

# Specify provider and model directly
[bright_cyan]synth agent chat -p openai -m gpt-4o[/bright_cyan]

# Quick single-shot mode
[bright_cyan]synth agent quick --prompt "50 transactions" --output data.csv[/bright_cyan]
    """

    console.print(usage)


def main():
    """Run the wizard demo."""
    console = Console()

    show_complete_flow()
    show_usage_instructions()

    console.print("\n[bold green]This is the most sophisticated Synthetic Data AI Agent![/bold green]\n")
    console.print("[dim]Features:[/dim]")
    features = [
        "Multi-provider LLM support (Claude, OpenAI, Gemini)",
        "Interactive setup wizard for easy configuration",
        "Intelligent natural language understanding",
        "AI-powered clarification of ambiguous requirements",
        "Document upload for reference pattern matching",
        "Multiple output formats (CSV, Excel, PDF, Word)",
    ]

    for feature in features:
        console.print(f"  [dim]-[/dim] {feature}")

    console.print()


if __name__ == "__main__":
    main()
