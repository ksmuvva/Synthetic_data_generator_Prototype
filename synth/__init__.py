"""
Synthetic Data Generator AI Agent

A CLI-based tool for generating high-quality synthetic data
through intelligent pattern learning and deterministic validation.
"""

__version__ = "0.1.0"
__author__ = "ksmuvva"
__license__ = "MIT"

from synth.config import settings
from synth.core import errors

__all__ = [
    "__version__",
    "settings",
    "errors",
]
