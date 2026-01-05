"""
Base output generator interface.

Program of Thoughts:
1. Define abstract base class for all generators
2. Define output format registry
3. Factory function for getting generator by format
4. Common utility methods
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Optional
import pandas as pd

from synth.patterns.schema import Schema


class OutputGenerator(ABC):
    """
    Abstract base class for output generators.

    Self-Reflection: All output generators must implement
    the generate() method with consistent signature.
    """

    @abstractmethod
    def generate(
        self,
        data: pd.DataFrame,
        output_path: Path,
        schema: Optional[Schema] = None,
        **kwargs
    ) -> Path:
        """
        Generate output file from DataFrame.

        Args:
            data: DataFrame to write
            output_path: Where to save the file
            schema: Optional schema for metadata/formatting
            **kwargs: Additional format-specific options

        Returns:
            Path to the generated file
        """
        pass

    @abstractmethod
    def supports_format(self, format_type: str) -> bool:
        """Check if this generator supports the given format."""
        pass

    def apply_styling(self, **kwargs) -> None:
        """
        Apply styling to output (format-specific).

        Subclasses can override to add formatting, colors, etc.
        """
        pass


class GeneratorRegistry:
    """Registry of available output generators."""

    _generators: dict[str, type[OutputGenerator]] = {}

    @classmethod
    def register(cls, format_type: str, generator_class: type[OutputGenerator]) -> None:
        """Register a generator for a format type."""
        cls._generators[format_type.lower()] = generator_class

    @classmethod
    def get_generator(cls, format_type: str) -> Optional[OutputGenerator]:
        """Get a generator instance for the format type."""
        generator_class = cls._generators.get(format_type.lower())
        if generator_class:
            return generator_class()
        return None

    @classmethod
    def list_formats(cls) -> list[str]:
        """List all registered format types."""
        return list(cls._generators.keys())


def get_generator(format_type: str) -> Optional[OutputGenerator]:
    """
    Get an output generator for the specified format.

    Args:
        format_type: Format type (csv, excel, pdf, word, json, etc.)

    Returns:
        OutputGenerator instance or None if format not supported
    """
    return GeneratorRegistry.get_generator(format_type)
