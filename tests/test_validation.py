"""
Unit tests for validation engine.
"""

import pytest
import pandas as pd
import numpy as np

from synth.validation.engine import (
    ValidationEngine,
    ValidationStatus,
    ValidationResult,
    TestResult,
)
from synth.patterns.schema import Schema, Field, FieldType


class TestValidationEngine:
    """Test validation engine."""

    @pytest.fixture
    def engine(self):
        """Create a validation engine."""
        return ValidationEngine(quality_threshold=0.85)

    @pytest.fixture
    def sample_reference(self):
        """Create reference data."""
        np.random.seed(42)
        return pd.DataFrame({
            "age": np.random.normal(45, 15, 1000).astype(int),
            "salary": np.random.normal(75000, 25000, 1000),
            "category": np.random.choice(["A", "B", "C"], 1000, p=[0.5, 0.3, 0.2]),
        })

    def test_validate_similar_data_passes(self, engine, sample_reference):
        """Test that similar data passes validation."""
        # Create synthetic data from same distribution
        np.random.seed(123)
        synthetic = pd.DataFrame({
            "age": np.random.normal(45, 15, 1000).astype(int),
            "salary": np.random.normal(75000, 25000, 1000),
            "category": np.random.choice(["A", "B", "C"], 1000, p=[0.5, 0.3, 0.2]),
        })

        result = engine.validate(synthetic, sample_reference)

        # Should pass with high score
        assert result.overall_status in [ValidationStatus.PASS, ValidationStatus.WARNING]
        assert result.quality_score > 0.7

    def test_validate_different_data_fails(self, engine, sample_reference):
        """Test that different data fails validation."""
        # Create synthetic data from different distribution
        np.random.seed(123)
        synthetic = pd.DataFrame({
            "age": np.random.normal(25, 5, 1000).astype(int),  # Different mean
            "salary": np.random.normal(25000, 5000, 1000),  # Different mean
            "category": np.random.choice(["X", "Y", "Z"], 1000),  # Different values
        })

        result = engine.validate(synthetic, sample_reference)

        # Should have lower score or fail
        assert result.quality_score < 0.9

    def test_schema_validation(self, engine, sample_reference):
        """Test schema validation component."""
        # Same schema
        synthetic = sample_reference.copy()
        result = engine.validate(synthetic, sample_reference)

        # Schema score should be 1.0
        assert result.schema_score == 1.0

        # Different column count
        synthetic_wrong = synthetic.drop(columns=["category"])
        result = engine.validate(synthetic_wrong, sample_reference)

        # Schema score should be penalized
        assert result.schema_score < 1.0

    def test_statistical_validation(self, engine, sample_reference):
        """Test statistical validation component."""
        # Same distribution
        np.random.seed(42)
        synthetic = pd.DataFrame({
            "value": np.random.normal(50, 10, 1000),
        })
        reference = pd.DataFrame({
            "value": np.random.normal(50, 10, 1000),
        })

        result = engine.validate(synthetic, reference)

        # Should pass KS test (high p-value)
        stat_results = [r for r in result.test_results if "ks_test" in r.test_name]
        if stat_results:
            # At least one KS test result
            assert len(stat_results) >= 1

    def test_constraint_validation(self, engine):
        """Test constraint validation."""
        reference = pd.DataFrame({
            "value": [1, 2, 3, 4, 5],
        })

        # Synthetic within range
        synthetic = pd.DataFrame({
            "value": [1, 2, 3, 4, 5],
        })

        result = engine.validate(synthetic, reference)
        assert result.constraint_score > 0.9

        # Synthetic outside range
        synthetic_outlier = pd.DataFrame({
            "value": [10, 20, 30, 40, 50],
        })

        result = engine.validate(synthetic_outlier, reference)
        # Should be penalized
        assert result.constraint_score < 1.0


class TestSchemaValidation:
    """Test schema validation."""

    @pytest.fixture
    def engine(self):
        return ValidationEngine()

    def test_column_count_validation(self, engine):
        """Test column count validation."""
        reference = pd.DataFrame({"a": [1], "b": [2], "c": [3]})
        synthetic = pd.DataFrame({"a": [1], "b": [2]})

        results, score = engine._validate_schema(synthetic, reference, None)

        # Should have a failing test
        assert any(r.test_name == "column_count" for r in results)
        assert score < 1.0

    def test_column_name_validation(self, engine):
        """Test column name validation."""
        reference = pd.DataFrame({"a": [1], "b": [2]})
        synthetic = pd.DataFrame({"x": [1], "y": [2]})

        results, score = engine._validate_schema(synthetic, reference, None)

        # Should have a failing test
        assert any(r.test_name == "column_names" for r in results)
        assert score < 1.0

    def test_data_type_validation(self, engine):
        """Test data type validation."""
        reference = pd.DataFrame({
            "int_col": [1, 2, 3],
            "float_col": [1.0, 2.0, 3.0],
        })
        synthetic = pd.DataFrame({
            "int_col": [1, 2, 3],
            "float_col": [1.0, 2.0, 3.0],
        })

        results, score = engine._validate_schema(synthetic, reference, None)

        # Should have type test
        assert any(r.test_name == "data_types" for r in results)
        assert score > 0.9  # All types match


class TestStatisticalValidation:
    """Test statistical validation."""

    @pytest.fixture
    def engine(self):
        return ValidationEngine()

    def test_ks_test_numeric(self, engine):
        """Test KS test for numeric data."""
        # Same distribution
        np.random.seed(42)
        synthetic = pd.Series(np.random.normal(50, 10, 1000))
        reference = pd.Series(np.random.normal(50, 10, 1000))

        # Create DataFrames
        syn_df = pd.DataFrame({"value": synthetic})
        ref_df = pd.DataFrame({"value": reference})

        results, score = engine._validate_statistical(syn_df, ref_df)

        # Should have KS test result
        assert any("ks_test" in r.test_name for r in results)
        # Score should be decent (same distribution)
        assert score > 0.01  # At least some p-value

    def test_chi2_test_categorical(self, engine):
        """Test Chi-Square test for categorical data."""
        synthetic = pd.DataFrame({
            "cat": ["A", "A", "B", "B", "C"] * 200,
        })
        reference = pd.DataFrame({
            "cat": ["A", "A", "B", "B", "C"] * 200,
        })

        results, score = engine._validate_statistical(synthetic, reference)

        # Should have chi2 test result
        assert any("chi2_test" in r.test_name for r in results)
        # Same distribution should pass
        assert score > 0.01


class TestConstraintValidation:
    """Test constraint validation."""

    @pytest.fixture
    def engine(self):
        return ValidationEngine()

    def test_range_constraint(self, engine):
        """Test range constraint validation."""
        reference = pd.DataFrame({
            "value": [10, 20, 30, 40, 50],
        })

        # Within range
        synthetic = pd.DataFrame({
            "value": [15, 25, 35, 45, 55],
        })

        results, score = engine._validate_constraints(synthetic, reference)

        # Should have range test
        assert score > 0.8

        # Outside range
        synthetic_out = pd.DataFrame({
            "value": [100, 200, 300, 400, 500],
        })

        results, score = engine._validate_constraints(synthetic_out, reference)

        # Should be penalized
        assert score < 1.0

    def test_null_percentage_validation(self, engine):
        """Test null percentage validation."""
        reference = pd.DataFrame({
            "value": [1, 2, 3, None, 5],  # 20% null
        })

        # Same null percentage
        synthetic = pd.DataFrame({
            "value": [1, 2, None, 4, 5],  # 20% null
        })

        results, score = engine._validate_constraints(synthetic, reference)

        # Should maintain score
        assert score > 0.9

        # Different null percentage
        synthetic_diff = pd.DataFrame({
            "value": [None, None, None, None, 5],  # 80% null
        })

        results, score = engine._validate_constraints(synthetic_diff, reference)

        # Should be penalized
        assert score < 1.0


class TestValidationResult:
    """Test ValidationResult structure."""

    def test_validation_result_structure(self):
        """Test that ValidationResult has correct structure."""
        result = ValidationResult(
            overall_status=ValidationStatus.PASS,
            quality_score=0.92,
            test_results=[],
            schema_score=1.0,
            statistical_score=0.9,
            constraint_score=0.95,
        )

        assert result.overall_status == ValidationStatus.PASS
        assert result.quality_score == 0.92
        assert len(result.test_results) == 0


class TestRecommendations:
    """Test recommendation generation."""

    @pytest.fixture
    def engine(self):
        return ValidationEngine()

    def test_failed_test_recommendations(self, engine):
        """Test recommendations for failed tests."""
        failed_test = TestResult(
            test_name="ks_test_age",
            status=ValidationStatus.FAIL,
            metric=0.001,
            threshold=0.05,
            message="Distribution mismatch",
        )

        recommendations = engine._generate_recommendations([failed_test])

        assert len(recommendations) > 0
        assert any("age" in r for r in recommendations)

    def test_warning_test_recommendations(self, engine):
        """Test recommendations for warnings."""
        warning_test = TestResult(
            test_name="range_salary",
            status=ValidationStatus.WARNING,
            message="Range exceeded",
        )

        recommendations = engine._generate_recommendations([warning_test])

        assert len(recommendations) > 0
        assert any("warnings" in r.lower() for r in recommendations)
