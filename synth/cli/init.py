"""
CLI command for initializing a new synth project.
"""

from typer import Typer
from rich.console import Console
from rich.table import Table
from pathlib import Path
import shutil

app = Typer(help="Initialize a new synth project")
console = Console()


@app.command(name="init")
def init_command(
    name: str = "synth-project",
    type: str = "tabular",
    force: bool = False,
):
    """
    Initialize a new synth project.

    Example:
        synth init my-project --type tabular
    """
    project_path = Path(name)

    # Check if directory exists
    if project_path.exists() and not force:
        console.print(f"[red]Error:[/red] Directory '{name}' already exists")
        console.print("Use --force to overwrite")
        raise typer.Exit(1)

    # Create project structure
    if project_path.exists():
        shutil.rmtree(project_path)

    project_path.mkdir(parents=True)
    (project_path / "patterns").mkdir()
    (project_path / "data").mkdir()
    (project_path / "output").mkdir()
    (project_path / "reports").mkdir()

    # Create config file
    config_content = """# Synth Project Configuration

project:
  name: {name}
  type: {type}
  created: {date}

patterns:
  directory: patterns
  format: json

data:
  directory: data
  supported_formats:
    - csv
    - excel
    - json

output:
  directory: output
  default_format: csv

validation:
  enabled: true
  quality_threshold: 0.85
""".format(
        name=name, type=type, date="2026-01-05"
    )

    (project_path / "synth-config.yaml").write_text(config_content)

    # Create .gitignore
    gitignore = """# Synth project
patterns/
data/
output/
reports/
*.pyc
__pycache__/
.pytest_cache/
.synth/

# But keep the directories
!.gitkeep
"""

    (project_path / ".gitignore").write_text(gitignore)

    # Create README
    readme = """# {name}

Synth project for generating synthetic data.

## Project Structure

```
{name}/
├── patterns/       # Learned patterns
├── data/          # Source data files
├── output/        # Generated synthetic data
├── reports/       # Validation reports
└── synth-config.yaml
```

## Getting Started

```bash
# Learn patterns from existing data
synth learn --source data/customers.csv --name customer_pattern

# Generate synthetic data
synth generate --pattern customer_pattern --count 1000 --output output/synthetic_customers.csv

# Validate the output
synth validate --synthetic output/synthetic_customers.csv --reference data/customers.csv
```

## Documentation

For more information, visit https://github.com/ksmuvva/Synthetic_data_generator_Prototype
""".format(
        name=name
    )

    (project_path / "README.md").write_text(readme)

    # Success message
    console.print(f"[green]✓[/green] Project initialized: [cyan]{name}[/cyan]")
    console.print(f"\n[bold]Project structure:[/bold]")

    table = Table(show_header=False, box=None)
    table.add_column("Path", style="cyan")
    table.add_column("Description", style="dim")
    table.add_row(f"{name}/", "Project root")
    table.add_row(f"  patterns/", "Learned patterns")
    table.add_row(f"  data/", "Source data files")
    table.add_row(f"  output/", "Generated synthetic data")
    table.add_row(f"  reports/", "Validation reports")
    table.add_row(f"  synth-config.yaml", "Project configuration")

    console.print(table)
    console.print(f"\n[dim]Next steps:[/dim]")
    console.print(f"  cd {name}")
    console.print(f"  synth learn --source data/your-file.csv --name my_pattern")


if __name__ == "__main__":
    import typer

    # Import for type annotation
    from typer import Option

    # Re-define with proper type hints
    @app.command(name="init")
    def init_command(
        name: str = Option("synth-project", "--name", "-n", help="Project name"),
        type: str = Option("tabular", "--type", "-t", help="Project type"),
        force: bool = Option(False, "--force", "-f", help="Overwrite existing directory"),
    ):
        """Initialize a new synth project."""
        init_command_original(name, type, force)

    def init_command_original(name: str, type: str, force: bool):
        """Original implementation."""
        init_command(name, type, force)

    app()
