"""
Data drift simulation for synthetic data.

Provides capabilities to simulate various types of data drift
in synthetic datasets.
"""

from dataclasses import dataclass, field
from typing import Optional, Any
from enum import Enum
import numpy as np
import pandas as pd


class DriftType(str, Enum):
    """Types of data drift."""

    GRADUAL = "gradual"  # Slow, gradual shift
    SUDDEN = "sudden"  # Abrupt change
    INCREMENTAL = "incremental"  # Step-wise changes
    RECURRING = "recurring"  # Cyclical patterns


@dataclass
class DriftPattern:
    """Pattern of drift to simulate."""

    field: str
    drift_type: DriftType

    # Drift parameters
    start_point: float = 0.0  # When drift starts (0.0 to 1.0)
    magnitude: float = 0.5  # How much drift to apply

    # For gradual drift
    rate: float = 0.1  # Rate of drift

    # For sudden drift
    change_point: float = 0.5  # Point where sudden change occurs

    # For recurring drift
    period: float = 0.25  # Period of recurrence


class DriftGenerator:
    """
    Generate synthetic data with drift.

    Simulates various types of drift patterns for testing
    monitoring and drift detection systems.
    """

    def __init__(self, seed: Optional[int] = None):
        """Initialize generator."""
        self.seed = seed
        if seed is not None:
            np.random.seed(seed)

    def apply_drift(
        self,
        df: pd.DataFrame,
        drift_patterns: list[DriftPattern],
    ) -> pd.DataFrame:
        """
        Apply drift patterns to dataframe.

        Args:
            df: Input dataframe
            drift_patterns: List of drift patterns to apply

        Returns:
            Dataframe with drift applied
        """
        df_drifted = df.copy()

        for pattern in drift_patterns:
            df_drifted = self._apply_single_drift(df_drifted, pattern)

        return df_drifted

    def _apply_single_drift(
        self, df: pd.DataFrame, pattern: DriftPattern
    ) -> pd.DataFrame:
        """Apply a single drift pattern."""
        n = len(df)

        if pattern.field not in df.columns:
            return df

        if pattern.drift_type == DriftType.GRADUAL:
            return self._apply_gradual_drift(df, pattern)

        elif pattern.drift_type == DriftType.SUDDEN:
            return self._apply_sudden_drift(df, pattern)

        elif pattern.drift_type == DriftType.INCREMENTAL:
            return self._apply_incremental_drift(df, pattern)

        elif pattern.drift_type == DriftType.RECURRING:
            return self._apply_recurring_drift(df, pattern)

        return df

    def _apply_gradual_drift(self, df: pd.DataFrame, pattern: DriftPattern) -> pd.DataFrame:
        """Apply gradual drift."""
        n = len(df)
        start_idx = int(n * pattern.start_point)

        for i in range(start_idx, n):
            progress = (i - start_idx) / (n - start_idx)
            drift_amount = pattern.magnitude * progress * pattern.rate

            if pd.api.types.is_numeric_dtype(df[pattern.field]):
                df.loc[i, pattern.field] += drift_amount

        return df

    def _apply_sudden_drift(self, df: pd.DataFrame, pattern: DriftPattern) -> pd.DataFrame:
        """Apply sudden drift."""
        n = len(df)
        change_idx = int(n * pattern.change_point)

        if pd.api.types.is_numeric_dtype(df[pattern.field]):
            # Apply sudden shift after change point
            shift = df[pattern.field].std() * pattern.magnitude
            df.loc[change_idx:, pattern.field] += shift

        return df

    def _apply_incremental_drift(self, df: pd.DataFrame, pattern: DriftPattern) -> pd.DataFrame:
        """Apply incremental drift."""
        n = len(df)
        start_idx = int(n * pattern.start_point)
        n_steps = 5
        step_size = (n - start_idx) // n_steps

        for step in range(n_steps):
            step_start = start_idx + step * step_size
            step_end = min(step_start + step_size, n)

            if step_end > step_start:
                shift = (step + 1) * pattern.magnitude / n_steps

                if pd.api.types.is_numeric_dtype(df[pattern.field]):
                    df.loc[step_start:step_end, pattern.field] += shift

        return df

    def _apply_recurring_drift(self, df: pd.DataFrame, pattern: DriftPattern) -> pd.DataFrame:
        """Apply recurring drift."""
        n = len(df)
        period = int(n * pattern.period)

        for i in range(n):
            cycle_position = (i % period) / period
            drift_amount = pattern.magnitude * np.sin(2 * np.pi * cycle_position)

            if pd.api.types.is_numeric_dtype(df[pattern.field]):
                df.loc[i, pattern.field] += drift_amount

        return df
