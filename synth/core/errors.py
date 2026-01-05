"""
Core error classes for synth.
"""

from typing import Optional, Any


class SynthError(Exception):
    """Base exception for all synth errors."""

    def __init__(self, message: str, details: Optional[dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class ConfigurationError(SynthError):
    """Error in configuration."""

    pass


class InputError(SynthError):
    """Error in input data or files."""

    pass


class PatternError(SynthError):
    """Error in pattern learning or loading."""

    pass


class GenerationError(SynthError):
    """Error during data generation."""

    pass


class ValidationError(SynthError):
    """Error during validation."""

    def __init__(
        self, message: str, score: Optional[float] = None, details: Optional[dict[str, Any]] = None
    ):
        super().__init__(message, details)
        self.score = score


class OutputError(SynthError):
    """Error in output writing."""

    pass


class FileFormatError(InputError):
    """Unsupported or invalid file format."""

    def __init__(self, format: str, supported_formats: list[str]):
        super().__init__(
            f"Unsupported file format: {format}",
            {"supported_formats": supported_formats},
        )


class SchemaError(InputError):
    """Error in data schema."""

    pass


class ConstraintError(SynthError):
    """Error in constraint satisfaction."""

    pass


__all__ = [
    "SynthError",
    "ConfigurationError",
    "InputError",
    "PatternError",
    "GenerationError",
    "ValidationError",
    "OutputError",
    "FileFormatError",
    "SchemaError",
    "ConstraintError",
]
