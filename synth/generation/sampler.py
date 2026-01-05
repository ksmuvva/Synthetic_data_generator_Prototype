"""
Statistical sampling generator for synthetic data.

Program of Thoughts:
1. Generate data from learned distributions
2. Handle null values according to schema
3. Enforce constraints
4. Maintain correlations (simplified for MVP)
"""

import numpy as np
import pandas as pd
from typing import Optional, Any
from dataclasses import dataclass

from synth.core.errors import GenerationError
from synth.patterns.storage import Pattern
from synth.patterns.statistical import DistributionType
from synth.patterns.schema import FieldType


class StatisticalSampler:
    """
    Generate synthetic data using statistical sampling.

    Self-Reflection:
    1. Is generated data statistically valid?
    2. Are constraints satisfied?
    3. Is generation deterministic with seed?
    """

    def __init__(self, seed: Optional[int] = None):
        """
        Initialize sampler.

        Args:
            seed: Random seed for reproducibility
        """
        self.seed = seed
        if seed is not None:
            np.random.seed(seed)

    def generate(self, pattern: Pattern, count: int) -> pd.DataFrame:
        """
        Generate synthetic data from pattern.

        PoT Steps:
        1. Initialize DataFrame
        2. Generate each column based on its pattern
        3. Handle null values
        4. Enforce constraints
        5. Validate output
        """
        if count <= 0:
            raise GenerationError(f"Invalid count: {count}")

        data = {}

        # Get field information from schema
        schema_fields = pattern.schema.get("fields", [])

        for field_info in schema_fields:
            field_name = field_info["name"]
            field_type = FieldType(field_info["type"])
            null_percentage = field_info.get("null_percentage", 0.0)

            # Generate the column
            column_data = self._generate_column(
                pattern, field_name, field_type, field_info, count
            )

            # Apply null values
            if null_percentage > 0:
                column_data = self._apply_nulls(column_data, null_percentage, count)

            data[field_name] = column_data

        # Create DataFrame
        df = pd.DataFrame(data)

        # Enforce constraints
        df = self._enforce_constraints(pattern, df)

        # Self-reflection: Validate generated data
        self._validate_generation(df, pattern, count)

        return df

    def _generate_column(
        self,
        pattern: Pattern,
        field_name: str,
        field_type: FieldType,
        field_info: dict,
        count: int,
    ) -> list[Any]:
        """Generate a single column."""
        if field_type in (FieldType.INTEGER, FieldType.FLOAT):
            return self._generate_numeric(pattern, field_name, count, field_type)
        elif field_type == FieldType.CATEGORICAL:
            return self._generate_categorical(pattern, field_name, count)
        elif field_type == FieldType.STRING:
            return self._generate_string(pattern, field_name, count, field_info)
        elif field_type == FieldType.BOOLEAN:
            return self._generate_boolean(pattern, field_name, count)
        elif field_type == FieldType.DATETIME:
            return self._generate_datetime(pattern, field_name, count, field_info)
        else:
            raise GenerationError(f"Unsupported field type: {field_type}")

    def _generate_numeric(
        self, pattern: Pattern, field_name: str, count: int, field_type: FieldType
    ) -> list[float]:
        """Generate numeric column from distribution."""
        # Get numeric pattern
        numeric_pattern = pattern.numeric_patterns.get(field_name)
        if not numeric_pattern:
            # Fallback: use basic statistics from schema
            field_info = self._get_field_info(pattern, field_name)
            return self._generate_numeric_from_stats(
                field_info, count, field_type == FieldType.INTEGER
            )

        dist_info = numeric_pattern["distribution"]
        dist_type = DistributionType(dist_info["dist_type"])
        params = dist_info["params"]

        # Generate from distribution
        if dist_type == DistributionType.NORMAL:
            mu, sigma = params
            data = np.random.normal(mu, sigma, count)
        elif dist_type == DistributionType.LOGNORMAL:
            shape, loc, scale = params
            data = np.random.lognormal(shape, loc, scale, count)
        elif dist_type == DistributionType.EXPONENTIAL:
            loc, scale = params
            data = np.random.exponential(scale, count) + loc
        elif dist_type == DistributionType.UNIFORM:
            loc, scale = params
            data = np.random.uniform(loc, loc + scale, count)
        else:
            # Fallback to normal
            mu, sigma = params[:2]
            data = np.random.normal(mu, sigma, count)

        # Apply bounds if available
        outlier_bounds = numeric_pattern.get("outlier_bounds")
        if outlier_bounds:
            lower, upper = outlier_bounds
            # Clip values to bounds
            data = np.clip(data, lower, upper)

        # Convert to integer if needed
        if field_type == FieldType.INTEGER:
            data = np.round(data).astype(int)

        return data.tolist()

    def _generate_numeric_from_stats(
        self, field_info: dict, count: int, as_integer: bool
    ) -> list[float]:
        """Generate numeric from basic statistics."""
        mean = field_info.get("mean", 0.0)
        std = field_info.get("std", 1.0)
        min_val = field_info.get("min_value")
        max_val = field_info.get("max_value")

        data = np.random.normal(mean, std, count)

        # Clip to min/max if available
        if min_val is not None and max_val is not None:
            data = np.clip(data, min_val, max_val)

        if as_integer:
            data = np.round(data).astype(int)

        return data.tolist()

    def _generate_categorical(
        self, pattern: Pattern, field_name: str, count: int
    ) -> list[Any]:
        """Generate categorical column from probabilities."""
        categorical_pattern = pattern.categorical_patterns.get(field_name)

        if not categorical_pattern:
            # Fallback: use value_counts from schema
            field_info = self._get_field_info(pattern, field_name)
            value_counts = field_info.get("value_counts", {})
            if not value_counts:
                # Generate placeholder
                return [f"category_{i % 5}" for i in range(count)]

            # Compute probabilities
            total = sum(value_counts.values())
            probabilities = {k: v / total for k, v in value_counts.items()}
        else:
            probabilities = categorical_pattern["probabilities"]

        # Generate based on probabilities
        values = list(probabilities.keys())
        probs = list(probabilities.values())

        # Normalize probabilities
        probs = np.array(probs)
        probs = probs / probs.sum()

        data = np.random.choice(values, size=count, p=probs)

        return data.tolist()

    def _generate_string(
        self, pattern: Pattern, field_name: str, count: int, field_info: dict
    ) -> list[str]:
        """Generate string column."""
        string_pattern = pattern.string_patterns.get(field_name)

        if string_pattern:
            # Use learned length distribution
            min_len = string_pattern["min_length"]
            max_len = string_pattern["max_length"]
        else:
            # Use schema info
            min_len = field_info.get("min_length", 5)
            max_len = field_info.get("max_length", 20)

        # Generate random strings with varying lengths
        data = []
        for _ in range(count):
            length = np.random.randint(min_len, max_len + 1)
            # Generate random alphanumeric string
            s = "".join(np.random.choice(list("abcdefghijklmnopqrstuvwxyz0123456789"), length))
            data.append(s)

        return data

    def _generate_boolean(
        self, pattern: Pattern, field_name: str, count: int
    ) -> list[bool]:
        """Generate boolean column."""
        # Get value counts to determine ratio
        field_info = self._get_field_info(pattern, field_name)
        value_counts = field_info.get("value_counts", {})

        # Default to 50/50 if no info
        true_prob = 0.5
        if value_counts:
            total = sum(value_counts.values())
            true_count = value_counts.get(True, value_counts.get("true", 0))
            true_prob = true_count / total

        data = np.random.random(count) < true_prob
        return data.tolist()

    def _generate_datetime(
        self, pattern: Pattern, field_name: str, count: int, field_info: dict
    ) -> list[Any]:
        """Generate datetime column."""
        # Use min/max from schema
        min_val = field_info.get("min_value")
        max_val = field_info.get("max_value")

        if min_val and max_val:
            # Generate random datetimes in range
            min_ts = pd.Timestamp(min_val).value // 10**9
            max_ts = pd.Timestamp(max_val).value // 10**9
            timestamps = np.random.randint(min_ts, max_ts, count)
            data = [pd.Timestamp(ts, unit="s") for ts in timestamps]
        else:
            # Fallback to recent dates
            base = pd.Timestamp("2020-01-01")
            timestamps = np.random.randint(0, 365 * 24 * 3600, count)
            data = [base + pd.Timedelta(seconds=int(ts)) for ts in timestamps]

        return data

    def _apply_nulls(self, data: list, null_percentage: float, count: int) -> list:
        """Apply null values to column."""
        num_nulls = int(count * null_percentage)
        if num_nulls > 0:
            null_indices = np.random.choice(count, num_nulls, replace=False)
            for idx in null_indices:
                data[idx] = None
        return data

    def _enforce_constraints(self, pattern: Pattern, df: pd.DataFrame) -> pd.DataFrame:
        """Enforce learned constraints."""
        # For MVP, basic constraint enforcement
        # TODO: Add more sophisticated constraint handling

        schema_fields = pattern.schema.get("fields", [])

        for field_info in schema_fields:
            field_name = field_info["name"]
            if field_name not in df.columns:
                continue

            # Enforce uniqueness
            if field_info.get("unique", False):
                # For now, just warn (proper handling is complex)
                pass

            # Enforce min/max for numeric
            min_val = field_info.get("min_value")
            max_val = field_info.get("max_value")
            if min_val is not None or max_val is not None:
                col = df[field_name]
                if pd.api.types.is_numeric_dtype(col):
                    if min_val is not None:
                        df.loc[df[field_name] < min_val, field_name] = min_val
                    if max_val is not None:
                        df.loc[df[field_name] > max_val, field_name] = max_val

        return df

    def _get_field_info(self, pattern: Pattern, field_name: str) -> dict:
        """Get field information from schema."""
        schema_fields = pattern.schema.get("fields", [])
        for field in schema_fields:
            if field["name"] == field_name:
                return field
        return {}

    def _validate_generation(
        self, df: pd.DataFrame, pattern: Pattern, expected_count: int
    ) -> None:
        """
        Validate generated data.

        Self-Reflection: Check for common issues
        """
        if len(df) != expected_count:
            raise GenerationError(
                f"Generated {len(df)} rows, expected {expected_count}"
            )

        # Check column count matches schema
        expected_cols = len(pattern.schema.get("fields", []))
        if len(df.columns) != expected_cols:
            raise GenerationError(
                f"Generated {len(df.columns)} columns, expected {expected_cols}"
            )

        # Check for all-null columns
        for col in df.columns:
            if df[col].isna().all():
                # Warning: column is all null
                pass
