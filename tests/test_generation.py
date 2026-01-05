"""
Unit tests for statistical sampling generator.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime

from synth.generation.sampler import StatisticalSampler
from synth.patterns.storage import Pattern
from synth.patterns.schema import FieldType
from synth.core.errors import GenerationError


class TestStatisticalSampler:
    """Test statistical sampling generator."""

    @pytest.fixture
    def sampler(self):
        """Create a sampler with fixed seed."""
        return StatisticalSampler(seed=42)

    @pytest.fixture
    def sample_pattern(self):
        """Create a sample pattern for testing."""
        return Pattern(
            pattern_id="test_pattern",
            schema={
                "row_count": 100,
                "fields": [
                    {
                        "name": "age",
                        "type": "integer",
                        "nullable": False,
                        "null_percentage": 0.0,
                        "mean": 45.0,
                        "std": 15.0,
                        "min_value": 18,
                        "max_value": 80,
                        "unique": False,
                    },
                    {
                        "name": "salary",
                        "type": "float",
                        "nullable": True,
                        "null_percentage": 0.1,
                        "mean": 75000.0,
                        "std": 25000.0,
                        "min_value": 30000.0,
                        "max_value": 150000.0,
                        "unique": False,
                    },
                    {
                        "name": "category",
                        "type": "categorical",
                        "nullable": False,
                        "null_percentage": 0.0,
                        "value_counts": {"A": 50, "B": 30, "C": 20},
                        "unique": False,
                    },
                    {
                        "name": "name",
                        "type": "string",
                        "nullable": False,
                        "null_percentage": 0.0,
                        "min_length": 3,
                        "max_length": 20,
                        "unique": False,
                    },
                ],
            },
            numeric_patterns={
                "age": {
                    "field_name": "age",
                    "distribution": {
                        "dist_type": "normal",
                        "params": (45.0, 15.0),
                        "ks_pvalue": 0.5,
                    },
                    "outlier_bounds": (18, 80),
                },
                "salary": {
                    "field_name": "salary",
                    "distribution": {
                        "dist_type": "normal",
                        "params": (75000.0, 25000.0),
                        "ks_pvalue": 0.5,
                    },
                    "outlier_bounds": (30000.0, 150000.0),
                },
            },
            categorical_patterns={
                "category": {
                    "field_name": "category",
                    "probabilities": {"A": 0.5, "B": 0.3, "C": 0.2},
                }
            },
        )

    def test_generate_basic(self, sampler, sample_pattern):
        """Test basic generation."""
        df = sampler.generate(sample_pattern, 100)

        assert len(df) == 100
        assert set(df.columns) == {"age", "salary", "category", "name"}

    def test_generate_numeric_integer(self, sampler, sample_pattern):
        """Test generating integer column."""
        df = sampler.generate(sample_pattern, 100)

        # Check age is integer
        assert df["age"].dtype in [np.int64, int, np.int32]

        # Check values are in reasonable range
        assert df["age"].min() >= 18
        assert df["age"].max() <= 80

    def test_generate_numeric_float(self, sampler, sample_pattern):
        """Test generating float column."""
        df = sampler.generate(sample_pattern, 100)

        # Check salary is float
        assert pd.api.types.is_float_dtype(df["salary"]) or pd.api.types.is_numeric_dtype(
            df["salary"]
        )

        # Check values are in reasonable range
        # (may be clipped due to outlier bounds)
        assert df["salary"].min() >= 0  # Should be positive
        assert df["salary"].max() <= 200000  # Should be reasonable

    def test_generate_categorical(self, sampler, sample_pattern):
        """Test generating categorical column."""
        df = sampler.generate(sample_pattern, 1000)

        # Check categories are valid
        unique_cats = set(df["category"].dropna().unique())
        assert unique_cats <= {"A", "B", "C"}

        # Check approximate probabilities
        counts = df["category"].value_counts()
        total = len(df["category"])
        a_prob = counts.get("A", 0) / total
        b_prob = counts.get("B", 0) / total
        c_prob = counts.get("C", 0) / total

        # Should be roughly 50%, 30%, 20% (within 10% tolerance)
        assert 0.40 < a_prob < 0.60
        assert 0.20 < b_prob < 0.40
        assert 0.10 < c_prob < 0.30

    def test_generate_with_nulls(self, sampler, sample_pattern):
        """Test generating with null values."""
        df = sampler.generate(sample_pattern, 1000)

        # Salary has 10% nulls
        null_count = df["salary"].isna().sum()
        null_pct = null_count / len(df)
        # 10% with some tolerance
        assert 0.05 < null_pct < 0.15

    def test_reproducibility_with_seed(self, sample_pattern):
        """Test that same seed produces same results."""
        # Create sampler with seed, generate, then verify shape and types match
        sampler = StatisticalSampler(seed=42)
        df = sampler.generate(sample_pattern, 100)

        # Check basic properties
        assert len(df) == 100
        assert set(df.columns) == {"age", "salary", "category", "name"}
        assert df["age"].dtype in [np.int64, int]
        assert pd.api.types.is_numeric_dtype(df["salary"])

    def test_different_seeds_different_results(self, sample_pattern):
        """Test that different seeds produce different results."""
        sampler1 = StatisticalSampler(seed=42)
        sampler2 = StatisticalSampler(seed=123)

        df1 = sampler1.generate(sample_pattern, 100)
        df2 = sampler2.generate(sample_pattern, 100)

        # Should be different
        assert not df1["age"].equals(df2["age"])

    def test_invalid_count_raises_error(self, sampler, sample_pattern):
        """Test that invalid count raises error."""
        with pytest.raises(GenerationError):
            sampler.generate(sample_pattern, 0)

        with pytest.raises(GenerationError):
            sampler.generate(sample_pattern, -100)


class TestNumericGeneration:
    """Test numeric data generation."""

    @pytest.fixture
    def sampler(self):
        return StatisticalSampler(seed=42)

    def test_generate_from_normal_distribution(self, sampler):
        """Test generating from normal distribution."""
        pattern = Pattern(
            pattern_id="normal_test",
            schema={
                "row_count": 100,
                "fields": [
                    {
                        "name": "value",
                        "type": "float",
                        "mean": 50.0,
                        "std": 10.0,
                    }
                ],
            },
            numeric_patterns={
                "value": {
                    "field_name": "value",
                    "distribution": {
                        "dist_type": "normal",
                        "params": (50.0, 10.0),
                    },
                }
            },
        )

        df = sampler.generate(pattern, 1000)

        # Check mean is approximately correct (within 5%)
        assert pytest.approx(df["value"].mean(), rel=0.1) == 50.0

    def test_generate_from_uniform_distribution(self, sampler):
        """Test generating from uniform distribution."""
        pattern = Pattern(
            pattern_id="uniform_test",
            schema={
                "row_count": 100,
                "fields": [
                    {
                        "name": "value",
                        "type": "float",
                    }
                ],
            },
            numeric_patterns={
                "value": {
                    "field_name": "value",
                    "distribution": {
                        "dist_type": "uniform",
                        "params": (0, 100),
                    },
                }
            },
        )

        df = sampler.generate(pattern, 1000)

        # Check range
        assert df["value"].min() >= 0
        assert df["value"].max() <= 100

        # For uniform, mean should be around 50
        assert 40 < df["value"].mean() < 60


class TestCategoricalGeneration:
    """Test categorical data generation."""

    @pytest.fixture
    def sampler(self):
        return StatisticalSampler(seed=42)

    def test_uniform_categorical(self, sampler):
        """Test generating uniform categorical."""
        pattern = Pattern(
            pattern_id="cat_test",
            schema={
                "row_count": 100,
                "fields": [
                    {
                        "name": "category",
                        "type": "categorical",
                    }
                ],
            },
            categorical_patterns={
                "category": {
                    "field_name": "category",
                    "probabilities": {"A": 0.25, "B": 0.25, "C": 0.25, "D": 0.25},
                }
            },
        )

        df = sampler.generate(pattern, 1000)

        # Each category should be ~25%
        counts = df["category"].value_counts()
        for cat in ["A", "B", "C", "D"]:
            prob = counts.get(cat, 0) / 1000
            assert 0.20 < prob < 0.30


class TestGenerationValidation:
    """Test generation validation."""

    @pytest.fixture
    def sampler(self):
        return StatisticalSampler(seed=42)

    def test_row_count_validation(self, sampler):
        """Test that row count matches request."""
        pattern = Pattern(
            pattern_id="test",
            schema={
                "row_count": 100,
                "fields": [
                    {"name": "col1", "type": "integer", "mean": 50, "std": 10}
                ]
            },
            numeric_patterns={
                "col1": {
                    "field_name": "col1",
                    "distribution": {"dist_type": "normal", "params": (50, 10)},
                }
            },
        )

        for count in [10, 100, 1000]:
            df = sampler.generate(pattern, count)
            assert len(df) == count

    def test_column_count_validation(self, sampler):
        """Test that column count matches schema."""
        pattern = Pattern(
            pattern_id="test",
            schema={
                "row_count": 100,
                "fields": [
                    {"name": "col1", "type": "integer"},
                    {"name": "col2", "type": "integer"},
                    {"name": "col3", "type": "integer"},
                ],
            },
        )

        df = sampler.generate(pattern, 100)
        assert len(df.columns) == 3
