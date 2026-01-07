"""
Correlation pattern learning and copula-based multivariate generation.

This module provides correlation preservation for synthetic data generation,
enabling realistic multivariate relationships between columns.
"""

from .copula import (
    CopulaType,
    CorrelationPattern,
    MultivariateAnalyzer,
    CopulaGenerator,
)

__all__ = [
    "CopulaType",
    "CorrelationPattern",
    "MultivariateAnalyzer",
    "CopulaGenerator",
]
