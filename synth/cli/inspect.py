"""
CLI command for inspecting learned patterns.
"""

from pathlib import Path
from typer import Typer, Option
from rich.console import Console
from rich.table import Table
from rich.tree import Tree
from rich.panel import Panel
from rich.json import JSON

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

    # Import PatternStorage
    from synth.patterns.storage import PatternStorage

    try:
        # Initialize storage
        storage = PatternStorage()

        # Load pattern
        loaded_pattern = storage.load_pattern(pattern)

        # Display based on detail level
        if detail == "summary":
            _display_summary(loaded_pattern, console)
        elif detail == "stats":
            _display_stats(loaded_pattern, console)
        elif detail == "full":
            _display_full(loaded_pattern, console)

    except Exception as e:
        console.print(f"[red]Error loading pattern: {e}[/red]")


def _display_summary(pattern, console: Console):
    """Display pattern summary."""
    console.print(Panel(
        f"[bold]Pattern: {pattern.pattern_id}[/bold]\n\n"
        f"Source: {', '.join(pattern.source_files) if pattern.source_files else 'N/A'}\n"
        f"Records: {pattern.row_count:,}\n"
        f"Fields: {len(pattern.schema.get('fields', [])) if pattern.schema else 0}\n"
        f"Learned: {pattern.learned_at[:10]}\n"
        f"Version: {pattern.version}",
        title="Pattern Summary",
        border_style="cyan"
    ))


def _display_stats(pattern, console: Console):
    """Display pattern statistics."""
    if not pattern.schema:
        console.print("[yellow]No schema information available[/yellow]")
        return

    # Show field statistics table
    table = Table(title="Field Statistics")
    table.add_column("Field", style="cyan")
    table.add_column("Type", style="yellow")
    table.add_column("Null %", style="dim")
    table.add_column("Unique", style="green")
    table.add_column("Stats", style="magenta")

    for field in pattern.schema.get("fields", []):
        name = field.get("name", "N/A")
        field_type = field.get("type", "unknown")
        null_pct = field.get("null_percentage", 0)
        unique_count = field.get("unique_count", "N/A")

        # Build stats string based on type
        if field_type in ["integer", "float"]:
            stats = f"μ={field.get('mean', 'N/A'):.2f}, σ={field.get('std', 'N/A'):.2f}"
            stats += f"\nRange: [{field.get('min_value', 'N/A'):.2f}, {field.get('max_value', 'N/A'):.2f}]"
        elif field_type == "string":
            min_len = field.get("min_length", "N/A")
            max_len = field.get("max_length", "N/A")
            avg_len = field.get("avg_length", "N/A")
            stats = f"Length: [{min_len}, {max_len}], avg: {avg_len:.1f}"
        else:
            stats = f"Mode: {field.get('mode', 'N/A')}"

        table.add_row(name, field_type, f"{null_pct:.1f}%", str(unique_count), stats)

    console.print(table)

    # Show quality metrics if available
    if pattern.quality_metrics:
        console.print(f"\n[bold]Quality Metrics:[/bold]")
        metrics_table = Table(show_header=False)
        metrics_table.add_column("Metric", style="cyan")
        metrics_table.add_column("Value", justify="right")

        for metric_name, value in pattern.quality_metrics.items():
            metrics_table.add_row(metric_name.replace("_", " ").title(), f"{value:.4f}")

        console.print(metrics_table)


def _display_full(pattern, console: Console):
    """Display full pattern details."""
    tree = Tree(f"[bold cyan]{pattern.pattern_id}[/bold cyan]")
    tree.add(f"[dim]Source: {', '.join(pattern.source_files) if pattern.source_files else 'N/A'}[/dim]")
    tree.add(f"[dim]Records: {pattern.row_count:,}[/dim]")
    tree.add(f"[dim]Learned: {pattern.learned_at}[/dim]")
    tree.add(f"[dim]Version: {pattern.version}[/dim]")

    if pattern.schema:
        fields = tree.add("[bold]Fields[/bold]")
        for field in pattern.schema.get("fields", []):
            name = field.get("name", "N/A")
            field_type = field.get("type", "unknown")
            nullable = field.get("nullable", False)
            unique = field.get("unique", False)

            info = f"{field_type}"
            if nullable:
                info += ", nullable"
            if unique:
                info += ", unique"

            fields.add(f"{name} [dim]({info})[/dim]")

    # Add pattern counts
    patterns_info = tree.add("[bold]Learned Patterns[/bold]")
    patterns_info.add(f"Numeric fields: {len(pattern.numeric_patterns)}")
    patterns_info.add(f"Categorical fields: {len(pattern.categorical_patterns)}")
    patterns_info.add(f"String fields: {len(pattern.string_patterns)}")

    # Add correlation patterns if present
    if pattern.correlation_patterns:
        corr = tree.add("[bold]Correlations[/bold]")
        corr.add(f"[dim]{len(pattern.correlation_patterns)} correlation patterns[/dim]")

    # Add relational patterns if present
    if pattern.relational_patterns:
        rel = tree.add("[bold]Relations[/bold]")
        rel.add(f"[dim]{len(pattern.relational_patterns)} relational patterns[/dim]")

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

    from synth.patterns.storage import PatternStorage

    try:
        storage = PatternStorage(storage_dir=Path(pattern_dir))
        patterns = storage.list_patterns()

        if not patterns:
            console.print("[dim](No patterns found)[/dim]")
            return

        table = Table(title="Learned Patterns")
        table.add_column("Pattern ID", style="cyan")
        table.add_column("File", style="dim")

        for pattern_file in patterns:
            # Extract pattern ID from filename
            pattern_id = Path(pattern_file).stem
            table.add_row(pattern_id, pattern_file)

        console.print(table)
        console.print(f"\n[dim]Total: {len(patterns)} pattern(s)[/dim]")

    except Exception as e:
        console.print(f"[red]Error listing patterns: {e}[/red]")


if __name__ == "__main__":
    app()
