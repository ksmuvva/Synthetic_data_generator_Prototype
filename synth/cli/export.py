"""
CLI command for exporting and importing patterns.
"""

from pathlib import Path
from typing import Optional
import json
import shutil

from typer import Typer, Option
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

app = Typer(help="Export/import patterns")
console = Console()


@app.command()
def export(
    pattern: str = Option(..., "--pattern", "-p", help="Pattern name or path"),
    output: str = Option(..., "--output", "-o", help="Output file path"),
    format_type: str = Option("json", "--format", "-f", help="Output format (json, yaml)"),
):
    """
    Export a learned pattern to a file.

    Examples:
        synth export --pattern customer_pattern --output customer_pattern.json
        synth export --pattern customer_pattern --output customer_pattern.yaml --format yaml
    """
    console.print(f"[cyan]Exporting pattern: {pattern}[/cyan]")
    console.print(f"[dim]  Output: {output}[/dim]")
    console.print(f"[dim]  Format: {format_type}[/dim]")

    from synth.patterns.storage import PatternStorage

    try:
        # Initialize storage
        storage = PatternStorage()

        # Load the pattern
        loaded_pattern = storage.load_pattern(pattern)

        # Prepare output path
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Export based on format
        if format_type == "json":
            _export_json(loaded_pattern, output_path, console)
        elif format_type == "yaml":
            _export_yaml(loaded_pattern, output_path, console)
        else:
            console.print(f"[yellow]Unsupported format: {format_type}. Using JSON.[/yellow]")
            _export_json(loaded_pattern, output_path.with_suffix(".json"), console)

    except Exception as e:
        console.print(f"[red]Export failed: {e}[/red]")


def _export_json(pattern, output_path: Path, console: Console):
    """Export pattern to JSON format."""
    # Serialize pattern to dict
    from synth.patterns.storage import PatternStorage
    pattern_dict = PatternStorage._serialize_pattern(pattern)

    # Write to file with nice formatting
    with open(output_path, "w") as f:
        json.dump(pattern_dict, f, indent=2, default=lambda x: str(x) if not isinstance(x, (int, float, str, bool, list, dict, type(None))) else x)

    console.print(f"[green]Exported to:[/green] {output_path}")
    console.print(f"[dim]  Size: {output_path.stat().st_size:,} bytes[/dim]")


def _export_yaml(pattern, output_path: Path, console: Console):
    """Export pattern to YAML format."""
    try:
        import yaml
    except ImportError:
        console.print("[yellow]PyYAML not installed. Install with: pip install pyyaml[/yellow]")
        console.print("[yellow]Falling back to JSON format.[/yellow]")
        _export_json(pattern, output_path.with_suffix(".json"), console)
        return

    # Serialize pattern to dict
    from synth.patterns.storage import PatternStorage
    pattern_dict = PatternStorage._serialize_pattern(pattern)

    # Write to YAML file
    with open(output_path, "w") as f:
        yaml.dump(pattern_dict, f, default_flow_style=False, sort_keys=False)

    console.print(f"[green]Exported to:[/green] {output_path}")
    console.print(f"[dim]  Size: {output_path.stat().st_size:,} bytes[/dim]")


@app.command()
def import_pattern(
    file: str = Option(..., "--file", "-f", help="Pattern file to import"),
    name: str = Option(None, "--name", "-n", help="Pattern name (uses filename if not specified)"),
    copy_to_storage: bool = Option(True, "--copy/--no-copy", help="Copy to patterns directory"),
):
    """
    Import a pattern from a file.

    Examples:
        synth import --file customer_pattern.json
        synth import --file customer_pattern.json --name my_pattern
        synth import --file /path/to/pattern.json --no-copy
    """
    console.print(f"[cyan]Importing pattern from: {file}[/cyan]")
    if name:
        console.print(f"[dim]  Pattern name: {name}[/dim]")

    from synth.patterns.storage import PatternStorage

    try:
        file_path = Path(file)

        if not file_path.exists():
            console.print(f"[red]File not found: {file_path}[/red]")
            return

        # Load pattern from file
        if file_path.suffix == ".json":
            with open(file_path) as f:
                pattern_dict = json.load(f)
        elif file_path.suffix in [".yaml", ".yml"]:
            try:
                import yaml
            except ImportError:
                console.print("[yellow]PyYAML not installed. Install with: pip install pyyaml[/yellow]")
                return

            with open(file_path) as f:
                pattern_dict = yaml.safe_load(f)
        else:
            console.print(f"[red]Unsupported file format: {file_path.suffix}[/red]")
            console.print("[dim]Supported formats: .json, .yaml, .yml[/dim]")
            return

        # Determine pattern name
        pattern_name = name or file_path.stem

        # Display pattern info
        console.print(f"\n[bold]Pattern Information:[/bold]")
        console.print(f"  ID: {pattern_dict.get('pattern_id', pattern_name)}")
        console.print(f"  Records: {pattern_dict.get('row_count', 'N/A'):,}")
        console.print(f"  Fields: {len(pattern_dict.get('schema', {}).get('fields', []))}")
        console.print(f"  Version: {pattern_dict.get('version', 'N/A')}")

        # Copy to storage if requested
        if copy_to_storage:
            storage = PatternStorage()
            target_path = storage.storage_dir / file_path.name

            # Copy file
            shutil.copy(file_path, target_path)
            console.print(f"\n[green]Copied to:[/green] {target_path}")
            console.print(f"[dim]You can now use: synth inspect --pattern {file_path.stem}[/dim]")
        else:
            console.print(f"\n[dim]Pattern imported from: {file_path}[/dim]")
            console.print(f"[dim]Use with: synth inspect --pattern {file_path}[/dim]")

    except Exception as e:
        console.print(f"[red]Import failed: {e}[/red]")


@app.command()
def validate_pattern(
    file: str = Option(..., "--file", "-f", help="Pattern file to validate"),
):
    """
    Validate a pattern file structure.

    Examples:
        synth export-validate --file customer_pattern.json
    """
    console.print(f"[cyan]Validating pattern file: {file}[/cyan]")

    from synth.patterns.storage import PatternStorage
    from synth.core.errors import PatternError

    try:
        file_path = Path(file)

        if not file_path.exists():
            console.print(f"[red]File not found: {file_path}[/red]")
            return

        # Determine file type and load
        if file_path.suffix == ".json":
            with open(file_path) as f:
                pattern_dict = json.load(f)
        elif file_path.suffix in [".yaml", ".yml"]:
            try:
                import yaml
            except ImportError:
                console.print("[yellow]PyYAML not installed[/yellow]")
                return

            with open(file_path) as f:
                pattern_dict = yaml.safe_load(f)
        else:
            console.print(f"[red]Unsupported file format: {file_path.suffix}[/red]")
            return

        # Validate structure
        issues = []
        warnings = []

        # Check required fields
        if "pattern_id" not in pattern_dict:
            issues.append("Missing required field: pattern_id")
        if not pattern_dict.get("schema") and not (
            pattern_dict.get("numeric_patterns")
            or pattern_dict.get("categorical_patterns")
            or pattern_dict.get("string_patterns")
        ):
            issues.append("Pattern must have either schema or field patterns")

        # Check for deprecated fields
        if "version" not in pattern_dict:
            warnings.append("Missing version field (will default to 1.0)")

        # Check schema structure if present
        if "schema" in pattern_dict:
            schema = pattern_dict["schema"]
            if "fields" not in schema:
                issues.append("Schema missing 'fields' array")
            elif not isinstance(schema["fields"], list):
                issues.append("Schema 'fields' must be an array")

        # Display results
        if issues:
            console.print(f"\n[red]Validation failed with {len(issues)} error(s):[/red]")
            for issue in issues:
                console.print(f"  [red]✗[/red] {issue}")
        else:
            console.print(f"\n[green]Pattern structure is valid![/green]")

        if warnings:
            console.print(f"\n[yellow]{len(warnings)} warning(s):[/yellow]")
            for warning in warnings:
                console.print(f"  [yellow]⚠[/yellow] {warning}")

        # Display pattern info if valid
        if not issues:
            console.print(f"\n[bold]Pattern Summary:[/bold]")
            console.print(f"  ID: {pattern_dict.get('pattern_id', 'N/A')}")
            console.print(f"  Records: {pattern_dict.get('row_count', 'N/A'):,}")
            console.print(f"  Fields: {len(pattern_dict.get('schema', {}).get('fields', []))}")
            console.print(f"  Version: {pattern_dict.get('version', 'N/A')}")

    except json.JSONDecodeError as e:
        console.print(f"[red]Invalid JSON: {e}[/red]")
    except Exception as e:
        console.print(f"[red]Validation failed: {e}[/red]")


# Rename to avoid conflict with Python's built-in
app.command("export-validate")(validate_pattern)

if __name__ == "__main__":
    app()
