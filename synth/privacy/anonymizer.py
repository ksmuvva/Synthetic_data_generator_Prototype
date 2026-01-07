"""
Privacy anonymization for k-anonymity and l-diversity.

Provides k-anonymity and l-diversity checking and enforcement
for privacy-preserving synthetic data generation.
"""

from dataclasses import dataclass, field
from typing import Optional, Any, list
from enum import Enum
import numpy as np
import pandas as pd


class AnonymityStatus(str, Enum):
    """Anonymity validation status."""

    ANONYMIZED = "anonymized"
    NOT_ANONYMIZED = "not_anonymized"
    PARTIALLY_ANONYMIZED = "partially_anonymized"


@dataclass
class QuasiIdentifier:
    """Quasi-identifier field for anonymity checking."""

    field_name: str
    weight: float = 1.0  # Importance weight for generalization


@dataclass
class AnonymityResult:
    """Result of anonymity validation."""

    status: AnonymityStatus
    k_value: int  # Actual k-anonymity achieved
    l_value: int = 0  # Actual l-diversity achieved

    # Violations
    violating_records: int = 0
    violation_percentage: float = 0.0

    # Recommendations
    generalizations_needed: dict[str, str] = field(default_factory=dict)


class KAnonymityChecker:
    """
    Check and enforce k-anonymity.

    Ensures each record is indistinguishable from at least k-1 others
    based on quasi-identifiers.
    """

    def __init__(self, quasi_identifiers: list[QuasiIdentifier]):
        """
        Initialize checker.

        Args:
            quasi_identifiers: List of quasi-identifier fields
        """
        self.quasi_identifiers = quasi_identifiers

    def check(self, df: pd.DataFrame, k: int) -> AnonymityResult:
        """
        Check k-anonymity.

        Args:
            df: Input dataframe
            k: Required k value

        Returns:
            AnonymityResult with validation details
        """
        # Get quasi-identifier columns
        qi_columns = [qi.field_name for qi in self.quasi_identifiers if qi.field_name in df.columns]

        if len(qi_columns) == 0:
            return AnonymityResult(
                status=AnonymityStatus.NOT_ANONYMIZED,
                k_value=1,
                violating_records=len(df),
                violation_percentage=1.0,
            )

        # Group by quasi-identifiers
        grouped = df.groupby(qi_columns).size()

        # Check k-anonymity
        violating_groups = grouped[grouped < k]
        violating_count = violating_groups.sum()

        actual_k = int(grouped.min()) if len(grouped) > 0 else 1

        if actual_k >= k:
            status = AnonymityStatus.ANONYMIZED
        elif actual_k >= k // 2:
            status = AnonymityStatus.PARTIALLY_ANONYMIZED
        else:
            status = AnonymityStatus.NOT_ANONYMIZED

        # Generate generalization recommendations
        generalizations = self._suggest_generalizations(df, qi_columns, k, violating_groups)

        return AnonymityResult(
            status=status,
            k_value=actual_k,
            violating_records=violating_count,
            violation_percentage=violating_count / len(df) if len(df) > 0 else 0.0,
            generalizations_needed=generalizations,
        )

    def _suggest_generalizations(
        self, df: pd.DataFrame, qi_columns: list[str], k: int,
        violating_groups: pd.Series
    ) -> dict[str, str]:
        """Suggest generalizations to achieve k-anonymity."""
        generalizations = {}

        for col in qi_columns:
            if pd.api.types.is_numeric_dtype(df[col]):
                # Suggest binning for numeric columns
                generalizations[col] = f"Bin into ranges (width={self._estimate_bin_width(df[col], k)})"
            elif pd.api.types.is_string_dtype(df[col]):
                # Suggest masking for string columns
                generalizations[col] = "Mask or categorize values"

        return generalizations

    def _estimate_bin_width(self, series: pd.Series, k: int) -> float:
        """Estimate bin width for numeric column."""
        # Use Freedman-Diaconis rule adjusted for k-anonymity
        iqr = series.quantile(0.75) - series.quantile(0.25)
        n = len(series)
        bin_width = 2 * iqr / (n ** (1/3))
        return max(bin_width, (series.max() - series.min()) / (n / k))


class LDiversityChecker:
    """
    Check and enforce l-diversity.

    Ensures each group of quasi-identifiers has at least l distinct
    sensitive values.
    """

    def __init__(
        self,
        quasi_identifiers: list[QuasiIdentifier],
        sensitive_column: str,
    ):
        """
        Initialize checker.

        Args:
            quasi_identifiers: List of quasi-identifier fields
            sensitive_column: Sensitive attribute to check diversity for
        """
        self.quasi_identifiers = quasi_identifiers
        self.sensitive_column = sensitive_column

    def check(self, df: pd.DataFrame, l: int) -> AnonymityResult:
        """
        Check l-diversity.

        Args:
            df: Input dataframe
            l: Required l value

        Returns:
            AnonymityResult with validation details
        """
        if self.sensitive_column not in df.columns:
            return AnonymityResult(
                status=AnonymityStatus.NOT_ANONYMIZED,
                k_value=0,
                l_value=0,
                violating_records=len(df),
                violation_percentage=1.0,
            )

        # Get quasi-identifier columns
        qi_columns = [qi.field_name for qi in self.quasi_identifiers if qi.field_name in df.columns]

        if len(qi_columns) == 0:
            return AnonymityResult(
                status=AnonymityStatus.NOT_ANONYMIZED,
                k_value=0,
                l_value=0,
                violating_records=len(df),
                violation_percentage=1.0,
            )

        # Group by quasi-identifiers and count distinct sensitive values
        grouped = df.groupby(qi_columns)[self.sensitive_column].nunique()

        # Check l-diversity
        violating_groups = grouped[grouped < l]
        violating_count = df.groupby(qi_columns).size()[violating_groups.index].sum() if len(violating_groups) > 0 else 0

        actual_l = int(grouped.min()) if len(grouped) > 0 else 1

        if actual_l >= l:
            status = AnonymityStatus.ANONYMIZED
        elif actual_l >= l // 2:
            status = AnonymityStatus.PARTIALLY_ANONYMIZED
        else:
            status = AnonymityStatus.NOT_ANONYMIZED

        return AnonymityResult(
            status=status,
            k_value=0,
            l_value=actual_l,
            violating_records=violating_count,
            violation_percentage=violating_count / len(df) if len(df) > 0 else 0.0,
        )


class DataAnonymizer:
    """
    Apply anonymization techniques to achieve privacy guarantees.

    Implements generalization, suppression, and noise injection
    for k-anonymity and differential privacy.
    """

    def __init__(self, quasi_identifiers: list[QuasiIdentifier]):
        """Initialize anonymizer."""
        self.quasi_identifiers = quasi_identifiers

    def anonymize(
        self,
        df: pd.DataFrame,
        method: str = "generalize",
        k: int = 5,
    ) -> pd.DataFrame:
        """
        Anonymize dataframe.

        Args:
            df: Input dataframe
            method: Anonymization method ('generalize', 'suppress', 'noise')
            k: Target k value

        Returns:
            Anonymized dataframe
        """
        df_anon = df.copy()

        for qi in self.quasi_identifiers:
            if qi.field_name not in df.columns:
                continue

            if method == "generalize":
                df_anon = self._generalize_column(df_anon, qi.field_name, k)
            elif method == "suppress":
                df_anon = self._suppress_column(df_anon, qi.field_name, k)
            elif method == "noise":
                df_anon = self._add_noise(df_anon, qi.field_name)

        return df_anon

    def _generalize(self, df: pd.DataFrame, column: str, k: int) -> pd.DataFrame:
        """Generalize column values."""
        if pd.api.types.is_numeric_dtype(df[column]):
            # Bin numeric values
            bins = self._create_bins(df[column], k)
            df[f"{column}_generalized"] = pd.cut(df[column], bins=bins, labels=False)
        else:
            # Categorize string values
            df[f"{column}_generalized"] = df[column].astype(str).str[:1] + "*"

        return df

    def _generalize_column(self, df: pd.DataFrame, column: str, k: int) -> pd.DataFrame:
        """Generalize a single column."""
        if pd.api.types.is_numeric_dtype(df[column]):
            # Bin numeric values
            width = self._estimate_bin_width(df[column], k)
            min_val, max_val = df[column].min(), df[column].max()
            bins = int((max_val - min_val) / width) + 1

            df[column] = pd.cut(
                df[column],
                bins=bins,
                labels=[f"{i}" for i in range(bins)],
            )
        else:
            # Partial mask for strings
            df[column] = df[column].astype(str).apply(
                lambda x: x[:1] + "*" * (len(x) - 1) if len(x) > 1 else x
            )

        return df

    def _suppress_column(self, df: pd.DataFrame, column: str, k: int) -> pd.DataFrame:
        """Suppress rare values in column."""
        value_counts = df[column].value_counts()
        rare_values = value_counts[value_counts < k].index

        df.loc[df[column].isin(rare_values), column] = "*SUPPRESSED*"

        return df

    def _add_noise(self, df: pd.DataFrame, column: str) -> pd.DataFrame:
        """Add noise to numeric column."""
        if pd.api.types.is_numeric_dtype(df[column]):
            std = df[column].std()
            noise = np.random.normal(0, 0.1 * std, len(df))
            df[column] = df[column] + noise

        return df

    def _estimate_bin_width(self, series: pd.Series, k: int) -> float:
        """Estimate bin width for numeric column."""
        iqr = series.quantile(0.75) - series.quantile(0.25)
        n = len(series)
        bin_width = 2 * iqr / (n ** (1/3))
        return max(bin_width, (series.max() - series.min()) / (n / k))
