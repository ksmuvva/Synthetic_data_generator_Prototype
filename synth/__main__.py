"""
Main entry point for the synth CLI.

Run `python -m synth` or `synth` command.
"""

from typer import Typer
from rich.console import Console
from rich import print as rprint

from synth import __version__

# Create the CLI app
app = Typer(
    name="synth",
    help="Synthetic Data Generator AI Agent - Generate high-quality synthetic data",
    no_args_is_help=True,
    add_completion=False,
)

console = Console()


@app.command()
def version():
    """Show the version information."""
    rprint(f"[bold cyan]synth[/bold cyan] version [yellow]{__version__}[/yellow]")
    rprint("Synthetic Data Generator AI Agent")


@app.callback()
def main(
    verbose: bool = False,
    quiet: bool = False,
    config: str = None,
):
    """
    Synthetic Data Generator AI Agent

    Generate high-quality synthetic data through intelligent pattern learning
    and deterministic validation.
    """
    if verbose:
        console.log("Verbose mode enabled")
    if quiet:
        console.quiet = True
    if config:
        console.log(f"Using config: {config}")


# Import subcommands
from synth.cli import init, learn, generate, validate, inspect, export

# Register subcommands
app.add_typer(init.app, name="init")
app.add_typer(learn.app, name="learn")
app.add_typer(generate.app, name="generate")
app.add_typer(validate.app, name="validate")
app.add_typer(inspect.app, name="inspect")
app.add_typer(export.app, name="export")


# Default command when no subcommand is given
@app.command()
def help_command():
    """Show help information."""
    console.print("[bold cyan]Synth[/bold cyan] - Synthetic Data Generator AI Agent\n")
    console.print("[bold]Common commands:[/bold]")
    console.print("  synth init [name]       Initialize a new project")
    console.print("  synth learn             Extract patterns from data")
    console.print("  synth generate          Generate synthetic data")
    console.print("  synth validate          Validate synthetic data quality")
    console.print("  synth inspect           Inspect learned patterns")
    console.print("\n[bold]Getting help:[/bold]")
    console.print("  synth --help            Show this message")
    console.print("  synth [command] --help  Show help for a command")
    console.print("  synth examples          Show example workflows")


if __name__ == "__main__":
    app()
