#!/usr/bin/env python3
"""
Live CLI Demo - Show the actual CLI interface as users will see it.

Windows-compatible version.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.rule import Rule
from rich.syntax import Syntax


console = Console()


def show_live_cli_demo():
    """Show the CLI as users will experience it."""

    console.print("\n[bold cyan]============================================================================")
    console.print("[bold cyan]         SYNTHETIC DATA AI AGENT - LIVE CLI DEMO                   ")
    console.print("[bold cyan]============================================================================\n")

    # Step 1: Running the command
    console.print("[dim]$ synth agent chat[/dim]\n")

    # Step 2: Welcome Screen
    welcome_panel = Panel(
        "[bold cyan]AI Agent[/bold cyan]\n\n"
        "[dim]Powered by Claude (Anthropic) with intelligent reasoning[/dim]\n\n"
        "[dim]I'll help you create synthetic data through natural conversation.[/dim]\n\n"
        "[dim]Type your request naturally, or 'help' for examples.[/dim]\n"
        "[dim]Type 'exit' to quit.[/dim]",
        border_style="bright_cyan",
        padding=(1, 2)
    )
    console.print(welcome_panel)

    # Step 3: Setup Wizard
    console.print(Rule(style="bright_cyan"))
    console.print("[bold]Starting Setup Wizard...[/bold]\n")

    # Provider Selection
    console.print("[bold cyan]Step 1: Select Your AI Provider[/bold cyan]\n")

    provider_table = Table(title="Available LLM Providers", show_header=True)
    provider_table.add_column("Option", style="cyan", width=8)
    provider_table.add_column("Provider", style="green", width=20)
    provider_table.add_column("Features", style="dim")

    provider_table.add_row("1", "Claude (Anthropic)", "Extended thinking, 200K context")
    provider_table.add_row("2", "GPT (OpenAI)", "GPT-4o, fast response")
    provider_table.add_row("3", "Gemini (Google)", "1M context window, multimodal")

    console.print(provider_table)
    console.print("\n[dim]Choose your AI provider [1/2/3]: 1[/dim]")
    console.print("[green][bold]Selected: Claude (Anthropic)[/bold][/green]\n")

    # Model Selection
    console.print("[bold cyan]Step 2: Select Your Model[/bold cyan]\n")

    model_table = Table(title="Available Claude Models", show_header=True)
    model_table.add_column("Option", style="cyan", width=8)
    model_table.add_column("Model", style="green", width=20)
    model_table.add_column("Description", style="dim")

    model_table.add_row("1", "Claude 3.5 Sonnet", "Best balance, intelligent reasoning")
    model_table.add_row("2", "Claude 3.5 Haiku", "Fastest, cost-effective")
    model_table.add_row("3", "Claude 3 Opus", "Most capable, highest quality")

    console.print(model_table)
    console.print("\n[dim]Choose your model [1/2/3]: 1[/dim]")
    console.print("[green][bold]Selected: Claude 3.5 Sonnet[/bold][/green]\n")

    # API Key
    console.print("[bold cyan]Step 3: Enter API Key[/bold cyan]\n")
    console.print("[dim]Get your API key from: https://console.anthropic.com/[/dim]\n")
    console.print("[cyan]Enter your API key: [/cyan][dim]sk-ant-...[/dim]")
    console.print("[green][bold]API key accepted![/bold][/green]\n")

    # Requirements
    console.print("[bold cyan]Step 4: Describe Your Data Needs[/bold cyan]\n")
    console.print("[dim]Example prompts:[/dim]")
    console.print("  [dim]1.[/dim] Create 50 financial transactions")
    console.print("  [dim]2.[/dim] Generate 1000 customer records")
    console.print("  [dim]3.[/dim] I need user profiles with age and location\n")
    console.print("[cyan]What data do you want to generate?[/cyan]")
    console.print("[green]Create 100 financial transactions with amount between $10 and $5000[/green]\n")

    # Document Upload
    console.print("[bold cyan]Step 5: Upload Reference Documents?[/bold cyan]\n")
    console.print("[cyan]Upload documents? [y/n]: [/cyan][dim]n[/dim]")

    # Summary
    console.print(Rule(style="bright_cyan"))
    console.print("[bold cyan]Configuration Summary[/bold cyan]\n")
    console.print("[cyan]Provider:[/cyan] Claude (Anthropic)")
    console.print("[cyan]Model:[/cyan] Claude 3.5 Sonnet")
    console.print("[cyan]API Key:[/cyan] " + "*"*20)
    console.print("\n[cyan]Requirements:[/cyan]")
    console.print("  Create 100 financial transactions with amount between $10 and $5000")
    console.print("\n[cyan]Uploaded Files:[/cyan] None")
    console.print("\n[green][bold]Setup complete![/bold][/green]\n")

    # AI Conversation
    console.print(Rule(style="bright_cyan"))
    console.print("[bold]AI Agent Starting...[/bold]\n")

    console.print("[cyan]AI:[/cyan] I understand you want 100 financial transactions. Let me clarify:\n")
    console.print("  [cyan]1.[/cyan] What currency should be used?")
    console.print("\n[dim]>[/dim] [green]USD[/green]")
    console.print("\n[cyan]AI:[/cyan] Got it. USD.")
    console.print("  [cyan]2.[/cyan] What date range should the transactions cover?")
    console.print("\n[dim]>[/dim] [green]2024-01-01 to 2024-12-31[/green]")
    console.print("\n[cyan]AI:[/cyan] Perfect. Generating 100 financial transactions...\n")
    console.print("[green][bold]Generated 100 records[/bold][/green]")
    console.print("[green][bold]Saved to: transactions_20250105.csv[/bold][/green]\n")

    # Usage options
    console.print(Rule(style="bright_cyan"))
    console.print("[bold cyan]Usage Options[/bold cyan]\n")

    usage_code = """
# Interactive Setup (First-time users)
$ synth agent chat

# Quick Mode (With API key in environment)
$ export ANTHROPIC_API_KEY=sk-ant-...
$ synth agent chat --skip-setup

# Specify Provider
$ synth agent chat -p openai
$ synth agent chat -p gemini

# Quick Single-shot
$ synth agent quick --prompt "50 transactions" --output data.csv
    """

    syntax = Syntax(usage_code.strip(), "bash", theme="monokai")
    console.print(syntax)

    console.print("\n[bold cyan]============================================================================")
    console.print("[bold green]                         READY TO USE!                                 ")
    console.print("[bold cyan]============================================================================\n")


def show_ui_scorecard():
    """Show a UI/UX scorecard."""
    console.print("\n[bold cyan]============================================================================")
    console.print("[bold cyan]                    UI/UX SCORECARD                                  ")
    console.print("[bold cyan]============================================================================\n")

    score_table = Table(show_header=True, box=None, padding=(0, 1))
    score_table.add_column("Aspect", style="bold cyan", width=25)
    score_table.add_column("Score", justify="center", width=10)
    score_table.add_column("Notes", style="dim")

    score_table.add_row("Visual Design", "[green]8/10[/green]", "Clean, modern, good use of colors")
    score_table.add_row("Navigation", "[green]8/10[/green]", "Clear step-by-step flow")
    score_table.add_row("Feedback", "[yellow]6/10[/yellow]", "Missing loading spinners/progress")
    score_table.add_row("Error Handling", "[green]7/10[/green]", "Clear messages, could add recovery")
    score_table.add_row("Accessibility", "[yellow]6/10[/yellow]", "Good contrast, no high-contrast mode")
    score_table.add_row("Documentation", "[green]7/10[/green]", "Helpful examples inline")
    score_table.add_row("", "", "")
    score_table.add_row("[bold]OVERALL[/bold]", "[green]7.5/10[/green]", "Solid foundation, good polish needed")

    console.print(score_table)

    console.print("\n[bold yellow]Quick Wins to Improve:[/bold yellow]\n")
    quick_wins = [
        "[green]+[/green] Add loading spinner during API calls",
        "[green]+[/green] Add 'Recommended' badge to default model",
        "[green]+[/green] Show 'Generating X/Y records...' progress",
        "[green]+[/green] Add keyboard shortcuts (q=quit, h=help)",
        "[green]+[/green] Add estimated time before generation",
    ]

    for win in quick_wins:
        console.print(f"  {win}")


if __name__ == "__main__":
    show_live_cli_demo()
    show_ui_scorecard()
