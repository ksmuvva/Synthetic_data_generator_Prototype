"""
Schema builder for user-specified patterns.

Program of Thoughts:
1. Build Schema from conversation state
2. Convert FieldSpec to Schema fields
3. Apply constraints and validation
4. Generate default patterns for user-specified schemas
5. Create Pattern objects for generation
"""

from pathlib import Path
from typing import Any, Optional
import numpy as np
import pandas as pd
from datetime import datetime

from synth.agent.state import (
    ConversationState,
    FieldSpec,
    Constraint,
)
from synth.patterns.schema import Schema, Field, FieldType
from synth.patterns.storage import Pattern, create_pattern_from_analysis
from synth.patterns.statistical import (
    NumericPattern,
    CategoricalPattern,
    StringPattern,
    DistributionParams,
    DistributionType,
)
from synth.generation.sampler import StatisticalSampler


class SchemaBuilder:
    """
    Build schemas from user specifications.

    Self-Reflection: Converts conversational requirements into
    structured Schema and Pattern objects compatible with the
    existing generation infrastructure.
    """

    # Default distributions for user-specified fields
    DEFAULT_DISTRIBUTIONS = {
        "integer": DistributionType.UNIFORM,
        "float": DistributionType.NORMAL,
        "string": None,  # No distribution, uses string patterns
        "categorical": None,  # Uses probability distribution
        "datetime": None,  # Uses date range
        "boolean": None,  # Uses binary distribution
    }

    # Default ranges for numeric fields
    DEFAULT_RANGES = {
        "age": (18, 80),
        "amount": (10, 1000),
        "price": (1, 500),
        "quantity": (1, 100),
        "salary": (30000, 150000),
        "score": (0, 100),
    }

    def __init__(self):
        """Initialize the schema builder."""
        pass

    def build_from_conversation(
        self,
        state: ConversationState,
        reference_df: Optional[pd.DataFrame] = None
    ) -> Schema:
        """
        Build Schema from conversation state.

        If reference_df is provided, use it to infer statistics.
        Otherwise, use defaults for user-specified fields.
        """
        fields = []

        for field_name, field_spec in state.fields.items():
            # Convert FieldSpec to Field
            field = self._build_field(field_name, field_spec, reference_df)
            fields.append(field)

        # Create Schema
        row_count = state.record_count or 100
        schema = Schema(
            row_count=row_count,
            fields=fields,
        )

        return schema

    def _build_field(
        self,
        name: str,
        spec: FieldSpec,
        reference_df: Optional[pd.DataFrame] = None
    ) -> Field:
        """Build a Field from FieldSpec."""
        # Map data type string to FieldType
        field_type = self._map_field_type(spec.data_type, name)

        # Get statistics from reference or use defaults
        stats = self._get_field_statistics(name, spec, field_type, reference_df)

        # Create Field
        field = Field(
            name=name,
            type=field_type,
            nullable=spec.nullable,
            unique=spec.unique,
            **stats
        )

        return field

    def _map_field_type(self, type_str: str, field_name: str) -> FieldType:
        """Map string type to FieldType enum."""
        type_str = type_str.lower() if type_str else ""

        # Direct mapping
        type_map = {
            "integer": FieldType.INTEGER,
            "int": FieldType.INTEGER,
            "float": FieldType.FLOAT,
            "double": FieldType.FLOAT,
            "decimal": FieldType.FLOAT,
            "string": FieldType.STRING,
            "str": FieldType.STRING,
            "text": FieldType.STRING,
            "categorical": FieldType.CATEGORICAL,
            "category": FieldType.CATEGORICAL,
            "datetime": FieldType.DATETIME,
            "date": FieldType.DATETIME,
            "time": FieldType.DATETIME,
            "timestamp": FieldType.DATETIME,
            "boolean": FieldType.BOOLEAN,
            "bool": FieldType.BOOLEAN,
        }

        # Try direct mapping
        if type_str in type_map:
            return type_map[type_str]

        # Infer from field name
        if "id" in field_name.lower():
            return FieldType.STRING
        if "email" in field_name.lower():
            return FieldType.STRING
        if "date" in field_name.lower() or "time" in field_name.lower():
            return FieldType.DATETIME
        if "is_" in field_name.lower() or "has_" in field_name.lower():
            return FieldType.BOOLEAN
        if "amount" in field_name.lower() or "price" in field_name.lower():
            return FieldType.FLOAT
        if "count" in field_name.lower() or "quantity" in field_name.lower():
            return FieldType.INTEGER

        # Default to string
        return FieldType.STRING

    def _get_field_statistics(
        self,
        name: str,
        spec: FieldSpec,
        field_type: FieldType,
        reference_df: Optional[pd.DataFrame] = None
    ) -> dict[str, Any]:
        """Get statistics for a field."""
        stats = {}

        # If reference DataFrame exists, extract statistics
        if reference_df is not None and name in reference_df.columns:
            return self._extract_stats_from_reference(name, reference_df, field_type)

        # Use defaults based on field type and constraints
        if field_type == FieldType.INTEGER:
            stats = self._default_integer_stats(name, spec)
        elif field_type == FieldType.FLOAT:
            stats = self._default_float_stats(name, spec)
        elif field_type == FieldType.STRING:
            stats = self._default_string_stats(name, spec)
        elif field_type == FieldType.CATEGORICAL:
            stats = self._default_categorical_stats(name, spec)
        elif field_type == FieldType.DATETIME:
            stats = self._default_datetime_stats(name, spec)
        elif field_type == FieldType.BOOLEAN:
            stats = self._default_boolean_stats(name, spec)

        return stats

    def _extract_stats_from_reference(
        self,
        name: str,
        reference_df: pd.DataFrame,
        field_type: FieldType
    ) -> dict[str, Any]:
        """Extract statistics from reference DataFrame."""
        series = reference_df[name].dropna()
        stats = {}

        if field_type in (FieldType.INTEGER, FieldType.FLOAT):
            stats["mean"] = float(series.mean())
            stats["std"] = float(series.std())
            stats["min_value"] = float(series.min())
            stats["max_value"] = float(series.max())
            stats["median"] = float(series.median())

        elif field_type == FieldType.STRING:
            stats["min_length"] = int(series.str.len().min())
            stats["max_length"] = int(series.str.len().max())
            stats["avg_length"] = float(series.str.len().mean())

        elif field_type == FieldType.CATEGORICAL:
            value_counts = series.value_counts()
            stats["value_counts"] = value_counts.to_dict()
            stats["mode"] = series.mode().iloc[0] if not series.mode().empty else None

        return stats

    def _default_integer_stats(self, name: str, spec: FieldSpec) -> dict[str, Any]:
        """Default statistics for integer fields."""
        # Check for constraint-specified range
        if "range" in spec.constraints:
            min_val, max_val = spec.constraints["range"]
        else:
            min_val, max_val = self.DEFAULT_RANGES.get(name, (1, 100))

        mean = (min_val + max_val) / 2
        std = (max_val - min_val) / 6  # Assuming 6-sigma covers most range

        return {
            "mean": mean,
            "std": std,
            "min_value": min_val,
            "max_value": max_val,
            "median": mean,
        }

    def _default_float_stats(self, name: str, spec: FieldSpec) -> dict[str, Any]:
        """Default statistics for float fields."""
        if "range" in spec.constraints:
            min_val, max_val = spec.constraints["range"]
        else:
            min_val, max_val = self.DEFAULT_RANGES.get(name, (0.0, 100.0))

        mean = (min_val + max_val) / 2
        std = (max_val - min_val) / 6

        return {
            "mean": mean,
            "std": std,
            "min_value": min_val,
            "max_value": max_val,
            "median": mean,
        }

    def _default_string_stats(self, name: str, spec: FieldSpec) -> dict[str, Any]:
        """Default statistics for string fields."""
        # Heuristics based on field name
        if "id" in name.lower():
            min_len, max_len = 8, 12
        elif "email" in name.lower():
            min_len, max_len = 15, 30
        elif "name" in name.lower():
            min_len, max_len = 5, 30
        else:
            min_len, max_len = 5, 20

        return {
            "min_length": min_len,
            "max_length": max_len,
            "avg_length": (min_len + max_len) / 2,
        }

    def _default_categorical_stats(self, name: str, spec: FieldSpec) -> dict[str, Any]:
        """Default statistics for categorical fields."""
        # Check for enum constraint
        if "enum" in spec.constraints:
            values = spec.constraints["enum"]
            return {
                "value_counts": {v: 1.0/len(values) for v in values},
                "mode": values[0] if values else None,
            }

        # Use common values based on field name
        if "country" in name.lower():
            values = ["USA", "UK", "Canada", "Germany", "France"]
        elif "currency" in name.lower():
            values = ["USD", "EUR", "GBP", "JPY"]
        elif "status" in name.lower():
            values = ["active", "inactive", "pending"]
        else:
            values = ["A", "B", "C"]

        return {
            "value_counts": {v: 1.0/len(values) for v in values},
            "mode": values[0],
        }

    def _default_datetime_stats(self, name: str, spec: FieldSpec) -> dict[str, Any]:
        """Default statistics for datetime fields."""
        # Default to current year range
        now = datetime.now()
        start = datetime(now.year, 1, 1)
        end = datetime(now.year, 12, 31)

        return {
            "min_value": start,
            "max_value": end,
        }

    def _default_boolean_stats(self, name: str, spec: FieldSpec) -> dict[str, Any]:
        """Default statistics for boolean fields."""
        return {
            "mode": True,  # Default to True
        }

    def build_pattern_from_schema(
        self,
        schema: Schema,
        pattern_id: str
    ) -> Pattern:
        """
        Build a Pattern from a Schema.

        Creates default patterns for each field based on type and statistics.
        """
        from synth.patterns.statistical import UnivariateAnalyzer
        from scipy import stats
        from synth.patterns.storage import _serialize_schema

        numeric_patterns = {}
        categorical_patterns = {}
        string_patterns = {}

        analyzer = UnivariateAnalyzer()

        for field in schema.fields:
            if field.type == FieldType.INTEGER:
                # Create default numeric pattern as dict (what sampler expects)
                dist_type = DistributionType.NORMAL
                params = (field.mean or 50, field.std or 15)

                numeric_patterns[field.name] = {
                    "field_name": field.name,
                    "distribution": {
                        "dist_type": dist_type.value,
                        "params": params,
                        "log_likelihood": 0.0,
                        "aic": 0.0,
                        "ks_statistic": 0.0,
                        "ks_pvalue": 1.0,
                    },
                    "outlier_method": "iqr",
                    "outlier_threshold": 1.5,
                    "has_outliers": False,
                    "outlier_bounds": None,
                }

            elif field.type == FieldType.FLOAT:
                # Create default numeric pattern as dict
                dist_type = DistributionType.NORMAL
                params = (field.mean or 0.0, field.std or 1.0)

                numeric_patterns[field.name] = {
                    "field_name": field.name,
                    "distribution": {
                        "dist_type": dist_type.value,
                        "params": params,
                        "log_likelihood": 0.0,
                        "aic": 0.0,
                        "ks_statistic": 0.0,
                        "ks_pvalue": 1.0,
                    },
                    "outlier_method": "iqr",
                    "outlier_threshold": 1.5,
                    "has_outliers": False,
                    "outlier_bounds": None,
                }

            elif field.type == FieldType.CATEGORICAL:
                # Create categorical pattern as dict
                probs = field.value_counts or {}
                categorical_patterns[field.name] = {
                    "field_name": field.name,
                    "probabilities": probs,
                    "is_multimodal": len(probs) > 2,
                    "entropy": 0.0,
                }

            elif field.type == FieldType.STRING:
                # Create string pattern as dict
                string_patterns[field.name] = {
                    "field_name": field.name,
                    "min_length": field.min_length or 5,
                    "max_length": field.max_length or 20,
                    "avg_length": field.avg_length or 10,
                    "length_distribution": {
                        "dist_type": DistributionType.UNIFORM.value,
                        "params": (5, 20),
                        "log_likelihood": 0.0,
                        "aic": 0.0,
                        "ks_statistic": 0.0,
                        "ks_pvalue": 1.0,
                    },
                    "common_prefixes": [],
                    "common_suffixes": [],
                    "regex_pattern": None,
                }

        # Create Pattern
        pattern = Pattern(
            pattern_id=pattern_id,
            source_files=[],  # User-specified, no source file
            learned_at=datetime.now().isoformat(),
            schema=_serialize_schema(schema),
            row_count=schema.row_count,
            numeric_patterns=numeric_patterns,
            categorical_patterns=categorical_patterns,
            string_patterns=string_patterns,
            quality_metrics={},
            version="1.0",
        )

        return pattern
