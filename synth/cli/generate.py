"""
CLI command for generating synthetic data.

Self-Reflection Loop:
1. Load pattern from storage
2. Initialize sampler
3. Generate synthetic data
4. Save to output file
5. Optionally validate
"""

from pathlib import Path
from typer import Typer, Option
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.panel import Panel
import pandas as pd

from synth.generation.sampler import StatisticalSampler
from synth.patterns.storage import PatternStorage
from synth.validation.engine import ValidationEngine
from synth.input.parser import FileParser
from synth.config import settings
from synth.core.errors import SynthError

app = Typer(help="Generate synthetic data from learned patterns")
console = Console()


@app.command()
def generate(
    pattern: str = Option(..., "--pattern", "-p", help="Pattern name or file path"),
    count: int = Option(..., "--count", "-n", help="Number of records to generate"),
    output: str = Option(..., "--output", "-o", help="Output file path"),
    seed: int = Option(None, "--seed", help="Random seed for reproducibility"),
    validate: bool = Option(False, "--validate", "-v", help="Validate after generation"),
    reference: str = Option(None, "--reference", "-r", help="Reference file for validation"),
    format_type: str = Option("csv", "--format", "-f", help="Output format (csv, excel, json, parquet)"),
):
    """
    Generate synthetic data from a learned pattern.

    Examples:
        synth generate --pattern customer_pattern.json --count 10000 --output synthetic_customers.csv
        synth generate --pattern customer_pattern.json --count 1000 --seed 42 --output output.csv
        synth generate --pattern customer_pattern.json --count 5000 --validate --reference original_data.csv
    """
    try:
        # Initialize
        storage = PatternStorage()
        sampler = StatisticalSampler(seed=seed)

        console.print(f"[cyan]Generating synthetic data...[/cyan]\n")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:

            # Phase 1: Load pattern
            task1 = progress.add_task("Loading pattern...", total=100)

            # Check if pattern is a file or name
            pattern_path = Path(pattern)
            if pattern_path.exists() and pattern_path.suffix == ".json":
                # Load from file path
                loaded_pattern = storage.load_pattern(pattern_path.name)
            else:
                # Try to load from patterns directory
                pattern_file = f"{pattern}.json"
                try:
                    loaded_pattern = storage.load_pattern(pattern_file)
                except Exception:
                    # Try as direct file path
                    loaded_pattern = storage.load_pattern(pattern)

            progress.update(task1, completed=100)

            # Phase 2: Generate records
            task2 = progress.add_task(f"Generating {count:,} records...", total=count)

            df = sampler.generate(loaded_pattern, count)

            progress.update(task2, completed=count)

            # Phase 3: Write output
            task3 = progress.add_task("Writing output...", total=100)

            # Ensure output directory exists
            output_path = Path(output)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Write based on format
            if format_type == "csv":
                df.to_csv(output_path, index=False)
            elif format_type == "excel":
                df.to_excel(output_path, index=False)
            elif format_type == "json":
                df.to_json(output_path, orient="records", indent=2)
            elif format_type == "jsonl":
                df.to_json(output_path, orient="records", lines=True)
            elif format_type == "parquet":
                df.to_parquet(output_path, index=False)
            else:
                # Default to CSV
                df.to_csv(output_path, index=False)

            progress.update(task3, completed=100)

        # Display success summary
        console.print(Panel(
            f"[bold green]✓ Generation Complete[/bold green]\n\n"
            f"Records: [cyan]{count:,}[/cyan]\n"
            f"Columns: [cyan]{len(df.columns)}[/cyan]\n"
            f"Pattern: [dim]{loaded_pattern.pattern_id}[/dim]\n"
            f"Output: [dim]{output_path}[/dim]"
            if seed else f"",
            title="Generation Summary",
            border_style="green",
        ))

        # Show sample data
        console.print("\n[bold]Sample Data (first 5 rows):[/bold]")
        console.print(df.head().to_string(index=False))

        # Phase 4: Validate if requested
        if validate:
            console.print(f"\n[cyan]Running validation...[/cyan]")

            if reference is None:
                console.print("[yellow]Warning: No reference file provided. Cannot run full validation.[/yellow]")
                console.print("[dim]Use --reference to specify original data for comparison[/dim]")
            else:
                try:
                    validator = ValidationEngine()
                    parser = FileParser()

                    # Load reference data
                    ref_df = parser.parse(reference)

                    # Run validation
                    result = validator.validate(df, ref_df)

                    # Display validation results
                    _display_validation_results(result)

                except Exception as e:
                    console.print(f"[yellow]Validation failed: {str(e)}[/yellow]")

    except SynthError as e:
        console.print(f"[red]Error:[/red] {e.message}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error:[/red] {str(e)}")
        raise typer.Exit(1)


def _display_validation_results(result):
    """Display validation results to user."""
    from synth.validation.engine import ValidationStatus

    # Overall score
    status_color = {
        ValidationStatus.PASS: "green",
        ValidationStatus.WARNING: "yellow",
        ValidationStatus.FAIL: "red",
    }

    color = status_color.get(result.overall_status, "dim")

    console.print(Panel(
        f"[bold {color}]Quality Score: {result.quality_score:.2f}[/bold {color}]\n"
        f"[bold {color}]Status: {result.overall_status.value.upper()}[/bold {color}]\n\n"
        f"Schema Score: [cyan]{result.schema_score:.2f}[/cyan]\n"
        f"Statistical Score: [cyan]{result.statistical_score:.2f}[/cyan]\n"
        f"Constraint Score: [cyan]{result.constraint_score:.2f}[/cyan]",
        title="Validation Results",
        border_style=color,
    ))

    # Component scores
    if result.test_results:
        console.print("\n[bold]Test Results:[/bold]")

        for test in result.test_results[:10]:  # Show first 10
            status_symbol = {
                ValidationStatus.PASS: "✓",
                ValidationStatus.WARNING: "⚠",
                ValidationStatus.FAIL: "✗",
            }.get(test.status, "?")

            status_color = {
                ValidationStatus.PASS: "green",
                ValidationStatus.WARNING: "yellow",
                ValidationStatus.FAIL: "red",
            }.get(test.status, "dim")

            console.print(f"  [{status_color}]{status_symbol}[/{status_color}] {test.test_name}: {test.message}")

    # Recommendations
    if result.recommendations:
        console.print(f"\n[bold]Recommendations:[/bold]")
        for rec in result.recommendations[:5]:
            console.print(f"  • {rec}")


@app.command()
def scale(
    pattern: str = Option(..., "--pattern", "-p", help="Pattern name or file path"),
    scale: int = Option(..., "--scale", "-s", help="Scale factor (2, 10, 100)"),
    output: str = Option(..., "--output", "-o", help="Output file path"),
    seed: int = Option(None, "--seed", help="Random seed"),
):
    """
    Generate scaled synthetic data (2x, 10x, 100x of source).

    Examples:
        synth generate-scale --pattern customer_pattern --scale 10 --output scaled_customers.csv
    """
    try:
        storage = PatternStorage()
        sampler = StatisticalSampler(seed=seed)

        # Load pattern
        pattern_obj = storage.load_pattern(f"{pattern}.json")

        # Calculate count from source
        count = pattern_obj.row_count * scale

        console.print(f"[cyan]Generating {scale}x scaled data ({count:,} records)...[/cyan]")

        # Generate
        df = sampler.generate(pattern_obj, count)

        # Save
        df.to_csv(output, index=False)

        console.print(f"[green]✓[/green] Generated [cyan]{count:,}[/cyan] records to [cyan]{output}[/cyan]")

    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
