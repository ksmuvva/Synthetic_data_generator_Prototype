"""
Copula sampler for correlation-preserving generation.
"""

from typing import Optional
import numpy as np
import pandas as pd

from synth.patterns.correlation import CorrelationPattern, MultivariateAnalyzer
from synth.patterns.storage import Pattern
from synth.patterns.schema import FieldType
from synth.generation.sampler import StatisticalSampler


class CopulaSampler(StatisticalSampler):
    """
    Generate synthetic data preserving correlations.

    Extends StatisticalSampler to add correlation preservation
    capabilities using copula methods.
    """

    def __init__(self, seed: Optional[int] = None):
        """Initialize copula sampler."""
        super().__init__(seed=seed)
        self.correlation_analyzer = MultivariateAnalyzer()

    def generate_with_correlation(
        self,
        pattern: Pattern,
        count: int
    ) -> pd.DataFrame:
        """
        Generate synthetic data preserving learned correlations.

        Args:
            pattern: Pattern with correlation_patterns
            count: Number of records to generate

        Returns:
            DataFrame with correlated data
        """
        # Check if correlation patterns exist
        if not pattern.correlation_patterns:
            # Fallback to uncorrelated generation
            return self.generate(pattern, count)

        # Load correlation pattern
        corr_pattern = self._load_correlation_pattern(pattern)

        # Generate marginals for each field
        marginals = self._generate_marginals(pattern, count)

        # Generate correlated samples
        from synth.patterns.correlation import CopulaGenerator
        copula_gen = CopulaGenerator(seed=self.seed)
        df = copula_gen.generate(corr_pattern, marginals, count)

        # Apply constraints and validation
        df = self._enforce_constraints(pattern, df)
        self._validate_generation(df, pattern, count)

        return df

    def _load_correlation_pattern(self, pattern: Pattern) -> CorrelationPattern:
        """Load correlation pattern from Pattern."""
        from synth.patterns.correlation import CorrelationPattern, CopulaType

        corr_dict = pattern.correlation_patterns

        # Convert to CorrelationPattern object
        return CorrelationPattern(
            field_order=corr_dict["field_order"],
            correlation_matrix=np.array(corr_dict["correlation_matrix"]),
            copula_type=CopulaType(corr_dict["copula_type"]),
            quality_score=corr_dict.get("quality_score", 1.0),
            is_positive_definite=corr_dict.get("is_positive_definite", True),
            eigenvalues=np.array(corr_dict["eigenvalues"]) if "eigenvalues" in corr_dict else None,
            condition_number=corr_dict.get("condition_number"),
        )

    def _generate_marginals(
        self,
        pattern: Pattern,
        count: int
    ) -> dict[str, np.ndarray]:
        """Generate marginal distributions for each field."""
        marginals = {}

        schema_fields = pattern.schema.get("fields", [])
        numeric_fields = [
            f["name"] for f in schema_fields
            if f["type"] in ("integer", "float")
        ]

        # Generate each column independently to get marginals
        for field_name in numeric_fields:
            field_info = next(f for f in schema_fields if f["name"] == field_name)
            column_data = self._generate_column(
                pattern,
                field_name,
                FieldType(field_info["type"]),
                field_info,
                count
            )
            marginals[field_name] = np.array(column_data)

        return marginals
