"""
CLI command for validating synthetic data quality.
"""

from pathlib import Path
from typer import Typer, Option
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from synth.validation.engine import ValidationEngine, ValidationStatus
from synth.input.parser import FileParser
from synth.core.errors import SynthError

app = Typer(help="Validate synthetic data quality")
console = Console()


@app.command()
def validate(
    synthetic: str = Option(..., "--synthetic", "-s", help="Synthetic data file"),
    reference: str = Option(..., "--reference", "-r", help="Reference/original data file"),
    metrics: str = Option("all", "--metrics", "-m", help="Metrics to compute (all, distribution, schema, semantic)"),
    output: str = Option(None, "--output", "-o", help="Save report to file"),
    report_format: str = Option("text", "--report-format", "-f", help="Report format (text, json, html)"),
):
    """
    Validate synthetic data against reference data.

    Examples:
        synth validate --synthetic synthetic_customers.csv --reference customers_real.csv
        synth validate --synthetic synthetic.csv --reference real.csv --output report.txt
    """
    try:
        # Initialize
        parser = FileParser()
        validator = ValidationEngine()

        console.print(f"[cyan]Running validation...[/cyan]\n")

        # Parse files
        syn_df = parser.parse(synthetic)
        ref_df = parser.parse(reference)

        # Run validation
        result = validator.validate(syn_df, ref_df)

        # Display results
        _display_validation_results(result, metrics)

        # Save report if requested
        if output:
            _save_report(result, output, report_format)
            console.print(f"\n[dim]Report saved to: {output}[/dim]")

    except SynthError as e:
        console.print(f"[red]Error:[/red] {e.message}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error:[/red] {str(e)}")
        raise typer.Exit(1)


def _display_validation_results(result, metrics_filter):
    """Display validation results to user."""
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
        title="Overall Quality Score",
        border_style=color,
    ))

    # Detailed results table
    console.print(f"\n[bold]Test Results:[/bold]")

    table = Table(show_header=True)
    table.add_column("Test", style="cyan")
    table.add_column("Status", justify="center", style="bold")
    table.add_column("Metric", justify="right", style="yellow")
    table.add_column("Threshold", justify="right", style="dim")
    table.add_column("Details", style="dim")

    for test in result.test_results:
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

        metric_str = f"{test.metric:.4f}" if test.metric is not None else "N/A"
        threshold_str = f"{test.threshold:.4f}" if test.threshold is not None else "N/A"

        table.add_row(
            test.test_name,
            f"[{status_color}]{status_symbol}[/{status_color}]",
            metric_str,
            threshold_str,
            test.message,
        )

    console.print(table)

    # Recommendations
    if result.recommendations:
        console.print(f"\n[bold]Recommendations:[/bold]")
        for rec in result.recommendations:
            console.print(f"  • {rec}")


def _save_report(result, output_path, report_format):
    """Save validation report to file."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if report_format == "json":
        import json

        report = {
            "overall_status": result.overall_status.value,
            "quality_score": result.quality_score,
            "schema_score": result.schema_score,
            "statistical_score": result.statistical_score,
            "constraint_score": result.constraint_score,
            "test_results": [
                {
                    "test_name": t.test_name,
                    "status": t.status.value,
                    "metric": t.metric,
                    "message": t.message,
                }
                for t in result.test_results
            ],
            "recommendations": result.recommendations,
        }

        with open(output_path, "w") as f:
            json.dump(report, f, indent=2)

    elif report_format == "html":
        html = f"""
        <!DOCTYPE html>
        <html>
        <head><title>Validation Report</title></head>
        <body>
            <h1>Validation Report</h1>
            <h2>Overall Score: {result.quality_score:.2f} - {result.overall_status.value.upper()}</h2>
            <h3>Component Scores</h3>
            <ul>
                <li>Schema: {result.schema_score:.2f}</li>
                <li>Statistical: {result.statistical_score:.2f}</li>
                <li>Constraint: {result.constraint_score:.2f}</li>
            </ul>
            <h3>Test Results</h3>
            <table border="1">
                <tr><th>Test</th><th>Status</th><th>Metric</th><th>Details</th></tr>
                {"".join(f"<tr><td>{t.test_name}</td><td>{t.status.value}</td><td>{t.metric or 'N/A'}</td><td>{t.message}</td></tr>"
                       for t in result.test_results)}
            </table>
            <h3>Recommendations</h3>
            <ul>
                {"".join(f"<li>{r}</li>" for r in result.recommendations)}
            </ul>
        </body>
        </html>
        """

        with open(output_path, "w") as f:
            f.write(html)

    else:  # text format
        with open(output_path, "w") as f:
            f.write(f"Validation Report\n")
            f.write(f"{'='*50}\n\n")
            f.write(f"Overall Score: {result.quality_score:.2f}\n")
            f.write(f"Status: {result.overall_status.value.upper()}\n\n")
            f.write(f"Component Scores:\n")
            f.write(f"  Schema: {result.schema_score:.2f}\n")
            f.write(f"  Statistical: {result.statistical_score:.2f}\n")
            f.write(f"  Constraint: {result.constraint_score:.2f}\n\n")
            f.write(f"Test Results:\n")
            for test in result.test_results:
                f.write(f"  {test.test_name}: {test.status.value} - {test.message}\n")
            f.write(f"\nRecommendations:\n")
            for rec in result.recommendations:
                f.write(f"  - {rec}\n")


@app.command()
def compare(
    files: list[str] = Option(..., "--files", "-f", help="Files to compare"),
    metric: str = Option("distribution", "--metric", "-m", help="Comparison metric"),
):
    """
    Compare multiple synthetic datasets.

    Examples:
        synth validate-compare --files synth1.csv synth2.csv synth3.csv
    """
    console.print(f"[cyan]Comparing {len(files)} datasets...[/cyan]")

    try:
        parser = FileParser()
        validator = ValidationEngine()

        # Parse all files
        datasets = []
        for file_path in files:
            df = parser.parse(file_path)
            datasets.append((file_path, df))

        # Compare each against the first (reference)
        reference_name, reference_df = datasets[0]

        console.print(f"\n[dim]Using {reference_name} as reference[/dim]\n")

        comparison_table = Table()
        comparison_table.add_column("Dataset", style="cyan")
        comparison_table.add_column("Quality Score", justify="right", style="yellow")
        comparison_table.add_column("Status")

        for name, df in datasets[1:]:
            result = validator.validate(df, reference_df)

            status_color = {
                ValidationStatus.PASS: "green",
                ValidationStatus.WARNING: "yellow",
                ValidationStatus.FAIL: "red",
            }.get(result.overall_status, "dim")

            comparison_table.add_row(
                name,
                f"{result.quality_score:.2f}",
                f"[{status_color}]{result.overall_status.value.upper()}[/{status_color}]"
            )

        console.print(comparison_table)

    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
