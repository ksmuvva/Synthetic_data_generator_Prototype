"""
Schema inference and field type detection.

Program of Thoughts:
1. Detect data types from sample values
2. Handle nullable fields
3. Infer constraints (min, max, unique, patterns)
4. Validate schema consistency
"""

from enum import Enum
from typing import Any, Optional, Union
from dataclasses import dataclass, field
import re
from datetime import datetime
import pandas as pd
import numpy as np

from synth.core.errors import SchemaError


class FieldType(str, Enum):
    """Supported field types."""

    INTEGER = "integer"
    FLOAT = "float"
    STRING = "string"
    BOOLEAN = "boolean"
    DATETIME = "datetime"
    CATEGORICAL = "categorical"
    UNKNOWN = "unknown"


@dataclass
class FieldConstraints:
    """Constraints for a field."""

    min: Optional[Union[int, float]] = None
    max: Optional[Union[int, float]] = None
    pattern: Optional[str] = None  # Regex pattern
    unique: bool = False
    nullable: bool = True
    enum: Optional[list[Any]] = None  # Valid categorical values
    format: Optional[str] = None  # Date format, etc.


@dataclass
class Field:
    """Field definition with type and statistics."""

    name: str
    type: FieldType
    nullable: bool = True
    unique: bool = False
    constraints: FieldConstraints = field(default_factory=FieldConstraints)

    # Computed statistics
    null_count: int = 0
    null_percentage: float = 0.0
    unique_count: int = 0
    sample_values: list[Any] = field(default_factory=list)

    # For numeric fields
    mean: Optional[float] = None
    std: Optional[float] = None
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    median: Optional[float] = None
    quartiles: Optional[tuple[float, float, float]] = None  # Q1, Q2, Q3

    # For categorical fields
    value_counts: Optional[dict[str, int]] = None
    mode: Optional[Any] = None

    # For string fields
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    avg_length: Optional[float] = None

    def __post_init__(self):
        """Compute null percentage after initialization."""
        # Null percentage is already set during field inference
        # This method is kept for potential future use
        pass


@dataclass
class Schema:
    """Schema definition for a dataset."""

    fields: list[Field] = field(default_factory=list)
    row_count: int = 0
    inferred_at: Optional[datetime] = None

    def add_field(self, field: Field) -> None:
        """Add a field to the schema."""
        self.fields.append(field)

    def get_field(self, name: str) -> Optional[Field]:
        """Get a field by name."""
        for f in self.fields:
            if f.name == name:
                return f
        return None

    def get_numeric_fields(self) -> list[Field]:
        """Get all numeric fields."""
        return [f for f in self.fields if f.type in (FieldType.INTEGER, FieldType.FLOAT)]

    def get_categorical_fields(self) -> list[Field]:
        """Get all categorical fields."""
        return [f for f in self.fields if f.type == FieldType.CATEGORICAL]

    def get_string_fields(self) -> list[Field]:
        """Get all string fields."""
        return [f for f in self.fields if f.type == FieldType.STRING]


class SchemaInferrer:
    """
    Infer schema from DataFrame.

    Self-Reflection Questions:
    1. Is the data type detection accurate?
    2. Are nullable fields correctly identified?
    3. Are constraints reasonable?
    4. Edge cases handled?
    """

    def __init__(
        self,
        sample_size: int = 10000,
        categorical_threshold: int = 50,  # Max unique values for categorical
        null_threshold: float = 0.5,  # Max null percentage for valid field
    ):
        self.sample_size = sample_size
        self.categorical_threshold = categorical_threshold
        self.null_threshold = null_threshold

    def infer(self, df: pd.DataFrame) -> Schema:
        """
        Infer schema from DataFrame.

        Args:
            df: Input DataFrame

        Returns:
            Inferred Schema
        """
        if df.empty:
            raise SchemaError("Cannot infer schema from empty DataFrame")

        schema = Schema(row_count=len(df), inferred_at=datetime.now())

        # Sample data for faster processing
        sample_df = df if len(df) < self.sample_size else df.sample(self.sample_size)

        for column in df.columns:
            field = self._infer_field(df[column], sample_df[column], column)
            if field is not None:
                schema.add_field(field)

        # Self-reflection: Check schema quality
        self._validate_schema(schema, df)

        return schema

    def _infer_field(
        self, series: pd.Series, sample_series: pd.Series, name: str
    ) -> Optional[Field]:
        """
        Infer field type and statistics.

        PoT Steps:
        1. Check null percentage
        2. Detect dtype
        3. Compute statistics based on type
        4. Infer constraints
        """
        null_count = series.isna().sum()
        null_pct = null_count / len(series)

        # Skip fields with too many nulls
        if null_pct > self.null_threshold:
            return None

        non_null_series = series.dropna()
        field_type = self._detect_field_type(non_null_series)

        field = Field(
            name=name,
            type=field_type,
            nullable=null_count > 0,
            null_count=int(null_count),
            null_percentage=float(null_pct),
            unique_count=non_null_series.nunique(),
        )

        # Compute statistics based on type
        if field_type == FieldType.INTEGER:
            self._compute_numeric_stats(field, non_null_series)
        elif field_type == FieldType.FLOAT:
            self._compute_numeric_stats(field, non_null_series)
        elif field_type == FieldType.CATEGORICAL:
            self._compute_categorical_stats(field, non_null_series)
        elif field_type == FieldType.STRING:
            self._compute_string_stats(field, non_null_series)
        elif field_type == FieldType.BOOLEAN:
            self._compute_boolean_stats(field, non_null_series)
        elif field_type == FieldType.DATETIME:
            self._compute_datetime_stats(field, non_null_series)

        # Infer constraints
        field.constraints = self._infer_constraints(field, non_null_series)
        # Update field.unique from constraints
        field.unique = field.constraints.unique

        # Sample values
        field.sample_values = non_null_series.head(5).tolist()

        return field

    def _detect_field_type(self, series: pd.Series) -> FieldType:
        """
        Detect field type from series.

        Detection logic:
        1. Check pandas dtype first
        2. For object dtype, try to infer actual type
        3. Consider cardinality for categorical (but be smarter about integers)
        """
        dtype = series.dtype

        # Numeric types
        if pd.api.types.is_integer_dtype(dtype):
            # For integers, check if they look like categories
            # If the ratio of unique values to total values is very low AND values repeat,
            # it's likely categorical. Otherwise treat as integer.
            n_unique = series.nunique()
            total = len(series)
            unique_ratio = n_unique / total if total > 0 else 0

            # Categorical if: very few unique values OR low unique ratio with repetitions
            if n_unique <= 10 or (unique_ratio < 0.05 and n_unique < total):
                # Additional check: do values repeat? (look for repetition pattern)
                value_counts = series.value_counts()
                if value_counts.max() > 1:  # At least one value repeats
                    return FieldType.CATEGORICAL

            return FieldType.INTEGER
        elif pd.api.types.is_float_dtype(dtype):
            return FieldType.FLOAT
        elif pd.api.types.is_bool_dtype(dtype):
            return FieldType.BOOLEAN
        elif pd.api.types.is_datetime64_any_dtype(dtype):
            return FieldType.DATETIME

        # Object dtype - need to infer
        if dtype == "object":
            # Check if boolean-like first
            unique_vals = set(series.dropna().unique())
            if unique_vals <= {"true", "false", "True", "False", "T", "F", "1", "0", "yes", "no", "Y", "N"}:
                return FieldType.BOOLEAN

            # Try to convert to numeric
            try:
                numeric_series = pd.to_numeric(series, errors="coerce")
                if numeric_series.notna().sum() > len(series) * 0.8:  # 80% convertible
                    n_unique = series.nunique()
                    total = len(series)
                    unique_ratio = n_unique / total if total > 0 else 0
                    if n_unique <= 10 or (unique_ratio < 0.05 and n_unique < total):
                        return FieldType.CATEGORICAL
                    return FieldType.FLOAT if series.dtype == float else FieldType.INTEGER
            except (ValueError, TypeError):
                pass

            # Try datetime - but require high success rate
            try:
                datetime_series = pd.to_datetime(series, errors="coerce")
                # Only consider as datetime if 90%+ convert successfully
                if datetime_series.notna().sum() > len(series) * 0.9:
                    return FieldType.DATETIME
            except (ValueError, TypeError):
                pass

            # Check if categorical (low cardinality relative to length)
            n_unique = series.nunique()
            if n_unique <= self.categorical_threshold or n_unique < len(series) * 0.05:
                return FieldType.CATEGORICAL

            return FieldType.STRING

        return FieldType.UNKNOWN

    def _compute_numeric_stats(self, field: Field, series: pd.Series) -> None:
        """Compute statistics for numeric fields."""
        field.mean = float(series.mean())
        field.std = float(series.std())
        field.min_value = float(series.min())
        field.max_value = float(series.max())
        field.median = float(series.median())
        field.quartiles = (
            float(series.quantile(0.25)),
            float(series.quantile(0.50)),
            float(series.quantile(0.75)),
        )

    def _compute_categorical_stats(self, field: Field, series: pd.Series) -> None:
        """Compute statistics for categorical fields."""
        value_counts = series.value_counts()
        field.value_counts = value_counts.head(20).to_dict()
        field.mode = value_counts.index[0]

    def _compute_string_stats(self, field: Field, series: pd.Series) -> None:
        """Compute statistics for string fields."""
        lengths = series.str.len()
        field.min_length = int(lengths.min())
        field.max_length = int(lengths.max())
        field.avg_length = float(lengths.mean())

    def _compute_boolean_stats(self, field: Field, series: pd.Series) -> None:
        """Compute statistics for boolean fields."""
        value_counts = series.value_counts()
        field.value_counts = value_counts.to_dict()

    def _compute_datetime_stats(self, field: Field, series: pd.Series) -> None:
        """Compute statistics for datetime fields."""
        field.min_value = series.min()
        field.max_value = series.max()

    def _infer_constraints(self, field: Field, series: pd.Series) -> FieldConstraints:
        """Infer constraints for a field."""
        is_unique = field.unique_count == len(series)

        constraints = FieldConstraints(nullable=field.nullable, unique=is_unique)

        if field.type in (FieldType.INTEGER, FieldType.FLOAT):
            constraints.min = field.min_value
            constraints.max = field.max_value

        # For categorical, store enum values
        if field.type == FieldType.CATEGORICAL and field.value_counts:
            constraints.enum = list(field.value_counts.keys())

        return constraints

    def _validate_schema(self, schema: Schema, df: pd.DataFrame) -> None:
        """
        Validate inferred schema.

        Self-Reflection: Check for potential issues
        """
        issues = []

        # Check for fields with all nulls
        for field in schema.fields:
            if field.null_percentage >= 0.99:
                issues.append(f"Field '{field.name}' is 99%+ null")

        # Check for no valid fields
        if len(schema.fields) == 0:
            issues.append("No valid fields could be inferred")

        if issues:
            # Log warnings but don't fail
            for issue in issues:
                print(f"[yellow]Warning:[/yellow] {issue}")
