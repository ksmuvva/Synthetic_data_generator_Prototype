"""
Unit tests for schema inference module.

Self-Reflection Loop:
1. Write test
2. Run test
3. If fails, debug and fix
4. Refactor if needed
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime

from synth.patterns.schema import (
    SchemaInferrer,
    Schema,
    Field,
    FieldType,
    FieldConstraints,
)
from synth.core.errors import SchemaError


class TestSchemaInferrer:
    """Test schema inference functionality."""

    @pytest.fixture
    def inferrer(self):
        """Create a schema inferrer."""
        return SchemaInferrer()

    @pytest.fixture
    def sample_numeric_df(self):
        """Create a sample DataFrame with numeric data."""
        return pd.DataFrame({
            "age": [25, 30, 35, 40, 45, 50, 55, 60, 65, 70],
            "salary": [50000.0, 60000.0, 70000.0, 80000.0, 90000.0,
                      100000.0, 110000.0, 120000.0, 130000.0, 140000.0],
            "score": [1, 2, 3, 4, 5, 1, 2, 3, 4, 5],
        })

    @pytest.fixture
    def sample_mixed_df(self):
        """Create a sample DataFrame with mixed types."""
        return pd.DataFrame({
            "id": [1, 2, 3, 4, 5],
            "name": ["Alice", "Bob", "Charlie", "Diana", "Eve"],
            "age": [25, 30, 35, 40, 45],
            "email": ["alice@example.com", "bob@example.com", "charlie@example.com",
                     "diana@example.com", "eve@example.com"],
            "active": [True, True, False, True, False],
            "category": ["A", "B", "A", "B", "A"],
        })

    @pytest.fixture
    def sample_with_nulls_df(self):
        """Create a DataFrame with null values."""
        return pd.DataFrame({
            "col1": [1, 2, None, 4, 5],
            "col2": [1.1, 2.2, 3.3, None, 5.5],
            "col3": ["a", "b", None, "d", "e"],
        })

    def test_infer_numeric_schema(self, inferrer, sample_numeric_df):
        """Test schema inference for numeric data."""
        schema = inferrer.infer(sample_numeric_df)

        assert schema.row_count == 10
        assert len(schema.fields) == 3

        # Check age field
        age_field = schema.get_field("age")
        assert age_field is not None
        assert age_field.type == FieldType.INTEGER
        assert age_field.mean == pytest.approx(47.5, rel=0.1)
        assert age_field.min_value == 25
        assert age_field.max_value == 70

        # Check salary field
        salary_field = schema.get_field("salary")
        assert salary_field is not None
        assert salary_field.type == FieldType.FLOAT
        assert salary_field.mean == pytest.approx(95000.0, rel=0.1)

    def test_infer_mixed_schema(self, inferrer, sample_mixed_df):
        """Test schema inference for mixed types."""
        schema = inferrer.infer(sample_mixed_df)

        assert len(schema.fields) == 6

        # Check integer field
        id_field = schema.get_field("id")
        assert id_field.type == FieldType.INTEGER

        # Check string field (may be categorical due to low cardinality)
        name_field = schema.get_field("name")
        assert name_field.type in (FieldType.STRING, FieldType.CATEGORICAL)

        # Check boolean field
        active_field = schema.get_field("active")
        assert active_field.type == FieldType.BOOLEAN

        # Check categorical field
        category_field = schema.get_field("category")
        # Should be categorical (low cardinality)
        assert category_field.type in (FieldType.CATEGORICAL, FieldType.STRING)

    def test_infer_with_nulls(self, inferrer, sample_with_nulls_df):
        """Test schema inference with null values."""
        schema = inferrer.infer(sample_with_nulls_df)

        # All columns should have null tracking
        col1 = schema.get_field("col1")
        assert col1 is not None
        assert col1.null_count == 1
        assert col1.null_percentage == pytest.approx(0.2, rel=0.1)
        # nullable should be True when there are nulls
        assert col1.nullable

        col2 = schema.get_field("col2")
        assert col2 is not None
        assert col2.null_count == 1
        assert col2.null_percentage == pytest.approx(0.2, rel=0.1)
        assert col2.nullable

        col3 = schema.get_field("col3")
        assert col3 is not None
        assert col3.null_count == 1
        assert col3.null_percentage == pytest.approx(0.2, rel=0.1)
        assert col3.nullable

    def test_empty_dataframe_raises_error(self, inferrer):
        """Test that empty DataFrame raises error."""
        with pytest.raises(SchemaError):
            inferrer.infer(pd.DataFrame())

    def test_field_constraints(self, inferrer, sample_numeric_df):
        """Test that field constraints are inferred."""
        schema = inferrer.infer(sample_numeric_df)

        age_field = schema.get_field("age")
        assert age_field.constraints.min == 25
        assert age_field.constraints.max == 70

    def test_unique_detection(self, inferrer):
        """Test detection of unique fields."""
        df = pd.DataFrame({
            "id": [1, 2, 3, 4, 5],
            "value": [10, 10, 10, 10, 10],
        })
        schema = inferrer.infer(df)

        id_field = schema.get_field("id")
        assert id_field.unique is True

        value_field = schema.get_field("value")
        assert value_field.unique is False


class TestFieldTypeDetection:
    """Test field type detection logic."""

    @pytest.fixture
    def inferrer(self):
        return SchemaInferrer()

    def test_detect_integer_type(self, inferrer):
        """Test integer type detection."""
        series = pd.Series([1, 2, 3, 4, 5])
        field_type = inferrer._detect_field_type(series)
        assert field_type == FieldType.INTEGER

    def test_detect_float_type(self, inferrer):
        """Test float type detection."""
        series = pd.Series([1.1, 2.2, 3.3, 4.4, 5.5])
        field_type = inferrer._detect_field_type(series)
        assert field_type == FieldType.FLOAT

    def test_detect_string_type(self, inferrer):
        """Test string type detection."""
        # Create inferrer with lower categorical threshold for this test
        test_inferrer = SchemaInferrer(categorical_threshold=5)
        # Use 8 unique values to exceed the threshold
        series = pd.Series(["hello", "world", "test", "data", "sample", "extra", "more", "values"])
        field_type = test_inferrer._detect_field_type(series)
        assert field_type == FieldType.STRING

    def test_detect_categorical_type(self, inferrer):
        """Test categorical type detection."""
        series = pd.Series(["A", "B", "A", "B", "A", "B", "A", "B"])
        field_type = inferrer._detect_field_type(series)
        assert field_type == FieldType.CATEGORICAL

    def test_detect_boolean_type(self, inferrer):
        """Test boolean type detection."""
        series = pd.Series([True, False, True, False, True])
        field_type = inferrer._detect_field_type(series)
        assert field_type == FieldType.BOOLEAN


class TestFieldStatistics:
    """Test field statistics computation."""

    @pytest.fixture
    def inferrer(self):
        return SchemaInferrer()

    def test_numeric_statistics(self, inferrer):
        """Test numeric field statistics."""
        df = pd.DataFrame({"values": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]})
        schema = inferrer.infer(df)

        field = schema.get_field("values")
        assert field.mean == pytest.approx(5.5, rel=0.1)
        assert field.std == pytest.approx(3.03, rel=0.1)
        assert field.median == pytest.approx(5.5, rel=0.1)
        assert field.quartiles == (3.25, 5.5, 7.75)

    def test_categorical_statistics(self, inferrer):
        """Test categorical field statistics."""
        df = pd.DataFrame({"cat": ["A", "A", "A", "B", "B"]})
        schema = inferrer.infer(df)

        field = schema.get_field("cat")
        assert field.value_counts is not None
        assert field.value_counts.get("A") == 3
        assert field.value_counts.get("B") == 2
        assert field.mode == "A"
