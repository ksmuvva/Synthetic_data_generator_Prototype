"""
True AI Agent session with LLM integration.

Coordinates the conversational interface using LLM providers (Claude, OpenAI, Gemini)
for intelligent natural language understanding and reasoning.
"""

from pathlib import Path
from typing import Optional, Dict, Any
import pandas as pd
from datetime import datetime

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.markdown import Markdown
    from rich.syntax import Syntax
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn
    from rich.live import Live
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

from synth.agent.state import (
    ConversationState,
    Message,
    MessageRole,
    IntentType,
)
from synth.agent.llm import get_llm_provider, LLMProvider, LLMMessage, ClaudeProvider, OpenAIProvider, GeminiProvider
from synth.agent.llm.parser import LLMIntentParser, LLMReasoningEngine
from synth.agent.schema_builder import SchemaBuilder
from synth.agent.templates.base import get_template_library
from synth.output.base import get_generator
from synth.generation.sampler import StatisticalSampler
from synth.patterns.storage import PatternStorage
from synth.input.parser import FileParser


def _get_provider_name(llm: LLMProvider) -> str:
    """Get human-readable provider name from LLM instance."""
    if isinstance(llm, ClaudeProvider):
        return "Claude (Anthropic)"
    elif isinstance(llm, OpenAIProvider):
        return "GPT (OpenAI)"
    elif isinstance(llm, GeminiProvider):
        return "Gemini (Google)"
    else:
        return llm.__class__.__name__


class TrueAIAgent:
    """
    True AI Agent with LLM integration.

    Uses LLM providers for natural language understanding,
    chain-of-thought reasoning, and dynamic question generation.
    """

    def __init__(
        self,
        llm: Optional[LLMProvider] = None,
        console: Optional["Console"] = None,
        show_thinking: bool = True
    ):
        """
        Initialize the true AI agent.

        Args:
            llm: LLM provider (uses Claude by default)
            console: Rich console instance
            show_thinking: Whether to show LLM's thinking process
        """
        if not RICH_AVAILABLE:
            raise ImportError(
                "rich is required for the AI agent. "
                "Install it with: pip install rich"
            )

        self.console = console or Console()
        self.show_thinking = show_thinking

        # Core LLM components
        self.llm = llm or get_llm_provider(
            provider="claude",
            enable_thinking=show_thinking
        )
        self.provider_name = _get_provider_name(self.llm)
        self.parser = LLMIntentParser(llm=self.llm)
        self.reasoning = LLMReasoningEngine(llm=self.llm)

        # Support components (reuse existing)
        self.schema_builder = SchemaBuilder()
        self.template_library = get_template_library()
        self.sampler = StatisticalSampler()
        self.storage = PatternStorage()
        self.file_parser = FileParser()

        # Conversation state
        self.state = ConversationState()
        self.conversation_id = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Control flags
        self.running = False

    def run(self) -> None:
        """Start the REPL conversation loop with LLM."""
        self.running = False

        # Print welcome
        self._print_welcome()

        self.running = True

        # Main conversation loop
        while self.running:
            try:
                # Get user input
                user_input = self._get_user_input()

                if not user_input:
                    continue

                # Add to history
                self.state.add_message(MessageRole.USER, user_input)

                # Process with LLM
                response = self.process_input(user_input)

                # Display response
                self._display_response(response)

                # Check for exit
                if response.get("action") == "exit":
                    self.running = False

            except KeyboardInterrupt:
                self.console.print("\n[yellow]Interrupted. Type 'exit' to quit.[/yellow]")
            except Exception as e:
                self.console.print(f"[red]Error: {str(e)}[/red]")

        # Print goodbye
        self._print_goodbye()

    def process_input(self, user_input: str) -> Dict[str, Any]:
        """
        Process user input with LLM-powered reasoning.

        Args:
            user_input: Raw user input string

        Returns:
            Response dict with action, message, and metadata
        """
        # Build context for LLM
        context = {
            "history": [
                {"role": msg.role.value, "content": msg.content}
                for msg in self.state.messages[-10:]  # Last 10 messages
            ],
            "current_state": {
                "entity_type": self.state.entity_type,
                "record_count": self.state.record_count,
                "fields": list(self.state.fields.keys()),
                "output_format": self.state.output_format,
                "template_id": self.state.template_id,
            }
        }

        # Parse intent with LLM - show spinner during API call
        from rich.spinner import Spinner
        with self.console.status("[bold cyan]Thinking...[/bold cyan]", spinner="dots"):
            intent = self.parser.parse(user_input, context=context)

        # Handle special intents
        if intent.intent_type == IntentType.EXIT:
            return {"action": "exit", "message": "Goodbye!"}

        if intent.intent_type == IntentType.HELP:
            return {"action": "help", "message": self._get_help_text()}

        if intent.intent_type == IntentType.UPLOAD:
            return self._handle_upload(intent)

        if intent.intent_type == IntentType.USE_TEMPLATE:
            return self._handle_template(intent)

        # Analyze requirements with LLM reasoning - show spinner during API call
        with self.console.status("[bold cyan]Analyzing requirements...[/bold cyan]", spinner="dots"):
            analysis = self.reasoning.analyze_requirements(
                user_input,
                context=context
            )

        # Update state with extracted info
        if "extracted_info" in analysis:
            extracted = analysis["extracted_info"]

            if extracted.get("entity_type"):
                self.state.entity_type = extracted["entity_type"]
            if extracted.get("record_count"):
                self.state.record_count = extracted["record_count"]
            if extracted.get("output_format"):
                self.state.output_format = extracted["output_format"]

            # Extract fields mentioned
            for field_name in extracted.get("fields", []):
                if field_name not in self.state.fields:
                    from synth.agent.state import FieldSpec
                    self.state.fields[field_name] = FieldSpec(
                        name=field_name,
                        data_type="unknown"  # Will be clarified
                    )

        # Build response
        response = {
            "action": analysis.get("next_action", "ask_question"),
            "message": analysis.get("next_question", ""),
            "is_complete": analysis.get("is_complete", False),
            "metadata": {
                "reasoning": analysis.get("reasoning", ""),
                "suggested_answers": analysis.get("suggested_answers", []),
                "missing_info": analysis.get("missing_information", []),
            }
        }

        # Add assistant message to history
        if response["message"]:
            self.state.add_message(MessageRole.ASSISTANT, response["message"])

        # Check if ready to generate
        if response["is_complete"]:
            response["action"] = "confirm_generation"

        return response

    def generate_data(self, output_path: Optional[Path] = None) -> tuple[bool, str, Path]:
        """
        Generate synthetic data using current state.

        Args:
            output_path: Optional output path (auto-generated if None)

        Returns:
            (success, message, output_path)
        """
        try:
            count = self.state.record_count or 100

            # Estimate time: ~0.5 seconds per record (conservative estimate)
            estimated_seconds = max(5, count * 0.5)
            self.console.print(f"[dim]Estimated time: ~{estimated_seconds:.0f} seconds[/dim]\n")

            # Build schema from state
            self.console.print("[cyan]Building schema...[/cyan]")
            if self.state.template_id:
                template = self.template_library.get(self.state.template_id)
                if not template:
                    return False, f"Template '{self.state.template_id}' not found", None
                schema = template.to_schema(count)
            else:
                schema = self.schema_builder.build_from_conversation(self.state)

            # Build pattern
            self.console.print("[cyan]Creating generation pattern...[/cyan]")
            pattern = self.schema_builder.build_pattern_from_schema(
                schema,
                f"agent_{self.conversation_id}"
            )

            # Generate data with progress tracking
            self.console.print(f"[cyan]Generating {count} records...[/cyan]\n")

            # Use progress bar for generation
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TextColumn("({task.completed}/{task.total})"),
                TimeRemainingColumn(),
                console=self.console,
            ) as progress:

                task = progress.add_task(
                    "[cyan]Generating records[/cyan]",
                    total=count
                )

                # Generate in batches for better progress display
                batch_size = max(1, min(100, count // 10))
                df_parts = []

                for i in range(0, count, batch_size):
                    current_batch = min(batch_size, count - i)
                    batch_df = self.sampler.generate(pattern, current_batch)
                    df_parts.append(batch_df)
                    progress.update(task, completed=min(i + current_batch, count))

                import pandas as pd
                df = pd.concat(df_parts, ignore_index=True)

            # Determine output path
            if output_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                ext = self._get_file_extension(self.state.output_format)
                entity = self.state.entity_type or "data"
                output_path = Path(f"{entity}_{timestamp}{ext}")

            # Generate output file
            self.console.print(f"\n[cyan]Writing to {output_path.name}...[/cyan]")
            generator = get_generator(self.state.output_format)
            if not generator:
                return False, f"Unsupported output format: {self.state.output_format}", None

            output_path = generator.generate(
                df,
                output_path,
                schema=schema,
                title=f"{self.state.entity_type or 'Synthetic'} Data"
            )

            return True, f"Generated {len(df)} records", output_path

        except Exception as e:
            return False, f"Generation failed: {str(e)}", None

    def _get_user_input(self) -> str:
        """Get user input from console."""
        from rich.prompt import Prompt
        return Prompt.ask("\n[dim]>[/dim] ", console=self.console)

    def _display_response(self, response: Dict[str, Any]) -> None:
        """Display agent response to user."""
        # Show thinking if enabled and available
        if self.show_thinking and response["metadata"].get("reasoning"):
            thinking = response["metadata"]["reasoning"]
            # Truncate if too long
            if len(thinking) > 500:
                thinking = thinking[:500] + "..."
            self.console.print(f"[dim][Thinking] {thinking}[/dim]\n")

        # Show main message
        self.console.print(f"[cyan]{response['message']}[/cyan]")

        # Show suggested answers if available
        suggested = response["metadata"].get("suggested_answers", [])
        if suggested:
            self.console.print(f"  [dim]Suggestions: {', '.join(map(str, suggested[:5]))}[/dim]")

        # If complete, ask for confirmation and generate
        if response["is_complete"]:
            from rich.prompt import Confirm
            if Confirm.ask("Generate now?", default=True):
                success, message, output_path = self.generate_data()
                if success:
                    self.console.print(f"[green]OK] {message}[/green]")
                    self.console.print(f"[green]OK] Saved to: {output_path}[/green]")
                else:
                    self.console.print(f"[red]Error: {message}[/red]")
            else:
                self.console.print("[yellow]Cancelled.[/yellow]")

    def _handle_upload(self, intent) -> Dict[str, Any]:
        """Handle document upload with LLM analysis."""
        if not intent.metadata or "file_path" not in intent.metadata:
            return {"action": "ask_question", "message": "Which file would you like to upload?"}

        # Parse and analyze with LLM
        # (Implementation similar to rule-based version)
        return {"action": "ask_question", "message": "Upload feature with LLM analysis coming soon"}

    def _handle_template(self, intent) -> Dict[str, Any]:
        """Handle template usage with LLM recommendation."""
        if intent.template_id:
            # Load template
            template = self.template_library.get(intent.template_id)
            if template:
                self.state.template_id = intent.template_id
                return {
                    "action": "ask_question",
                    "message": f"Using template: {template.name}\n\nHow many records? (default: 100)"
                }

        # LLM recommends template
        return {
            "action": "ask_question",
            "message": f"Available templates: {', '.join(self.template_library.list_templates())}\nWhich would you like to use?"
        }

    def _get_file_extension(self, format_type: str) -> str:
        """Get file extension for format type."""
        extensions = {
            "csv": ".csv",
            "excel": ".xlsx",
            "json": ".json",
            "pdf": ".pdf",
            "word": ".docx",
        }
        return extensions.get(format_type, ".csv")

    def _get_help_text(self) -> str:
        """Get help text."""
        return f"""
[bold]AI Agent - Commands:[/bold]

Just describe what you want naturally! Examples:
  "Create 50 customer records with name, email, age"
  "Generate financial transactions with amounts between $10 and $1000"
  "I need 100 user profiles for testing"
  "Use the ecommerce template and output to PDF"

[dim](Powered by {self.provider_name})[/dim]

[dim]Commands:[/dim]
  [dim]help[/dim]  - Show this help message
  [dim]exit[/dim]  - Exit the agent

[dim]Keyboard Shortcuts:[/dim]
  [dim]Ctrl+C[/dim] - Interrupt current operation
        """

    def _print_welcome(self) -> None:
        """Print welcome message."""
        welcome_text = f"""
[bold cyan]AI Agent[/bold cyan] :robot:

[dim]Powered by {self.provider_name} with intelligent reasoning[/dim]

[dim]I'll help you create synthetic data through natural conversation.[/dim]

[dim]Type your request naturally, or 'help' for examples.[/dim]
[dim]Type 'exit' to quit.[/dim]
        """
        self.console.print(Panel(
            Markdown(welcome_text.strip()),
            border_style="bright_cyan",
            padding=(1, 2)
        ))

    def _print_goodbye(self) -> None:
        """Print goodbye message."""
        self.console.print("\n[bold cyan]Session complete! :sparkles:[/bold cyan]\n")

    def load_pattern(self, pattern_path: str) -> bool:
        """Load an existing pattern into the session."""
        try:
            pattern = self.storage.load_pattern(pattern_path)
            self.state.loaded_patterns.append(pattern.pattern_id)
            self.console.print(f"[green]Loaded pattern: {pattern.pattern_id}[/green]")
            return True
        except Exception as e:
            self.console.print(f"[red]Failed to load pattern: {str(e)}[/red]")
            return False
