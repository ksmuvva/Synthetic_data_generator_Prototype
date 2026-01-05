"""
CLI command for the AI Agent mode.

Completely LLM-driven AI agent with interactive setup wizard.
Supports: Anthropic Claude, OpenAI GPT, Google Gemini.
"""

from pathlib import Path
from typer import Typer, Option

try:
    from rich.console import Console
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

from synth.agent.llm.session import TrueAIAgent
from synth.agent.llm import get_llm_provider
from synth.agent.llm.wizard import run_setup_wizard
from synth.core.errors import SynthError

app = Typer(
    help="AI Agent mode - Generate synthetic data through LLM-powered conversation"
)


class AgentError(SynthError):
    """Error in agent interaction."""
    pass


@app.command()
def chat(
    skip_setup: bool = Option(False, "--skip-setup", help="Skip interactive setup wizard"),
    provider: str = Option(None, "--provider", "-p", help="LLM provider (claude, openai, gemini)"),
    model: str = Option(None, "--model", "-m", help="Model to use"),
    api_key: str = Option(None, "--api-key", help="API key (overrides environment)"),
    show_thinking: bool = Option(True, "--show-thinking/--hide-thinking", help="Show LLM thinking process"),
) -> None:
    """
    Start LLM-powered AI agent with interactive setup.

    **First Time Setup:**
    The agent will guide you through:
    1. Selecting your AI provider (Claude, OpenAI, Gemini)
    2. Choosing a model
    3. Entering your API key
    4. Describing your data requirements
    5. Optionally uploading reference documents

    **Skip Setup:**
    Use --skip-setup to use environment variables and command-line options:
    export ANTHROPIC_API_KEY=your_key
    synth agent chat --skip-setup

    **Examples:**
        synth agent chat                      # Full interactive setup
        synth agent chat --skip-setup         # Use env variables
        synth agent chat -p openai -m gpt-4o  # Specific configuration
    """
    if not RICH_AVAILABLE:
        raise AgentError(
            "rich is required for the AI agent. "
            "Install it with: pip install rich"
        )

    console = Console()

    try:
        # Run setup wizard unless skipped
        if not skip_setup:
            provider, model, api_key, requirements, uploaded_files = run_setup_wizard(console)

            # Create LLM provider with user's configuration
            llm = get_llm_provider(
                provider=provider,
                api_key=api_key,
                model=model,
                temperature=0.7,
            )

            # Enable thinking for Claude by default
            if provider in ("claude", "anthropic"):
                llm.enable_thinking = show_thinking

            # Create AI agent
            agent = TrueAIAgent(
                llm=llm,
                console=console,
                show_thinking=show_thinking
            )

            # Set initial requirements if provided
            if requirements:
                agent.state.add_message("user", requirements)

            # Load uploaded files if any
            for file_path in uploaded_files:
                if hasattr(agent, 'load_pattern'):
                    agent.load_pattern(str(file_path))

            # Start conversation
            console.print("\n[dim]Starting AI Agent...[/dim]\n")
            agent.run()

        else:
            # Skip setup - use command line options
            if not provider:
                # Try to detect from environment
                import os
                if os.getenv("ANTHROPIC_API_KEY"):
                    provider = "claude"
                elif os.getenv("OPENAI_API_KEY"):
                    provider = "openai"
                elif os.getenv("GOOGLE_API_KEY"):
                    provider = "gemini"
                else:
                    console.print("[red]Error: No provider specified and no API keys found in environment.[/red]")
                    console.print("\n[dim]Run without --skip-setup for interactive setup, or set an API key:[/dim]")
                    console.print("  export ANTHROPIC_API_KEY=your_key")
                    console.print("  export OPENAI_API_KEY=your_key")
                    console.print("  export GOOGLE_API_KEY=your_key")
                    raise SystemExit(1)

            # Build kwargs
            provider_kwargs = {"temperature": 0.7}
            if model:
                provider_kwargs["model"] = model
            if api_key:
                provider_kwargs["api_key"] = api_key

            # Enable thinking for Claude by default
            if provider.lower() in ("claude", "anthropic"):
                provider_kwargs["enable_thinking"] = show_thinking

            # Create LLM provider
            try:
                llm = get_llm_provider(provider=provider, **provider_kwargs)
            except ValueError as e:
                console.print(f"[red]Error: {e}[/red]")
                console.print("\n[dim]Supported providers: claude, openai, gemini[/dim]")
                raise SystemExit(1)

            # Create AI agent
            config_name = PROVIDER_NAMES.get(provider, provider)
            console.print(f"[cyan]Starting AI Agent with {config_name}...[/cyan]\n")

            agent = TrueAIAgent(
                llm=llm,
                console=console,
                show_thinking=show_thinking
            )

            # Start conversation
            agent.run()

    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user.[/yellow]")
        raise SystemExit(0)

    except Exception as e:
        console.print(f"\n[red]Error: {str(e)}[/red]")
        raise SystemExit(1)


PROVIDER_NAMES = {
    "claude": "Claude",
    "anthropic": "Claude",
    "openai": "OpenAI GPT",
    "gpt": "OpenAI GPT",
    "gemini": "Google Gemini",
    "google": "Google Gemini",
}


@app.command()
def quick(
    prompt: str = Option(..., "--prompt", "-p", help="Single prompt to process"),
    count: int = Option(100, "--count", "-n", help="Number of records to generate"),
    output: str = Option(..., "--output", "-o", help="Output file path"),
    format: str = Option("csv", "--format", "-f", help="Output format (csv, excel, pdf, word)"),
    provider: str = Option("claude", "--provider", help="LLM provider (claude, openai, gemini)"),
) -> None:
    """
    Quick single-shot mode (non-interactive).

    **Example:**
        synth agent quick --prompt "50 transactions" --output data.csv
        synth agent quick -p "100 customers" -o customers.pdf -f pdf --provider openai
    """
    if not RICH_AVAILABLE:
        raise AgentError(
            "rich is required for the agent. "
            "Install it with: pip install rich"
        )

    console = Console()

    try:
        # Create LLM provider
        try:
            llm = get_llm_provider(provider=provider)
        except ValueError as e:
            console.print(f"[red]Error: {e}[/red]")
            raise SystemExit(1)

        # Create agent
        agent = TrueAIAgent(llm=llm, console=console, show_thinking=False)

        # Parse the prompt
        intent = agent.parser.parse(prompt)

        # Set basic info
        if intent.record_count:
            agent.state.record_count = intent.record_count
        else:
            agent.state.record_count = count

        if intent.entity_type:
            agent.state.entity_type = intent.entity_type
        else:
            console.print("[yellow]Could not determine entity type. Using default.[/yellow]")
            agent.state.entity_type = "data"

        if intent.output_format != "csv":
            agent.state.output_format = intent.output_format
        else:
            agent.state.output_format = format

        # Check if we have enough info
        if not agent.state.is_complete():
            console.print("[yellow]Insufficient information for quick mode.[/yellow]")
            console.print("Try interactive mode: synth agent chat")
            raise SystemExit(1)

        # Generate data
        success, message, output_path = agent.generate_data(Path(output))

        if success:
            console.print(f"[green]OK] {message}[/green]")
            console.print(f"[green]OK] Saved to: {output_path}[/green]")
        else:
            console.print(f"[red]Error: {message}[/red]")
            raise SystemExit(1)

    except Exception as e:
        console.print(f"\n[red]Error: {str(e)}[/red]")
        raise SystemExit(1)


if __name__ == "__main__":
    app()
