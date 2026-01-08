"""
CLI Interface for the True AI Agent.

Provides interactive and single-request modes for interacting with the agent.
"""

import asyncio
import sys
from typing import Optional
from datetime import datetime

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.markdown import Markdown
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
    from rich.prompt import Prompt
    from rich.syntax import Syntax
    from rich.text import Text
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    Console = None  # type: ignore

from synth.agent.true_ai_agent import TrueAIAgent
from synth.agent.models.core import Response


class AgentCLI:
    """
    Command-line interface for the AI Agent.

    Features:
    - Interactive chat mode
    - Single request mode
    - Progress display
    - Colored output (with rich)
    """

    def __init__(
        self,
        storage_path: str = ".agent_memory",
        llm_provider: Optional[str] = None,
    ):
        """
        Initialize CLI.

        Args:
            storage_path: Path for persistent memory
            llm_provider: LLM provider to use
        """
        self.storage_path = storage_path
        self.llm_provider = llm_provider
        self.console = Console() if RICH_AVAILABLE else None

        # Initialize agent
        self.agent = TrueAIAgent(
            storage_path=storage_path,
            llm_provider=llm_provider,
        )
        self.agent.initialize()

    def run_interactive(self):
        """Run interactive chat mode."""
        self._print_header()

        if RICH_AVAILABLE:
            self.console.print(Panel(
                "[bold green]True AI Agent[/bold green] - Interactive Mode",
                subtitle="Type 'exit' or 'quit' to exit, 'help' for commands",
                border_style="blue"
            ))
        else:
            print("=" * 60)
            print("True AI Agent - Interactive Mode")
            print("Type 'exit' or 'quit' to exit, 'help' for commands")
            print("=" * 60)

        while True:
            try:
                # Get user input
                user_input = self._get_prompt()

                if not user_input:
                    continue

                # Handle commands
                if user_input.lower() in ['exit', 'quit', 'q']:
                    self._print_goodbye()
                    break

                if user_input.lower() in ['help', 'h', '?']:
                    self._print_help()
                    continue

                if user_input.lower() in ['status', 's']:
                    self._print_status()
                    continue

                if user_input.lower() in ['clear', 'c']:
                    if RICH_AVAILABLE:
                        self.console.clear()
                    else:
                        print("\n" * 50)
                    continue

                # Process request
                response = asyncio.run(self._process_with_display(user_input))
                self._display_response(response)

            except KeyboardInterrupt:
                self._print("\n[yellow]Interrupted. Type 'exit' to quit.[/yellow]")
                continue
            except Exception as e:
                self._print_error(f"Error: {str(e)}")
                continue

    def run_single_request(self, request: str):
        """
        Run a single request and exit.

        Args:
            request: User request string
        """
        self._print_header()

        response = asyncio.run(self._process_with_display(request))
        self._display_response(response)

    async def _process_with_display(self, request: str) -> Response:
        """Process request with progress display."""
        if RICH_AVAILABLE:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console,
                transient=True,
            ) as progress:
                task = progress.add_task("Processing...", total=None)

                response = await self.agent.process_request(request)

                progress.update(task, completed=True)
        else:
            print("Processing...")
            response = await self.agent.process_request(request)

        return response

    def _get_prompt(self) -> str:
        """Get user input prompt."""
        if RICH_AVAILABLE:
            try:
                return Prompt.ask(
                    "\n[bold blue]You[/bold blue]",
                    console=self.console,
                )
            except:
                # Fallback to input()
                return input("\nYou: ")
        else:
            return input("\nYou: ")

    def _display_response(self, response: Response):
        """Display agent response."""
        if not RICH_AVAILABLE:
            self._display_response_plain(response)
            return

        # Display main message
        if response.message:
            self.console.print(Panel(
                response.message,
                title="[bold green]Agent[/bold green]",
                border_style="green" if response.success else "red",
            ))

        # Display metadata
        if response.metadata:
            metadata_table = Table(show_header=False, box=None)
            metadata_table.add_column("Metric", style="cyan")
            metadata_table.add_column("Value", style="yellow")

            for key, value in response.metadata.items():
                if key == "processing_time_seconds":
                    metadata_table.add_row("Processing Time", f"{value:.2f}s")
                elif key == "steps_executed":
                    metadata_table.add_row("Steps Executed", str(value))
                elif key == "tools_used":
                    metadata_table.add_row("Tools Used", ", ".join(value))

            if metadata_table.row_count > 0:
                self.console.print(metadata_table)

        # Display suggestions
        if response.suggestions:
            self.console.print("\n[bold yellow]Suggestions:[/bold yellow]")
            for i, suggestion in enumerate(response.suggestions, 1):
                self.console.print(f"  {i}. [cyan]{suggestion.title}[/cyan]")
                self.console.print(f"     {suggestion.description}")
                if suggestion.benefit:
                    self.console.print(f"     [dim]Benefit: {suggestion.benefit}[/dim]")

        # Display warnings
        if response.warnings:
            self.console.print("\n[bold red]Warnings:[/bold red]")
            for warning in response.warnings:
                severity_emoji = "🔴" if warning.severity.value == "high" else "🟡"
                self.console.print(f"  {severity_emoji} {warning.message}")
                if warning.mitigation:
                    self.console.print(f"     [dim]Mitigation: {warning.mitigation}[/dim]")

        # Display plan if exists
        if response.plan and response.plan.steps:
            self.console.print("\n[bold cyan]Execution Plan:[/bold cyan]")
            for i, step in enumerate(response.plan.steps, 1):
                status_icon = {
                    "pending": "⏳",
                    "in_progress": "▶️",
                    "completed": "✅",
                    "failed": "❌",
                }.get(step.status.value, "❓")

                self.console.print(f"  {i}. {status_icon} {step.action}")
                if step.tool:
                    self.console.print(f"     Tool: {step.tool}")

        # Display data preview if available
        if response.data is not None:
            self.console.print("\n[bold cyan]Data Preview:[/bold cyan]")
            if hasattr(response.data, 'head'):
                # DataFrame
                self.console.print(str(response.data.head()))
                rows, cols = response.data.shape
                self.console.print(f"[dim]{rows} rows × {cols} columns[/dim]")
            elif hasattr(response.data, '__len__'):
                # Other sequence
                preview_len = min(5, len(response.data))
                self.console.print(str(response.data[:preview_len]))
                self.console.print(f"[dim]{len(response.data)} total items[/dim]")
            else:
                self.console.print(str(response.data))

    def _display_response_plain(self, response: Response):
        """Display response in plain text mode."""
        print(f"\n{'='*60}")
        print(f"Agent: {'✓' if response.success else '✗'} {response.message}")
        print(f"{'='*60}")

        if response.suggestions:
            print("\nSuggestions:")
            for i, suggestion in enumerate(response.suggestions, 1):
                print(f"  {i}. {suggestion.title}")
                print(f"     {suggestion.description}")

        if response.warnings:
            print("\nWarnings:")
            for warning in response.warnings:
                print(f"  • {warning.message}")

        if response.data is not None:
            print("\nData Preview:")
            print(str(response.data)[:500])

    def _print_header(self):
        """Print welcome header."""
        if RICH_AVAILABLE:
            self.console.print(Panel(
                "[bold cyan]SYNTH True AI Agent[/bold cyan]\n\n"
                "An autonomous AI agent with:\n"
                "• Multi-step planning\n"
                "• Decision making\n"
                "• Tool use\n"
                "• Self-correction\n"
                "• Proactive behavior\n"
                "• Persistent memory",
                border_style="cyan",
                padding=(1, 2),
            ))
        else:
            print("""
╔────────────────────────────────────────────────────────────────────┘
                    SYNTH True AI Agent

    An autonomous AI agent with:
    • Multi-step planning  • Decision making  • Tool use
    • Self-correction  • Proactive behavior  • Persistent memory
╚────────────────────────────────────────────────────────────────────╝
""")

    def _print_help(self):
        """Print help information."""
        if RICH_AVAILABLE:
            help_text = """
[bold]Commands:[/bold]
  [cyan]help, h, ?[/cyan]     - Show this help
  [cyan]status, s[/cyan]       - Show agent status
  [cyan]clear, c[/cyan]        - Clear screen
  [cyan]exit, quit, q[/cyan]   - Exit the agent

[bold]Examples:[/bold]
  [yellow]Generate 1000 synthetic records[/yellow]
  [yellow]Generate 5000 records and export to output.csv[/yellow]
  [yellow]Analyze the data in data.csv[/yellow]
  [yellow]Validate synthetic data against original[/yellow]
"""
            self.console.print(Markdown(help_text))
        else:
            print("""
Commands:
  help, h, ?     - Show this help
  status, s       - Show agent status
  clear, c        - Clear screen
  exit, quit, q   - Exit the agent

Examples:
  Generate 1000 synthetic records
  Generate 5000 records and export to output.csv
  Analyze the data in data.csv
  Validate synthetic data against original
""")

    def _print_status(self):
        """Print agent status."""
        status = self.agent.get_status()

        if RICH_AVAILABLE:
            table = Table(title="Agent Status", show_header=True)
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="yellow")

            table.add_row("Initialized", str(status["initialized"]))
            table.add_row("Requests Processed", str(status["requests_processed"]))
            table.add_row("Uptime", f"{status['uptime_seconds']:.1f}s")
            table.add_row("Tools Registered", str(status["tools_registered"]))

            memory_stats = status.get("memory_stats", {})
            if memory_stats:
                table.add_row("Memory Stats", str(memory_stats))

            self.console.print(table)
        else:
            print("\nAgent Status:")
            print(f"  Initialized: {status['initialized']}")
            print(f"  Requests Processed: {status['requests_processed']}")
            print(f"  Uptime: {status['uptime_seconds']:.1f}s")
            print(f"  Tools Registered: {status['tools_registered']}")

    def _print_goodbye(self):
        """Print goodbye message."""
        if RICH_AVAILABLE:
            self.console.print(Panel(
                "[bold green]Thank you for using SYNTH True AI Agent![/bold green]\n\n"
                "Your session has been saved.\n"
                f"Memory location: [cyan]{self.storage_path}[/cyan]",
                border_style="green",
            ))
        else:
            print(f"\nThank you for using SYNTH True AI Agent!")
            print(f"Your session has been saved to: {self.storage_path}")

    def _print_error(self, message: str):
        """Print error message."""
        if RICH_AVAILABLE:
            self.console.print(f"[red]Error:[/red] {message}")
        else:
            print(f"Error: {message}")


def main():
    """Main CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="SYNTH True AI Agent - Command Line Interface",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode
  python -m synth.agent.cli

  # Single request
  python -m synth.agent.cli --request "Generate 1000 records"

  # With custom memory path
  python -m synth.agent.cli --storage-path ./my_memory
        """,
    )

    parser.add_argument(
        "--request", "-r",
        help="Single request to process (exits after completion)",
    )
    parser.add_argument(
        "--storage-path", "-m",
        default=".agent_memory",
        help="Path for persistent memory storage (default: .agent_memory)",
    )
    parser.add_argument(
        "--llm-provider", "-l",
        help="LLM provider to use",
    )

    args = parser.parse_args()

    # Create CLI
    cli = AgentCLI(
        storage_path=args.storage_path,
        llm_provider=args.llm_provider,
    )

    # Run appropriate mode
    if args.request:
        cli.run_single_request(args.request)
    else:
        cli.run_interactive()


if __name__ == "__main__":
    main()
