"""
Interactive Setup Wizard for AI Agent.

Handles:
- Provider selection (Claude, OpenAI, Gemini)
- Model selection
- API key entry
- Requirements gathering
- Document upload
- LLM-powered clarification
"""

from pathlib import Path
from typing import Optional, Dict, Any, Tuple
import os

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.prompt import Prompt, Confirm
    from rich.markdown import Markdown
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


# Provider configurations
PROVIDER_CONFIGS = {
    "claude": {
        "name": "Claude (Anthropic)",
        "env_key": "ANTHROPIC_API_KEY",
        "models": [
            {"id": "claude-3-5-sonnet-20241022", "name": "Claude 3.5 Sonnet", "description": "Best balance, intelligent reasoning [recommended]"},
            {"id": "claude-3-5-haiku-20241022", "name": "Claude 3.5 Haiku", "description": "Fastest, good for simple tasks"},
            {"id": "claude-3-opus-20240229", "name": "Claude 3 Opus", "description": "Most capable, highest quality"},
        ],
    },
    "openai": {
        "name": "GPT (OpenAI)",
        "env_key": "OPENAI_API_KEY",
        "models": [
            {"id": "gpt-4o", "name": "GPT-4o", "description": "Latest, most capable [recommended]"},
            {"id": "gpt-4-turbo", "name": "GPT-4 Turbo", "description": "Fast, high quality"},
            {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo", "description": "Fastest, cost-effective"},
        ],
    },
    "gemini": {
        "name": "Gemini (Google)",
        "env_key": "GOOGLE_API_KEY",
        "models": [
            {"id": "gemini-1.5-pro", "name": "Gemini 1.5 Pro", "description": "High quality, 1M context [recommended]"},
            {"id": "gemini-1.5-flash", "name": "Gemini 1.5 Flash", "description": "Fastest, cost-effective"},
            {"id": "gemini-pro", "name": "Gemini Pro", "description": "Previous generation"},
        ],
    },
}


class SetupWizard:
    """
    Interactive setup wizard for AI Agent configuration.

    Guides users through:
    1. Provider selection
    2. Model selection
    3. API key entry
    4. Requirements gathering
    5. Document upload
    """

    def __init__(self, console: Optional["Console"] = None):
        """Initialize the setup wizard."""
        if not RICH_AVAILABLE:
            raise ImportError(
                "rich is required for the setup wizard. "
                "Install it with: pip install rich"
            )

        self.console = console or Console()
        self.provider: Optional[str] = None
        self.model: Optional[str] = None
        self.api_key: Optional[str] = None
        self.requirements: Optional[str] = None
        self.uploaded_files: list[Path] = []

    def run(self) -> Tuple[str, str, str, str, list[Path]]:
        """
        Run the complete setup wizard.

        Returns:
            (provider, model, api_key, requirements, uploaded_files)
        """
        self._print_banner()

        # Step 1: Provider selection
        self.provider = self._select_provider()

        # Step 2: Model selection
        self.model = self._select_model(self.provider)

        # Step 3: API key entry
        self.api_key = self._enter_api_key(self.provider)

        # Step 4: Requirements gathering
        self.requirements = self._gather_requirements()

        # Step 5: Document upload
        self.uploaded_files = self._offer_document_upload()

        # Summary
        self._print_summary()

        return (
            self.provider,
            self.model,
            self.api_key,
            self.requirements,
            self.uploaded_files,
        )

    def _print_banner(self) -> None:
        """Print welcome banner."""
        banner = """
===============================================================================
                    Synthetic Data AI Agent Setup
===============================================================================

I'll guide you through setting up your AI-powered data generation agent.

Powered by state-of-the-art LLMs (Claude, GPT-4, Gemini) with advanced
natural language understanding and reasoning capabilities.
        """
        self.console.print(Panel(
            Markdown(banner.strip()),
            border_style="bright_cyan",
            padding=(0, 2)
        ))

    def _select_provider(self) -> str:
        """Guide user to select LLM provider."""
        self.console.print("\n[bold cyan]Step 1: Select Your AI Provider[/bold cyan]\n")

        table = Table(title="Available LLM Providers", show_header=True, header_style="bold magenta")
        table.add_column("Option", style="cyan", width=8)
        table.add_column("Provider", style="green")
        table.add_column("Features", style="dim")

        table.add_row("1", "Claude (Anthropic)", "Extended thinking, 200K context, best reasoning")
        table.add_row("2", "GPT (OpenAI)", "GPT-4o, fast response, widely adopted")
        table.add_row("3", "Gemini (Google)", "1M context window, multimodal")

        self.console.print(table)

        # Keyboard shortcuts hint
        self.console.print("\n[dim]Tips: Press Enter for default (1), Ctrl+C to cancel[/dim]\n")

        while True:
            choice = Prompt.ask(
                "\n[bold cyan]Choose your AI provider[/bold cyan]",
                choices=["1", "2", "3"],
                default="1"
            )

            providers = {"1": "claude", "2": "openai", "3": "gemini"}
            selected = providers[choice]

            # Show confirmation
            provider_name = PROVIDER_CONFIGS[selected]["name"]
            self.console.print(f"\n[green]Selected:[/green] {provider_name}")

            if Confirm.ask("Is this correct? (or 'e' to edit)", default=True):
                return selected

            # If not correct, loop again

    def _select_model(self, provider: str) -> str:
        """Guide user to select model."""
        self.console.print(f"\n[bold cyan]Step 2: Select Your Model[/bold cyan]\n")

        config = PROVIDER_CONFIGS[provider]
        models = config["models"]

        table = Table(title=f"Available {config['name']} Models", show_header=True, header_style="bold magenta")
        table.add_column("Option", style="cyan", width=8)
        table.add_column("Model", style="green")
        table.add_column("Description", style="dim")

        for i, model in enumerate(models, 1):
            table.add_row(str(i), model["name"], model["description"])

        self.console.print(table)

        # Keyboard shortcuts hint
        self.console.print("\n[dim]Tips: Press Enter for default (1), Ctrl+C to cancel[/dim]\n")

        while True:
            choices = [str(i) for i in range(1, len(models) + 1)]
            choice = Prompt.ask(
                f"\n[bold cyan]Choose your model[/bold cyan]",
                choices=choices,
                default="1"
            )

            selected_model = models[int(choice) - 1]
            model_id = selected_model["id"]

            # Show confirmation
            self.console.print(f"\n[green]Selected:[/green] {selected_model['name']}")

            if Confirm.ask("Is this correct? (or 'e' to edit)", default=True):
                return model_id

            # If not correct, loop again

    def _enter_api_key(self, provider: str) -> str:
        """Guide user to enter API key."""
        self.console.print(f"\n[bold cyan]Step 3: Enter API Key[/bold cyan]\n")

        config = PROVIDER_CONFIGS[provider]
        env_var = config["env_key"]

        # Check if API key exists in environment
        existing_key = os.getenv(env_var)

        if existing_key:
            self.console.print(f"[green]Found API key in environment:[/green] {env_var}")
            self.console.print("[dim](Key is hidden for security)[/dim]")

            if Confirm.ask("\nUse this API key?", default=True):
                return existing_key

            # If user wants to enter a different key
            self.console.print("\n[dim]Enter a different API key:[/dim]")

        # Prompt for API key
        self.console.print(f"\n[dim]Get your API key from:[/dim]")
        if provider == "claude":
            self.console.print("  [cyan]https://console.anthropic.com/[/cyan]")
        elif provider == "openai":
            self.console.print("  [cyan]https://platform.openai.com/api-keys[/cyan]")
        elif provider == "gemini":
            self.console.print("  [cyan]https://makersuite.google.com/app/apikey[/cyan]")

        while True:
            api_key = Prompt.ask(
                f"\n[bold cyan]Enter your {config['name']} API key[/bold cyan]",
                password=True
            )

            if not api_key:
                self.console.print("[red]API key cannot be empty. Please try again.[/red]")
                continue

            # Validate API key format (basic check)
            if len(api_key) < 20:
                self.console.print("[yellow]Warning: API key seems short. Make sure you entered it correctly.[/yellow]")
                if not Confirm.ask("Continue anyway?", default=False):
                    continue

            self.console.print("[green]API key accepted![/green]")

            # Ask if user wants to save it
            if Confirm.ask("\nSave API key to environment for future sessions?", default=False):
                self.console.print(f"\n[dim]To save permanently, add to your ~/.bashrc or ~/.zshrc:[/dim]")
                self.console.print(f"  [cyan]export {env_var}=\"{api_key}\"[/cyan]")

            return api_key

    def _gather_requirements(self) -> str:
        """Gather user requirements."""
        self.console.print("\n[bold cyan]Step 4: Describe Your Data Needs[/bold cyan]\n")

        self.console.print("[dim]Tell me what kind of synthetic data you need.[/dim]")
        self.console.print("[dim]Be as specific as you like - the AI will understand![/dim]\n")

        examples = [
            "Create 50 financial transactions with amounts between $10 and $1000",
            "Generate 1000 customer records with names, emails, and addresses",
            "I need user profiles for testing: 500 records with age, location, and preferences",
            "Generate e-commerce orders: 200 records with products, quantities, and prices",
        ]

        self.console.print("[dim]Example prompts:[/dim]")
        for i, example in enumerate(examples, 1):
            self.console.print(f"  [dim]{i}.[/dim] {example}")

        self.console.print()

        while True:
            requirements = Prompt.ask(
                "\n[bold cyan]What data do you want to generate?[/bold cyan]",
                default=""
            )

            if not requirements or len(requirements.strip()) < 5:
                self.console.print("[red]Please provide more detail about your data requirements.[/red]")
                continue

            # Show confirmation
            self.console.print(f"\n[green]Your requirements:[/green] {requirements}")

            if Confirm.ask("\nIs this correct?", default=True):
                return requirements

            # If not correct, ask again
            self.console.print("\n[dim]Let's try again. Describe your data needs:[/dim]")

    def _offer_document_upload(self) -> list[Path]:
        """Offer user to upload reference documents."""
        self.console.print("\n[bold cyan]Step 5: Upload Reference Documents (Optional)[/bold cyan]\n")

        self.console.print("[dim]You can upload existing data files as reference.[/dim]")
        self.console.print("[dim]The AI will analyze them to match structure and patterns.[/dim]")
        self.console.print("[dim]Supported formats: CSV, Excel, JSON, PDF[/dim]\n")

        uploaded_files = []

        if not Confirm.ask("Do you want to upload any reference documents?", default=False):
            return uploaded_files

        while True:
            file_path = Prompt.ask(
                "\n[bold cyan]Enter file path[/bold cyan] (or press Enter to finish)",
                default=""
            )

            if not file_path:
                break

            path = Path(file_path)

            if not path.exists():
                self.console.print(f"[red]File not found: {file_path}[/red]")
                continue

            uploaded_files.append(path)
            self.console.print(f"[green]Added:[/green] {path.name}")

            if not Confirm.ask("\nUpload another file?", default=False):
                break

        return uploaded_files

    def _print_summary(self) -> None:
        """Print configuration summary."""
        self.console.print("\n" + "="*70)
        self.console.print("[bold cyan]Configuration Summary[/bold cyan]\n")

        config = PROVIDER_CONFIGS[self.provider]

        # Provider info
        self.console.print(f"[cyan]Provider:[/cyan] {config['name']}")
        model_info = next(m for m in config["models"] if m["id"] == self.model)
        self.console.print(f"[cyan]Model:[/cyan] {model_info['name']} ({self.model})")
        self.console.print(f"[cyan]API Key:[/cyan] {'*' * 20}")

        # Requirements
        self.console.print(f"\n[cyan]Requirements:[/cyan]")
        self.console.print(f"  {self.requirements}")

        # Uploaded files
        if self.uploaded_files:
            self.console.print(f"\n[cyan]Uploaded Files:[/cyan]")
            for file in self.uploaded_files:
                self.console.print(f"  - {file.name}")
        else:
            self.console.print(f"\n[cyan]Uploaded Files:[/cyan] None")

        self.console.print("\n" + "="*70)

        self.console.print("\n[green]Setup complete![/green]")
        self.console.print("[dim]The AI will now analyze your requirements and begin generating data.[/dim]\n")


def run_setup_wizard(console: Optional["Console"] = None) -> Tuple[str, str, str, str, list[Path]]:
    """
    Run the interactive setup wizard.

    Args:
        console: Rich console instance

    Returns:
        (provider, model, api_key, requirements, uploaded_files)
    """
    wizard = SetupWizard(console)
    return wizard.run()
