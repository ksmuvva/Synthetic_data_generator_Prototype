"""
LLM Integration Layer for AI Agent.

Provides multi-provider LLM API integration for true AI-powered reasoning.
Supports: Anthropic Claude, OpenAI GPT, Google Gemini, and more.
"""

from dataclasses import dataclass, field
from typing import Any, Optional
import os
import json


@dataclass
class LLMMessage:
    """Message for LLM conversation."""
    role: str  # "user", "assistant", "system"
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class LLMResponse:
    """Response from LLM."""
    content: str
    raw_response: dict[str, Any] = field(default_factory=dict)
    usage: dict[str, int] = field(default_factory=dict)
    model: str = ""
    thinking: Optional[str] = None  # For extended thinking


class LLMProvider:
    """Base class for LLM providers."""

    def generate(self, messages: list[LLMMessage], **kwargs) -> LLMResponse:
        """Generate response from messages."""
        raise NotImplementedError

    def generate_structured(self, messages: list[LLMMessage], schema: dict, **kwargs) -> dict:
        """Generate structured output matching schema."""
        raise NotImplementedError


class ClaudeProvider(LLMProvider):
    """
    Anthropic Claude API provider.

    Provides intelligent reasoning and natural language understanding
    through Claude's API with extended thinking support.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-3-5-sonnet-20241022",
        max_tokens: int = 4096,
        temperature: float = 0.7,
        enable_thinking: bool = False,
    ):
        """
        Initialize Claude provider.

        Args:
            api_key: Anthropic API key (or from ANTHROPIC_API_KEY env var)
            model: Model to use
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (0-1)
            enable_thinking: Enable extended thinking mode
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY not found. Set it as environment variable "
                "or pass api_key parameter."
            )

        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.enable_thinking = enable_thinking

        try:
            import anthropic
            self.client = anthropic.Anthropic(api_key=self.api_key)
        except ImportError:
            raise ImportError(
                "anthropic package is required. Install it with: pip install anthropic"
            )

    def generate(self, messages: list[LLMMessage], **kwargs) -> LLMResponse:
        """Generate response from Claude."""
        api_messages = [
            {"role": m.role, "content": m.content}
            for m in messages
        ]

        params = {
            "model": kwargs.get("model", self.model),
            "max_tokens": kwargs.get("max_tokens", self.max_tokens),
            "temperature": kwargs.get("temperature", self.temperature),
        }

        # Add system message if present
        system_msg = next((m for m in messages if m.role == "system"), None)
        if system_msg:
            params["system"] = system_msg.content
            api_messages = [m for m in api_messages if m["role"] != "system"]

        try:
            if self.enable_thinking and "thinking" in self.model.lower():
                response = self.client.messages.create(
                    **params,
                    messages=api_messages,
                    thinking={
                        "type": "enabled",
                        "budget_tokens": kwargs.get("thinking_budget", 16000),
                    },
                )
            else:
                response = self.client.messages.create(
                    **params,
                    messages=api_messages,
                )

            # Extract thinking content if present
            thinking = None
            for block in response.content:
                if block.type == "thinking":
                    thinking = block.text
                    break

            # Extract main content
            content = ""
            for block in response.content:
                if block.type == "text":
                    content += block.text

            return LLMResponse(
                content=content,
                raw_response=response.model_dump(),
                usage=response.usage.model_dump() if hasattr(response, 'usage') else {},
                model=response.model,
                thinking=thinking,
            )

        except Exception as e:
            raise RuntimeError(f"Claude API call failed: {str(e)}") from e

    def generate_structured(self, messages: list[LLMMessage], schema: dict, **kwargs) -> dict:
        """Generate structured output (JSON) matching schema."""
        schema_instruction = f"\n\nYou must respond with valid JSON matching this schema:\n{json.dumps(schema, indent=2)}"

        modified_messages = [
            LLMMessage(
                role=m.role,
                content=m.content + (schema_instruction if m.role == "system" else ""),
                metadata=m.metadata
            )
            for m in messages
        ]

        response = self.generate(modified_messages, **kwargs)

        # Parse JSON from response
        try:
            content = response.content.strip()
            if "```json" in content:
                start = content.find("```json") + 7
                end = content.rfind("```")
                content = content[start:end].strip()
            elif "```" in content:
                start = content.find("```") + 3
                end = content.rfind("```")
                content = content[start:end].strip()

            return json.loads(content)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse LLM response as JSON: {str(e)}\nResponse: {response.content[:200]}") from e


class OpenAIProvider(LLMProvider):
    """
    OpenAI GPT API provider.

    Provides intelligent reasoning through GPT-4 and GPT-3.5-turbo models.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o",
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ):
        """
        Initialize OpenAI provider.

        Args:
            api_key: OpenAI API key (or from OPENAI_API_KEY env var)
            model: Model to use (gpt-4o, gpt-4-turbo, gpt-3.5-turbo, etc.)
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (0-1)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OPENAI_API_KEY not found. Set it as environment variable "
                "or pass api_key parameter."
            )

        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature

        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=self.api_key)
        except ImportError:
            raise ImportError(
                "openai package is required. Install it with: pip install openai"
            )

    def generate(self, messages: list[LLMMessage], **kwargs) -> LLMResponse:
        """Generate response from OpenAI."""
        api_messages = [
            {"role": m.role, "content": m.content}
            for m in messages
        ]

        try:
            response = self.client.chat.completions.create(
                model=kwargs.get("model", self.model),
                messages=api_messages,
                max_tokens=kwargs.get("max_tokens", self.max_tokens),
                temperature=kwargs.get("temperature", self.temperature),
            )

            return LLMResponse(
                content=response.choices[0].message.content,
                raw_response=response.model_dump(),
                usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                },
                model=response.model,
            )

        except Exception as e:
            raise RuntimeError(f"OpenAI API call failed: {str(e)}") from e

    def generate_structured(self, messages: list[LLMMessage], schema: dict, **kwargs) -> dict:
        """Generate structured output (JSON) matching schema."""
        schema_instruction = f"\n\nYou must respond with valid JSON matching this schema:\n{json.dumps(schema, indent=2)}"

        modified_messages = [
            LLMMessage(
                role=m.role,
                content=m.content + (schema_instruction if m.role == "system" else ""),
                metadata=m.metadata
            )
            for m in messages
        ]

        response = self.generate(modified_messages, **kwargs)

        # Parse JSON from response
        try:
            content = response.content.strip()
            if "```json" in content:
                start = content.find("```json") + 7
                end = content.rfind("```")
                content = content[start:end].strip()
            elif "```" in content:
                start = content.find("```") + 3
                end = content.rfind("```")
                content = content[start:end].strip()

            return json.loads(content)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse LLM response as JSON: {str(e)}\nResponse: {response.content[:200]}") from e


class GeminiProvider(LLMProvider):
    """
    Google Gemini API provider.

    Provides intelligent reasoning through Gemini Pro and Ultra models.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gemini-1.5-pro",
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ):
        """
        Initialize Gemini provider.

        Args:
            api_key: Google API key (or from GOOGLE_API_KEY env var)
            model: Model to use (gemini-1.5-pro, gemini-1.5-flash, etc.)
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (0-1)
        """
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError(
                "GOOGLE_API_KEY not found. Set it as environment variable "
                "or pass api_key parameter."
            )

        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature

        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self.client = genai.GenerativeModel(model)
        except ImportError:
            raise ImportError(
                "google-generativeai package is required. Install it with: pip install google-generativeai"
            )

    def generate(self, messages: list[LLMMessage], **kwargs) -> LLMResponse:
        """Generate response from Gemini."""
        # Convert messages to Gemini format
        # Gemini doesn't have system messages, so we prepend to first user message
        system_msg = next((m for m in messages if m.role == "system"), None)

        chat_history = []
        for m in messages:
            if m.role == "system":
                continue  # Handle separately
            elif m.role == "user":
                content = m.content
                if system_msg and not chat_history:
                    content = f"{system_msg.content}\n\n{m.content}"
                chat_history.append({"role": "user", "parts": [content]})
            elif m.role == "assistant":
                chat_history.append({"role": "model", "parts": [m.content]})

        try:
            # Start chat with history (excluding last message which is the current input)
            if len(chat_history) > 1:
                chat = self.client.start_chat(history=chat_history[:-1])
                response = chat.send_message(
                    chat_history[-1]["parts"][0],
                    generation_config={
                        "max_output_tokens": kwargs.get("max_tokens", self.max_tokens),
                        "temperature": kwargs.get("temperature", self.temperature),
                    }
                )
            else:
                response = self.client.generate_content(
                    chat_history[0]["parts"][0],
                    generation_config={
                        "max_output_tokens": kwargs.get("max_tokens", self.max_tokens),
                        "temperature": kwargs.get("temperature", self.temperature),
                    }
                )

            return LLMResponse(
                content=response.text,
                raw_response={"candidates": [to_dict(c) for c in response.candidates] if hasattr(response, 'candidates') else []},
                usage=response.usage_metadata.to_dict() if hasattr(response, 'usage_metadata') else {},
                model=self.model,
            )

        except Exception as e:
            raise RuntimeError(f"Gemini API call failed: {str(e)}") from e

    def generate_structured(self, messages: list[LLMMessage], schema: dict, **kwargs) -> dict:
        """Generate structured output (JSON) matching schema."""
        schema_instruction = f"\n\nYou must respond with valid JSON matching this schema:\n{json.dumps(schema, indent=2)}"

        # For Gemini, we need to use JSON mode
        modified_messages = []
        for m in messages:
            if m.role == "system":
                modified_messages.append(LLMMessage(
                    role=m.role,
                    content=m.content + schema_instruction,
                    metadata=m.metadata
                ))
            else:
                modified_messages.append(m)

        response = self.generate(modified_messages, **kwargs)

        # Parse JSON from response
        try:
            content = response.content.strip()
            if "```json" in content:
                start = content.find("```json") + 7
                end = content.rfind("```")
                content = content[start:end].strip()
            elif "```" in content:
                start = content.find("```") + 3
                end = content.rfind("```")
                content = content[start:end].strip()

            return json.loads(content)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse LLM response as JSON: {str(e)}\nResponse: {response.content[:200]}") from e


def to_dict(obj):
    """Helper to convert objects to dict."""
    if hasattr(obj, 'model_dump'):
        return obj.model_dump()
    elif hasattr(obj, '__dict__'):
        return obj.__dict__
    return obj


def get_llm_provider(
    provider: str = "claude",
    api_key: Optional[str] = None,
    **kwargs
) -> LLMProvider:
    """
    Get LLM provider instance.

    Args:
        provider: Provider type ("claude", "openai", "gemini")
        api_key: API key for the provider (overrides env var)
        **kwargs: Additional provider parameters (model, temperature, etc.)

    Returns:
        Configured LLM provider

    Raises:
        ValueError: If provider is unknown or API key is missing
    """
    providers = {
        "claude": ClaudeProvider,
        "anthropic": ClaudeProvider,
        "openai": OpenAIProvider,
        "gpt": OpenAIProvider,
        "gemini": GeminiProvider,
        "google": GeminiProvider,
    }

    provider_lower = provider.lower()
    if provider_lower not in providers:
        raise ValueError(
            f"Unknown provider: {provider}. "
            f"Supported providers: {', '.join(providers.keys())}"
        )

    provider_class = providers[provider_lower]
    return provider_class(api_key=api_key, **kwargs)
