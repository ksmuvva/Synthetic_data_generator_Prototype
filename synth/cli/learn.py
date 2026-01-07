"""
CLI command for learning patterns from data sources.

Self-Reflection Loop:
1. Parse input file
2. Extract schema and patterns
3. Save pattern to storage
4. Display summary to user
"""

from pathlib import Path
from typer import Typer, Option
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.panel import Panel

from synth.input.parser import FileParser
from synth.patterns.schema import SchemaInferrer
from synth.patterns.statistical import UnivariateAnalyzer
from synth.patterns.storage import (
    PatternStorage,
    create_pattern_from_analysis,
)
from synth.patterns.correlation import MultivariateAnalyzer
from synth.config import settings
from synth.core.errors import SynthError

app = Typer(help="Extract patterns from data sources")
console = Console()


@app.command()
def learn(
    source: str = Option(..., "--source", "-s", help="Source file path"),
    name: str = Option(..., "--name", "-n", help="Pattern name"),
    output: str = Option(None, "--output", "-o", help="Output pattern file path"),
    format_type: str = Option(None, "--format", "-f", help="Source format (auto-detected if not specified)"),
    verbose: bool = Option(False, "--verbose", "-v", help="Show detailed progress"),
    correlation: bool = Option(False, "--correlation", help="Learn correlation patterns for multivariate generation"),
):
    """
    Extract patterns from a data source and save them for generation.

    Examples:
        synth learn --source customers.csv --name customer_pattern
        synth learn --source data.xlsx --name sales_data --format excel
        synth learn --source data.pdf --name pdf_data
        synth learn --source customers.csv --name customer_pattern --correlation
    """
    try:
        # Initialize
        parser = FileParser()
        schema_inferrer = SchemaInferrer()
        stat_analyzer = UnivariateAnalyzer()
        storage = PatternStorage()
        multivariate_analyzer = MultivariateAnalyzer() if correlation else None

        console.print(f"[cyan]Learning patterns from: {source}[/cyan]\n")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            disable=not verbose,
        ) as progress:

            # Phase 1: Read source
            if verbose:
                task1 = progress.add_task("Reading source file...", total=None)

            df = parser.parse(source, format_type=format_type)

            if verbose:
                progress.remove_task(task1)

            # Phase 2: Extract schema
            if verbose:
                task2 = progress.add_task("Inferring schema...", total=None)

            schema = schema_inferrer.infer(df)

            if verbose:
                progress.remove_task(task2)

            # Phase 3: Analyze patterns
            if verbose:
                task3 = progress.add_task("Analyzing statistical patterns...", total=None)

            # Analyze each field
            numeric_patterns = {}
            categorical_patterns = {}
            string_patterns = {}

            for field in schema.fields:
                if field.type.value in ("integer", "float"):
                    series = df[field.name].dropna()
                    if len(series) >= 10:
                        pattern = stat_analyzer.analyze_numeric(series, field.name)
                        numeric_patterns[field.name] = pattern

                elif field.type.value == "categorical":
                    series = df[field.name].dropna()
                    if len(series) >= 1:
                        pattern = stat_analyzer.analyze_categorical(series, field.name)
                        categorical_patterns[field.name] = pattern

                elif field.type.value == "string":
                    series = df[field.name].dropna()
                    if len(series) >= 1:
                        pattern = stat_analyzer.analyze_string(series, field.name)
                        string_patterns[field.name] = pattern

            if verbose:
                progress.remove_task(task3)

            # Phase 4: Learn correlations (if enabled)
            correlation_pattern_dict = None
            if correlation:
                if verbose:
                    task4 = progress.add_task("Learning correlation patterns...", total=None)

                # Get numeric columns
                numeric_fields = [
                    f.name for f in schema.fields
                    if f.type.value in ("integer", "float")
                ]

                if len(numeric_fields) >= 2:
                    try:
                        correlation_pattern = multivariate_analyzer.learn_correlation(
                            df[numeric_fields],
                            numeric_columns=numeric_fields
                        )
                        # Serialize correlation pattern for storage
                        correlation_pattern_dict = {
                            "field_order": correlation_pattern.field_order,
                            "correlation_matrix": correlation_pattern.correlation_matrix.tolist(),
                            "copula_type": correlation_pattern.copula_type.value,
                            "quality_score": correlation_pattern.quality_score,
                            "is_positive_definite": correlation_pattern.is_positive_definite,
                            "eigenvalues": correlation_pattern.eigenvalues.tolist() if correlation_pattern.eigenvalues is not None else None,
                            "condition_number": correlation_pattern.condition_number,
                        }
                        console.print(f"[green]✓[/green] Learned correlations for [cyan]{len(numeric_fields)}[/cyan] numeric fields")
                    except ValueError as e:
                        console.print(f"[yellow]Warning:[/yellow] Could not learn correlations: {str(e)}")
                        console.print("[dim]Continuing without correlation patterns...[/dim]")
                else:
                    console.print(f"[yellow]Warning:[/yellow] Need at least 2 numeric fields for correlation analysis (found {len(numeric_fields)})")

                if verbose:
                    progress.remove_task(task4)

            # Phase 5: Create and save pattern
            if verbose:
                task5 = progress.add_task("Creating pattern...", total=None)

            pattern = create_pattern_from_analysis(
                pattern_id=name,
                schema=schema,
                numeric_patterns=numeric_patterns,
                categorical_patterns=categorical_patterns,
                string_patterns=string_patterns,
                source_files=[source],
            )

            # Add correlation patterns if learned
            if correlation_pattern_dict:
                pattern.correlation_patterns = correlation_pattern_dict

            if verbose:
                progress.remove_task(task5)

            # Phase 6: Save to storage
            if verbose:
                task6 = progress.add_task("Saving pattern...", total=None)

            # Determine output path
            if output is None:
                output = f"{name}.json"

            output_path = storage.save_pattern(pattern, output)

            if verbose:
                progress.remove_task(task6)

        # Display success summary
        correlation_note = "\nCorrelations: [cyan]Learned[/cyan]" if correlation and correlation_pattern_dict else ""
        console.print(Panel(
            f"[bold green]✓ Pattern Learned Successfully[/bold green]\n\n"
            f"Pattern ID: [cyan]{name}[/cyan]\n"
            f"Source File: [dim]{source}[/dim]\n"
            f"Records: [cyan]{schema.row_count:,}[/cyan]\n"
            f"Fields: [cyan]{len(schema.fields)}[/cyan]\n"
            f"{correlation_note}"
            f"Output: [dim]{output_path}[/dim]",
            title="Pattern Summary",
            border_style="green",
        ))

        # Show field details
        _display_field_summary(schema, numeric_patterns, categorical_patterns)

    except SynthError as e:
        console.print(f"[red]Error:[/red] {e.message}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error:[/red] {str(e)}")
        raise typer.Exit(1)


def _display_field_summary(schema, numeric_patterns, categorical_patterns):
    """Display summary of learned patterns."""
    console.print("\n[bold]Fields:[/bold]")

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Field", style="cyan")
    table.add_column("Type", style="yellow")
    table.add_column("Distribution/Pattern", style="green")
    table.add_column("Details", style="dim")

    for field in schema.fields:
        details = []
        dist_info = "N/A"

        if field.name in numeric_patterns:
            pattern = numeric_patterns[field.name]
            dist_info = f"{pattern.distribution.dist_type.value}"
            details.append(f"μ={field.mean:.2f}" if field.mean else "")
            details.append(f"σ={field.std:.2f}" if field.std else "")
            details.append(f"min={field.min_value}" if field.min_value is not None else "")
            details.append(f"max={field.max_value}" if field.max_value is not None else "")

        elif field.name in categorical_patterns:
            pattern = categorical_patterns[field.name]
            dist_info = "Categorical"
            details.append(f"{len(pattern.probabilities)} values")
            details.append(f"entropy={pattern.entropy:.2f}")

        elif field.type.value == "string":
            dist_info = "String"
            if field.min_length is not None:
                details.append(f"len={field.min_length}-{field.max_length}")

        table.add_row(
            field.name,
            field.type.value,
            dist_info,
            ", ".join([str(d) for d in details if d])
        )

    console.print(table)


@app.command()
def batch(
    config: str = Option(..., "--config", "-c", help="Batch configuration file (YAML/JSON)"),
):
    """Learn patterns from multiple sources (batch mode)."""
    console.print(f"[cyan]Batch learning from config: {config}[/cyan]")
    console.print("[yellow]Batch mode not yet implemented[/yellow]")


if __name__ == "__main__":
    import typer
    app()
