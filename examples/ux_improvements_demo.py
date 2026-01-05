#!/usr/bin/env python3
"""
UX Improvements Demo - Showcasing the enhanced CLI experience.

This demo demonstrates all 6 UX improvements:
1. Loading spinners during LLM API calls
2. Progress counter during generation (Generating X/Y...)
3. Time estimates (~30 seconds remaining)
4. "Recommended" badge for default model
5. Keyboard shortcuts hints (Ctrl+C to cancel)
6. "Edit" option to go back and change selections
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import (
    Progress, SpinnerColumn, TextColumn, BarColumn,
    TimeRemainingColumn, TaskProgressColumn
)
from rich.status import Status
from rich.rule import Rule


console = Console()


def show_improvements_summary():
    """Show the UX improvements summary."""
    console.print("\n[bold cyan]============================================================================")
    console.print("[bold cyan]         UX IMPROVEMENTS - BEFORE & AFTER                        ")
    console.print("[bold cyan]============================================================================\n")

    improvements_table = Table(show_header=True, box=None, padding=(0, 1))
    improvements_table.add_column("Improvement", style="bold cyan", width=35)
    improvements_table.add_column("Before", style="red", width=25)
    improvements_table.add_column("After", style="green", width=30)

    improvements_table.add_row(
        "Loading Indicators",
        "[red]X[/red] No spinner during API calls",
        "[green]OK[/green] Dots spinner while thinking"
    )
    improvements_table.add_row(
        "Progress Tracking",
        "[red]X[/red] No progress updates",
        "[green]OK[/green] Generating X/Y with progress bar"
    )
    improvements_table.add_row(
        "Time Estimates",
        "[red]X[/red] No ETA shown",
        "[green]OK[/green] '~50 seconds remaining'"
    )
    improvements_table.add_row(
        "Recommended Model",
        "[red]X[/red] No guidance for beginners",
        "[green]OK[/green] '[recommended]' badge"
    )
    improvements_table.add_row(
        "Keyboard Shortcuts",
        "[red]X[/red] No shortcut hints",
        "[green]OK[/green] 'Ctrl+C to cancel' tips"
    )
    improvements_table.add_row(
        "Edit Option",
        "[red]X[/red] Can't go back",
        "[green]OK[/green] 'or 'e' to edit' prompt"
    )

    console.print(improvements_table)
    console.print()


def show_spinner_demo():
    """Demo loading spinner during API calls."""
    console.print("\n" + "="*78)
    console.print("[bold cyan]1. Loading Spinner During API Calls[/bold cyan]\n")

    console.print("[dim]BEFORE: No feedback, looks like app is frozen[/dim]\n")

    console.print("[bold green]AFTER: Animated spinner shows activity[/bold green]\n")

    # Simulate API call with spinner
    with Status("[bold cyan]Thinking...[/bold cyan]", spinner="dots", console=console):
        time.sleep(2)

    console.print("[green]Done! API response received.[/green]\n")


def show_progress_demo():
    """Demo progress tracking during generation."""
    console.print("\n" + "="*78)
    console.print("[bold cyan]2. Progress Counter During Generation[/bold cyan]\n")

    console.print("[dim]BEFORE: 'Generating 100 records...' (no updates)[/dim]\n")

    console.print("[bold green]AFTER: Real-time progress with count and percentage[/bold green]\n")

    # Show time estimate
    count = 100
    estimated_seconds = max(5, count * 0.5)
    console.print(f"[dim]Estimated time: ~{estimated_seconds:.0f} seconds[/dim]\n")

    console.print("[cyan]Building schema...[/cyan]")
    time.sleep(0.5)
    console.print("[cyan]Creating generation pattern...[/cyan]")
    time.sleep(0.5)
    console.print(f"[cyan]Generating {count} records...[/cyan]\n")

    # Simulate progress
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TextColumn("({task.completed}/{task.total})"),
        TimeRemainingColumn(),
        console=console,
    ) as progress:

        task = progress.add_task(
            "[cyan]Generating records[/cyan]",
            total=count
        )

        # Simulate batch generation
        batch_size = 10
        for i in range(0, count, batch_size):
            time.sleep(0.1)  # Simulate generation time
            current_batch = min(batch_size, count - i)
            progress.update(task, completed=min(i + current_batch, count))

    console.print()


def show_recommended_badge_demo():
    """Demo recommended badge for models."""
    console.print("\n" + "="*78)
    console.print("[bold cyan]3. 'Recommended' Badge for Default Model[/bold cyan]\n")

    console.print("[dim]BEFORE: All models look the same, unclear which to pick[/dim]\n")

    console.print("[bold green]AFTER: '[recommended]' badge guides beginners[/bold green]\n")

    table = Table(title="Available Claude Models", show_header=True, header_style="bold magenta")
    table.add_column("Option", style="cyan", width=8)
    table.add_column("Model", style="green")
    table.add_column("Description", style="dim")

    table.add_row("1", "Claude 3.5 Sonnet", "Best balance, intelligent reasoning [yellow][[recommended]][/yellow]")
    table.add_row("2", "Claude 3.5 Haiku", "Fastest, good for simple tasks")
    table.add_row("3", "Claude 3 Opus", "Most capable, highest quality")

    console.print(table)
    console.print()


def show_keyboard_shortcuts_demo():
    """Demo keyboard shortcuts hints."""
    console.print("\n" + "="*78)
    console.print("[bold cyan]4. Keyboard Shortcuts Hints[/bold cyan]\n")

    console.print("[dim]BEFORE: Users don't know about shortcuts[/dim]\n")

    console.print("[bold green]AFTER: Tips shown below each selection[/bold green]\n")

    console.print("[bold cyan]Step 1: Select Your AI Provider[/bold cyan]\n")

    table = Table(title="Available LLM Providers", show_header=True, header_style="bold magenta")
    table.add_column("Option", style="cyan", width=8)
    table.add_column("Provider", style="green")
    table.add_column("Features", style="dim")

    table.add_row("1", "Claude (Anthropic)", "Extended thinking, 200K context")
    table.add_row("2", "GPT (OpenAI)", "GPT-4o, fast response")
    table.add_row("3", "Gemini (Google)", "1M context window")

    console.print(table)

    # Show keyboard shortcuts hint
    console.print("\n[dim]Tips: Press Enter for default (1), Ctrl+C to cancel[/dim]\n")

    console.print("[cyan]Choose your AI provider [1/2/3]: [/cyan][dim]1[/dim]")
    console.print("[green]Selected: Claude (Anthropic)[/green]")

    console.print("\n[cyan]Is this correct? (or 'e' to edit) [Y/n]: [/cyan][dim]y[/dim]\n")


def show_edit_option_demo():
    """Demo edit option to go back."""
    console.print("\n" + "="*78)
    console.print("[bold cyan]5. 'Edit' Option to Go Back[/bold cyan]\n")

    console.print("[dim]BEFORE: If wrong selection, must restart entire wizard[/dim]\n")

    console.print("[bold green]AFTER: 'or 'e' to edit' prompt at each confirmation[/bold green]\n")

    console.print("[cyan]Choose your model [1/2/3]: [/cyan][dim]1[/dim]")
    console.print("[green]Selected: Claude 3.5 Sonnet[/green]")
    console.print("\n[cyan]Is this correct? (or 'e' to edit) [Y/n]: [/cyan][yellow]n[/yellow]")
    console.print("\n[dim]User chooses 'n', wizard loops back for retry[/dim]")
    console.print("[cyan]Choose your model [1/2/3]: [/cyan][dim]2[/dim]")
    console.print("[green]Selected: Claude 3.5 Haiku[/green]")
    console.print("\n[cyan]Is this correct? (or 'e' to edit) [Y/n]: [/cyan][green]y[/green]")
    console.print("\n[green]Proceeding to next step...[/green]\n")


def show_complete_flow():
    """Show the complete improved flow."""
    console.print("\n" + "="*78)
    console.print("[bold cyan]         COMPLETE IMPROVED USER FLOW                              ")
    console.print("="*78 + "\n")

    console.print("[bold cyan]$[/bold cyan] synth agent chat\n")

    # Welcome
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

    # Provider selection with all improvements
    console.print("\n" + "="*78)
    console.print("[bold]Starting Setup Wizard...[/bold]\n")

    console.print("[bold cyan]Step 1: Select Your AI Provider[/bold cyan]\n")

    provider_table = Table(title="Available LLM Providers", show_header=True)
    provider_table.add_column("Option", style="cyan", width=8)
    provider_table.add_column("Provider", style="green", width=20)
    provider_table.add_column("Features", style="dim")

    provider_table.add_row("1", "Claude (Anthropic)", "Extended thinking, 200K context, best reasoning")
    provider_table.add_row("2", "GPT (OpenAI)", "GPT-4o, fast response, widely adopted")
    provider_table.add_row("3", "Gemini (Google)", "1M context window, multimodal")

    console.print(provider_table)
    console.print("\n[dim]Tips: Press Enter for default (1), Ctrl+C to cancel[/dim]")
    console.print("\n[cyan]Choose your AI provider [1/2/3]: [/cyan][dim]1[/dim]")
    console.print("[green]Selected: Claude (Anthropic)[/green]")
    console.print("\n[cyan]Is this correct? (or 'e' to edit) [Y/n]: [/cyan][dim]y[/dim]\n")

    # Model selection with recommended badge
    console.print("[bold cyan]Step 2: Select Your Model[/bold cyan]\n")

    model_table = Table(title="Available Claude Models", show_header=True)
    model_table.add_column("Option", style="cyan", width=8)
    model_table.add_column("Model", style="green", width=20)
    model_table.add_column("Description", style="dim")

    model_table.add_row("1", "Claude 3.5 Sonnet", "Best balance, intelligent reasoning [yellow][[recommended]][/yellow]")
    model_table.add_row("2", "Claude 3.5 Haiku", "Fastest, good for simple tasks")
    model_table.add_row("3", "Claude 3 Opus", "Most capable, highest quality")

    console.print(model_table)
    console.print("\n[dim]Tips: Press Enter for default (1), Ctrl+C to cancel[/dim]")
    console.print("\n[cyan]Choose your model [1/2/3]: [/cyan][dim]1[/dim]")
    console.print("[green]Selected: Claude 3.5 Sonnet[/green]")
    console.print("\n[cyan]Is this correct? (or 'e' to edit) [Y/n]: [/cyan][dim]y[/dim]\n")

    # Requirements
    console.print("[bold cyan]Step 4: Describe Your Data Needs[/bold cyan]\n")
    console.print("[cyan]What data do you want to generate?[/cyan]")
    console.print("[green]Create 100 financial transactions with amount between $10 and $5000[/green]\n")

    # AI conversation with spinner
    console.print("\n" + "="*78)
    console.print("[bold]AI Agent Starting...[/bold]\n")

    # Show spinner
    with Status("[bold cyan]Thinking...[/bold cyan]", spinner="dots", console=console):
        time.sleep(1)

    console.print("[cyan]AI:[/cyan] I understand you want 100 financial transactions. Let me clarify:\n")
    console.print("  [cyan]1.[/cyan] What currency should be used?")

    console.print("\n[dim]>[/dim] [green]USD[/green]")

    # Show spinner again
    with Status("[bold cyan]Thinking...[/bold cyan]", spinner="dots", console=console):
        time.sleep(1)

    console.print("\n[cyan]AI:[/cyan] Got it. USD.")
    console.print("  [cyan]2.[/cyan] What date range should the transactions cover?")

    console.print("\n[dim]>[/dim] [green]2024-01-01 to 2024-12-31[/green]")

    # Show spinner again
    with Status("[bold cyan]Analyzing requirements...[/bold cyan]", spinner="dots", console=console):
        time.sleep(1)

    console.print("\n[cyan]AI:[/cyan] Perfect. Generating 100 financial transactions...\n")

    # Show generation with progress
    console.print("[dim]Estimated time: ~50 seconds[/dim]\n")

    console.print("[cyan]Building schema...[/cyan]")
    console.print("[cyan]Creating generation pattern...[/cyan]")
    console.print(f"[cyan]Generating 100 records...[/cyan]\n")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TextColumn("({task.completed}/{task.total})"),
        TimeRemainingColumn(),
        console=console,
        transient=True,  # Remove progress bar when complete
    ) as progress:

        task = progress.add_task(
            "[cyan]Generating records[/cyan]",
            total=100
        )

        batch_size = 10
        for i in range(0, 100, batch_size):
            time.sleep(0.05)
            current_batch = min(batch_size, 100 - i)
            progress.update(task, completed=min(i + current_batch, 100))

    console.print("[green][bold]Generated 100 records[/bold][/green]")
    console.print("[green][bold]Saved to: transactions_20250105.csv[/bold][/green]\n")

    console.print("\n" + "="*78)
    console.print("[bold cyan]                    ALL UX IMPROVEMENTS APPLIED!                       ")
    console.print("="*78 + "\n")


def show_scorecard():
    """Show updated UX scorecard."""
    console.print("\n[bold cyan]============================================================================")
    console.print("[bold cyan]                    UPDATED UI/UX SCORECARD                             ")
    console.print("[bold cyan]============================================================================\n")

    score_table = Table(show_header=True, box=None, padding=(0, 1))
    score_table.add_column("Aspect", style="bold cyan", width=25)
    score_table.add_column("Score", justify="center", width=10)
    score_table.add_column("Notes", style="dim")

    score_table.add_row("Visual Design", "[green]8/10[/green]", "Clean, modern, good use of colors")
    score_table.add_row("Navigation", "[green]9/10[/green]", "Clear flow, edit option for going back")
    score_table.add_row("Feedback", "[green]9/10[/green]", "Spinners, progress bar, time estimates")
    score_table.add_row("Error Handling", "[green]7/10[/green]", "Clear messages, could add recovery")
    score_table.add_row("Accessibility", "[yellow]7/10[/yellow]", "Good contrast, keyboard shortcuts shown")
    score_table.add_row("Documentation", "[green]8/10[/green]", "Helpful examples, recommended badges")
    score_table.add_row("", "", "")
    score_table.add_row("[bold]OVERALL[/bold]", "[green]8.0/10[/green]", "[green]Significant improvements! Ready for users[/green]")

    console.print(score_table)
    console.print()


def main():
    """Run the complete UX improvements demo."""
    console = Console()

    show_improvements_summary()
    show_spinner_demo()
    show_progress_demo()
    show_recommended_badge_demo()
    show_keyboard_shortcuts_demo()
    show_edit_option_demo()
    show_complete_flow()
    show_scorecard()


if __name__ == "__main__":
    main()
