"""
CLI command for inspecting learned patterns.
"""

from typer import Typer, Option
from rich.console import Console
from rich.table import Table
from rich.tree import Tree
from rich.panel import Panel

app = Typer(help="Inspect learned patterns")
console = Console()


@app.command()
def inspect(
    pattern: str = Option(..., "--pattern", "-p", help="Pattern name or file path"),
    detail: str = Option("summary", "--detail", "-d", help="Detail level (summary, full, stats)"),
):
    """
    Inspect a learned pattern and display its properties.

    Examples:
        synth inspect --pattern customer_pattern
        synth inspect --pattern customer_pattern --detail stats
        synth inspect --pattern patterns/customer_pattern.json --detail full
    """
    console.print(f"[cyan]Inspecting pattern: {pattern}[/cyan]\n")

    # TODO: Implement pattern loading and inspection

    # Mock display for now
    if detail == "summary":
        console.print(Panel(f"[bold]Pattern: customer_pattern[/bold]\n\n" f"Type: Tabular\n" f"Source: customers.csv\n" f"Records: 50,000\n" f"Fields: 12\n" f"Learned: 2026-01-05", title="Pattern Summary", border_style="cyan"))

    elif detail == "stats":
        # Show statistics table
        table = Table(title="Field Statistics")
        table.add_column("Field", style="cyan")
        table.add_column("Type", style="yellow")
        table.add_column("Distribution", style="green")
        table.add_column("Stats", style="dim")

        table.add_row("customer_id", "string", "Pattern", "CUST-[0-9]{8}")
        table.add_row("age", "integer", "Normal", "μ=42.3, σ=12.7")
        table.add_row("income", "float", "Log-Normal", "μ=11.2, σ=0.6")
        table.add_row("segment", "categorical", "Multinomial", "Regular: 70%, Premium: 20%, VIP: 10%")
        table.add_row("email", "string", "Pattern", "username@domain.tld")

        console.print(table)

        console.print(f"\n[bold]Correlations:[/bold]")
        corr_table = Table(show_header=True, header_style="bold magenta")
        corr_table.add_column("Pair", style="cyan")
        corr_table.add_column("Correlation", justify="right")

        corr_table.add_row("age ↔ income", "0.34")
        corr_table.add_row("age ↔ account_age", "0.67")
        corr_table.add_row("segment ↔ total_spent", "0.78")

        console.print(corr_table)

    elif detail == "full":
        tree = Tree("[bold cyan]customer_pattern[/bold cyan]")
        tree.add("[dim]Source: customers.csv[/dim]")
        tree.add("[dim]Records: 50,000[/dim]")

        fields = tree.add("[bold]Fields[/bold]")
        fields.add("customer_id [dim](string, unique)[/dim]")
        fields.add("name [dim](string)[/dim]")
        fields.add("age [dim](integer, ≥18)[/dim]")
        fields.add("email [dim](string)[/dim]")
        fields.add("segment [dim](categorical)[/dim]")
        fields.add("income [dim](float)[/dim]")

        constraints = tree.add("[bold]Constraints[/bold]")
        constraints.add("age >= 18")
        constraints.add("email matches regex")
        constraints.add("customer_id unique")

        console.print(tree)


@app.command()
def list(
    pattern_dir: str = Option("patterns", "--dir", "-d", help="Pattern directory"),
):
    """
    List all available patterns.

    Examples:
        synth inspect-list
        synth inspect-list --dir /path/to/patterns
    """
    console.print(f"[cyan]Available patterns in {pattern_dir}:[/cyan]\n")
    # TODO: Implement pattern listing
    console.print("[dim](No patterns found)[/dim]")


if __name__ == "__main__":
    app()
