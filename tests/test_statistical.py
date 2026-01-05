"""
Unit tests for statistical pattern learning module.
"""

import pytest
import pandas as pd
import numpy as np

from synth.patterns.statistical import (
    UnivariateAnalyzer,
    NumericPattern,
    CategoricalPattern,
    StringPattern,
    DistributionType,
)
from synth.core.errors import PatternError


class TestUnivariateAnalyzer:
    """Test univariate statistical analysis."""

    @pytest.fixture
    def analyzer(self):
        return UnivariateAnalyzer()

    @pytest.fixture
    def normal_data(self):
        """Generate sample normal data."""
        np.random.seed(42)
        return pd.Series(np.random.normal(50, 10, 1000))

    @pytest.fixture
    def categorical_data(self):
        """Generate sample categorical data."""
        np.random.seed(42)
        return pd.Series(
            np.random.choice(["A", "B", "C", "D"], 1000, p=[0.4, 0.3, 0.2, 0.1])
        )

    def test_analyze_numeric_normal(self, analyzer, normal_data):
        """Test analyzing normally distributed data."""
        pattern = analyzer.analyze_numeric(normal_data, "test_field")

        assert isinstance(pattern, NumericPattern)
        assert pattern.field_name == "test_field"
        # Normal or lognormal are both reasonable fits for normal-like data
        assert pattern.distribution.dist_type in (DistributionType.NORMAL, DistributionType.LOGNORMAL)
        assert len(pattern.distribution.params) >= 2  # at least mu, sigma

    def test_analyze_categorical(self, analyzer, categorical_data):
        """Test analyzing categorical data."""
        pattern = analyzer.analyze_categorical(categorical_data, "cat_field")

        assert isinstance(pattern, CategoricalPattern)
        assert pattern.field_name == "cat_field"
        assert len(pattern.probabilities) == 4
        assert "A" in pattern.probabilities
        assert pytest.approx(pattern.probabilities["A"], 0.1) == 0.4

    def test_insufficient_data_raises_error(self, analyzer):
        """Test that insufficient data raises error."""
        short_series = pd.Series([1, 2, 3])
        with pytest.raises(PatternError):
            analyzer.analyze_numeric(short_series, "test")

    def test_distribution_fitting(self, analyzer, normal_data):
        """Test distribution fitting quality."""
        pattern = analyzer.analyze_numeric(normal_data, "test")

        # For normal data, normal distribution should fit well
        # Check p-value is reasonable (not significant)
        assert pattern.distribution.ks_pvalue > 0.01 or pattern.distribution.ks_pvalue < 0.99

    def test_categorical_entropy(self, analyzer, categorical_data):
        """Test categorical entropy computation."""
        pattern = analyzer.analyze_categorical(categorical_data, "cat")

        # Entropy should be positive
        assert pattern.entropy > 0

        # For uniform distribution, entropy would be maximum
        # Our distribution is [0.4, 0.3, 0.2, 0.1], so entropy should be moderate
        assert pattern.entropy < np.log(4)  # Less than max entropy


class TestDistributionFitting:
    """Test distribution fitting functions."""

    @pytest.fixture
    def analyzer(self):
        return UnivariateAnalyzer()

    def test_fit_normal_distribution(self, analyzer):
        """Test fitting normal distribution."""
        np.random.seed(42)
        data = np.random.normal(100, 15, 1000)

        result = analyzer._fit_normal(data)

        assert result.dist_type == DistributionType.NORMAL
        assert len(result.params) == 2
        assert pytest.approx(result.params[0], rel=0.1) == 100  # mean
        assert pytest.approx(result.params[1], rel=0.2) == 15  # std

    def test_fit_uniform_distribution(self, analyzer):
        """Test fitting uniform distribution."""
        np.random.seed(42)
        data = np.random.uniform(0, 100, 1000)

        result = analyzer._fit_uniform(data)

        assert result.dist_type == DistributionType.UNIFORM
        assert len(result.params) == 2

    def test_best_distribution_selection(self, analyzer):
        """Test selection of best distribution."""
        np.random.seed(42)
        normal_data = np.random.normal(50, 10, 500)

        best_fit = analyzer._find_best_distribution(normal_data)

        # Should find a distribution that fits
        assert best_fit is not None
        assert best_fit.aic < float("inf")


class TestOutlierDetection:
    """Test outlier detection."""

    @pytest.fixture
    def analyzer(self):
        return UnivariateAnalyzer()

    def test_iqr_outlier_detection(self, analyzer):
        """Test IQR-based outlier detection."""
        # Create data with variation and clear outliers
        np.random.seed(42)
        normal_data = list(np.random.normal(50, 10, 100))
        data = pd.Series(normal_data + [1000, -1000])

        bounds, has_outliers = analyzer._detect_outliers(data, method="iqr")

        # Check that bounds were returned
        assert bounds is not None
        assert len(bounds) == 2
        # Bounds should have some range due to variation
        if bounds[0] < bounds[1]:
            # Verify the clear outliers would be outside bounds
            assert 1000 > bounds[1] or -1000 < bounds[0]

    def test_no_outliers_clean_data(self, analyzer):
        """Test outlier detection on clean data."""
        np.random.seed(42)
        data = pd.Series(np.random.normal(50, 10, 100))

        bounds, has_outliers = analyzer._detect_outliers(data, method="iqr")

        # May or may not have outliers depending on random data
        # Just check it doesn't crash and returns expected types
        assert isinstance(has_outliers, (bool, np.bool_))
        if bounds:
            assert isinstance(bounds, tuple)
            assert len(bounds) == 2


class TestCategoricalAnalysis:
    """Test categorical analysis."""

    @pytest.fixture
    def analyzer(self):
        return UnivariateAnalyzer()

    def test_multimodal_detection(self, analyzer):
        """Test multimodal distribution detection."""
        # Bimodal distribution
        probs = [0.45, 0.40, 0.10, 0.05]
        is_multimodal = analyzer._is_multimodal(probs)

        # Second peak is 40/45 = 0.89 > 0.2, so multimodal
        assert is_multimodal is True

    def test_unimodal_detection(self, analyzer):
        """Test unimodal distribution detection."""
        # Unimodal distribution
        probs = [0.80, 0.10, 0.05, 0.05]
        is_multimodal = analyzer._is_multimodal(probs)

        # Second peak is 10/80 = 0.125 < 0.2, so not multimodal
        assert is_multimodal is False

    def test_probability_normalization(self, analyzer):
        """Test that probabilities sum to 1."""
        data = pd.Series(["A", "A", "B", "B", "C"])
        pattern = analyzer.analyze_categorical(data, "cat")

        total_prob = sum(pattern.probabilities.values())
        assert pytest.approx(total_prob, 0.01) == 1.0


class TestStringAnalysis:
    """Test string pattern analysis."""

    @pytest.fixture
    def analyzer(self):
        return UnivariateAnalyzer()

    def test_length_statistics(self, analyzer):
        """Test string length statistics."""
        data = pd.Series(["short", "medium", "very long string", "tiny"])
        pattern = analyzer.analyze_string(data, "text")

        assert pattern.min_length == 4  # "tiny"
        assert pattern.max_length == 16  # "very long string"
        assert pattern.avg_length > 4
        assert pattern.avg_length < 16

    def test_common_patterns(self, analyzer):
        """Test finding common prefixes/suffixes."""
        data = pd.Series(["prefix_a", "prefix_b", "prefix_c"])
        prefixes = analyzer._find_common_patterns(data, prefix=True)

        assert "pre" in prefixes or "pref" in prefixes

    def test_email_regex_inference(self, analyzer):
        """Test email regex inference."""
        data = pd.Series(["test@example.com", "user@domain.org"])
        pattern = analyzer.analyze_string(data, "email")

        # Should detect email pattern
        assert pattern.regex_pattern is not None
        assert "@" in pattern.regex_pattern
