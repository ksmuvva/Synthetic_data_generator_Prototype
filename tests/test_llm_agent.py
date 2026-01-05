"""
Tests for LLM-powered agent components.

Tests the multi-provider LLM integration (Claude, OpenAI, Gemini).
Note: These tests require valid API keys to run with real providers.
"""

import pytest
import os

from synth.agent.llm import (
    LLMMessage,
    LLMResponse,
    LLMProvider,
    ClaudeProvider,
    OpenAIProvider,
    GeminiProvider,
    get_llm_provider,
)


class TestLLMMessage:
    """Test LLM message dataclass."""

    def test_message_creation(self):
        """Test creating a basic message."""
        msg = LLMMessage(role="user", content="Hello, world!")
        assert msg.role == "user"
        assert msg.content == "Hello, world!"
        assert msg.metadata == {}

    def test_message_with_metadata(self):
        """Test creating a message with metadata."""
        msg = LLMMessage(
            role="system",
            content="You are helpful",
            metadata={"temperature": 0.7}
        )
        assert msg.metadata["temperature"] == 0.7


class TestLLMResponse:
    """Test LLM response dataclass."""

    def test_response_creation(self):
        """Test creating a basic response."""
        response = LLMResponse(content="Response text")
        assert response.content == "Response text"
        assert response.thinking is None

    def test_response_with_thinking(self):
        """Test creating a response with thinking."""
        response = LLMResponse(
            content="Final answer",
            thinking="Let me think about this..."
        )
        assert response.thinking == "Let me think about this..."


class TestClaudeProvider:
    """Test Anthropic Claude provider."""

    def test_claude_provider_no_key_raises_error(self):
        """Test that missing API key raises error."""
        # Ensure no API key is set
        original_key = os.environ.get("ANTHROPIC_API_KEY")
        if original_key:
            del os.environ["ANTHROPIC_API_KEY"]

        try:
            with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
                ClaudeProvider()
        finally:
            # Restore original key if it existed
            if original_key:
                os.environ["ANTHROPIC_API_KEY"] = original_key

    def test_claude_provider_with_key(self):
        """Test creating provider with API key parameter."""
        # This test just verifies initialization, won't make real API calls
        try:
            provider = ClaudeProvider(api_key="test_key")
            assert provider.api_key == "test_key"
            assert provider.model == "claude-3-5-sonnet-20241022"
        except ImportError:
            pytest.skip("anthropic package not installed")


class TestOpenAIProvider:
    """Test OpenAI GPT provider."""

    def test_openai_provider_no_key_raises_error(self):
        """Test that missing API key raises error."""
        original_key = os.environ.get("OPENAI_API_KEY")
        if original_key:
            del os.environ["OPENAI_API_KEY"]

        try:
            with pytest.raises(ValueError, match="OPENAI_API_KEY"):
                OpenAIProvider()
        finally:
            if original_key:
                os.environ["OPENAI_API_KEY"] = original_key

    def test_openai_provider_with_key(self):
        """Test creating provider with API key parameter."""
        try:
            provider = OpenAIProvider(api_key="test_key")
            assert provider.api_key == "test_key"
            assert provider.model == "gpt-4o"
        except ImportError:
            pytest.skip("openai package not installed")


class TestGeminiProvider:
    """Test Google Gemini provider."""

    def test_gemini_provider_no_key_raises_error(self):
        """Test that missing API key raises error."""
        original_key = os.environ.get("GOOGLE_API_KEY")
        if original_key:
            del os.environ["GOOGLE_API_KEY"]

        try:
            with pytest.raises(ValueError, match="GOOGLE_API_KEY"):
                GeminiProvider()
        finally:
            if original_key:
                os.environ["GOOGLE_API_KEY"] = original_key

    def test_gemini_provider_with_key(self):
        """Test creating provider with API key parameter."""
        try:
            provider = GeminiProvider(api_key="test_key")
            assert provider.api_key == "test_key"
            assert provider.model == "gemini-1.5-pro"
        except ImportError:
            pytest.skip("google-generativeai package not installed")


class TestGetLLMProvider:
    """Test LLM provider factory function."""

    def test_get_claude_provider(self):
        """Test getting Claude provider via factory."""
        try:
            provider = get_llm_provider(provider="claude", api_key="test_key")
            assert isinstance(provider, ClaudeProvider)
        except ImportError:
            pytest.skip("anthropic package not installed")

    def test_get_anthropic_provider_alias(self):
        """Test that 'anthropic' is an alias for 'claude'."""
        try:
            provider = get_llm_provider(provider="anthropic", api_key="test_key")
            assert isinstance(provider, ClaudeProvider)
        except ImportError:
            pytest.skip("anthropic package not installed")

    def test_get_openai_provider(self):
        """Test getting OpenAI provider via factory."""
        try:
            provider = get_llm_provider(provider="openai", api_key="test_key")
            assert isinstance(provider, OpenAIProvider)
        except ImportError:
            pytest.skip("openai package not installed")

    def test_get_gpt_provider_alias(self):
        """Test that 'gpt' is an alias for 'openai'."""
        try:
            provider = get_llm_provider(provider="gpt", api_key="test_key")
            assert isinstance(provider, OpenAIProvider)
        except ImportError:
            pytest.skip("openai package not installed")

    def test_get_gemini_provider(self):
        """Test getting Gemini provider via factory."""
        try:
            provider = get_llm_provider(provider="gemini", api_key="test_key")
            assert isinstance(provider, GeminiProvider)
        except ImportError:
            pytest.skip("google-generativeai package not installed")

    def test_get_google_provider_alias(self):
        """Test that 'google' is an alias for 'gemini'."""
        try:
            provider = get_llm_provider(provider="google", api_key="test_key")
            assert isinstance(provider, GeminiProvider)
        except ImportError:
            pytest.skip("google-generativeai package not installed")

    def test_get_unknown_provider_raises_error(self):
        """Test that unknown provider raises ValueError."""
        with pytest.raises(ValueError, match="Unknown provider"):
            get_llm_provider(provider="unknown", api_key="test_key")


class TestLLMProvidersWithoutAPI:
    """Test provider initialization without requiring real API keys."""

    def test_claude_provider_initialization(self):
        """Test Claude provider can be initialized with key."""
        try:
            provider = ClaudeProvider(api_key="test_key_sk_123456")
            assert provider.api_key == "test_key_sk_123456"
            assert provider.model == "claude-3-5-sonnet-20241022"
            assert provider.temperature == 0.7
        except ImportError:
            pytest.skip("anthropic package not installed")

    def test_openai_provider_initialization(self):
        """Test OpenAI provider can be initialized with key."""
        try:
            provider = OpenAIProvider(api_key="test_key_sk_123456")
            assert provider.api_key == "test_key_sk_123456"
            assert provider.model == "gpt-4o"
            assert provider.temperature == 0.7
        except ImportError:
            pytest.skip("openai package not installed")

    def test_gemini_provider_initialization(self):
        """Test Gemini provider can be initialized with key."""
        try:
            provider = GeminiProvider(api_key="test_key_123456")
            assert provider.api_key == "test_key_123456"
            assert provider.model == "gemini-1.5-pro"
            assert provider.temperature == 0.7
        except ImportError:
            pytest.skip("google-generativeai package not installed")

    def test_custom_model_parameter(self):
        """Test that custom model can be specified."""
        try:
            provider = get_llm_provider(
                provider="claude",
                api_key="test_key",
                model="claude-3-opus-20240229"
            )
            assert provider.model == "claude-3-opus-20240229"
        except ImportError:
            pytest.skip("anthropic package not installed")

    def test_custom_temperature_parameter(self):
        """Test that custom temperature can be specified."""
        try:
            provider = get_llm_provider(
                provider="openai",
                api_key="test_key",
                temperature=0.5
            )
            assert provider.temperature == 0.5
        except ImportError:
            pytest.skip("openai package not installed")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
