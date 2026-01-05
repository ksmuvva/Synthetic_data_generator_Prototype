"""
Statistical pattern learning and distribution fitting.

Program of Thoughts:
1. Fit distributions to numeric data (normal, lognormal, exponential, uniform)
2. Learn categorical frequencies
3. Detect outliers
4. Store distribution parameters for generation
"""

from enum import Enum
from typing import Optional, Union, Tuple
from dataclasses import dataclass, field
import numpy as np
from scipy import stats
from scipy.optimize import curve_fit
import pandas as pd

from synth.core.errors import PatternError


class DistributionType(str, Enum):
    """Types of distributions for fitting."""

    NORMAL = "normal"
    LOGNORMAL = "lognormal"
    EXPONENTIAL = "exponential"
    UNIFORM = "uniform"
    BETA = "beta"
    GAMMA = "gamma"
    WEIBULL = "weibull"
    UNKNOWN = "unknown"


@dataclass
class DistributionParams:
    """Parameters for a fitted distribution."""

    dist_type: DistributionType
    params: Tuple[float, ...] = field(default_factory=tuple)
    log_likelihood: float = float("-inf")
    aic: float = float("inf")  # Akaike Information Criterion
    ks_statistic: float = 1.0
    ks_pvalue: float = 0.0


@dataclass
class NumericPattern:
    """Learned pattern for numeric field."""

    field_name: str
    distribution: DistributionParams
    outlier_method: str = "iqr"  # iqr, zscore, isolation_forest
    outlier_threshold: float = 3.0  # For z-score
    has_outliers: bool = False
    outlier_bounds: Optional[Tuple[float, float]] = None


@dataclass
class CategoricalPattern:
    """Learned pattern for categorical field."""

    field_name: str
    probabilities: dict[str, float]  # Value -> probability
    is_multimodal: bool = False
    entropy: float = 0.0


@dataclass
class StringPattern:
    """Learned pattern for string field."""

    field_name: str
    min_length: int
    max_length: int
    avg_length: float
    length_distribution: DistributionParams
    common_prefixes: list[str] = field(default_factory=list)
    common_suffixes: list[str] = field(default_factory=list)
    regex_pattern: Optional[str] = None


class UnivariateAnalyzer:
    """
    Analyze univariate patterns in data.

    Self-Reflection:
    1. Which distribution fits best?
    2. Are outliers genuine or errors?
    3. Is pattern stable across samples?
    """

    def __init__(self, significance_level: float = 0.05):
        self.significance_level = significance_level
        self._distributions_to_try = [
            DistributionType.NORMAL,
            DistributionType.LOGNORMAL,
            DistributionType.EXPONENTIAL,
            DistributionType.UNIFORM,
        ]

    def analyze_numeric(
        self, series: pd.Series, field_name: str
    ) -> NumericPattern:
        """
        Analyze numeric field and fit distributions.

        PoT Steps:
        1. Remove NaN values
        2. Try fitting each distribution
        3. Select best fit (lowest AIC)
        4. Detect outliers
        5. Validate fit quality
        """
        clean_series = series.dropna()

        if len(clean_series) < 10:
            raise PatternError(f"Insufficient data for numeric analysis: {field_name}")

        # Fit distributions
        best_fit = self._find_best_distribution(clean_series)

        # Detect outliers
        outlier_bounds, has_outliers = self._detect_outliers(clean_series)

        pattern = NumericPattern(
            field_name=field_name,
            distribution=best_fit,
            outlier_bounds=outlier_bounds,
            has_outliers=has_outliers,
        )

        # Self-reflection: Validate pattern quality
        self._validate_numeric_pattern(pattern, clean_series)

        return pattern

    def analyze_categorical(
        self, series: pd.Series, field_name: str
    ) -> CategoricalPattern:
        """
        Analyze categorical field.

        PoT Steps:
        1. Compute value frequencies
        2. Convert to probabilities
        3. Check for multimodality
        4. Compute entropy (diversity measure)
        """
        clean_series = series.dropna()

        if len(clean_series) == 0:
            raise PatternError(f"No valid data for categorical analysis: {field_name}")

        value_counts = clean_series.value_counts()
        total = len(clean_series)

        # Compute probabilities
        probabilities = {str(k): v / total for k, v in value_counts.items()}

        # Check for multimodality (multiple peaks)
        probs_list = list(probabilities.values())
        is_multimodal = self._is_multimodal(probs_list)

        # Compute entropy
        entropy = stats.entropy(probs_list)

        pattern = CategoricalPattern(
            field_name=field_name,
            probabilities=probabilities,
            is_multimodal=is_multimodal,
            entropy=entropy,
        )

        return pattern

    def analyze_string(
        self, series: pd.Series, field_name: str
    ) -> StringPattern:
        """
        Analyze string field patterns.

        PoT Steps:
        1. Compute length statistics
        2. Fit distribution to lengths
        3. Find common patterns (prefixes, suffixes)
        4. Try to infer regex pattern
        """
        clean_series = series.dropna().astype(str)

        if len(clean_series) == 0:
            raise PatternError(f"No valid data for string analysis: {field_name}")

        # Length statistics
        lengths = clean_series.str.len()
        min_len = int(lengths.min())
        max_len = int(lengths.max())
        avg_len = float(lengths.mean())

        # Fit distribution to lengths
        length_dist = self._find_best_distribution(lengths)

        # Common patterns
        prefixes = self._find_common_patterns(clean_series, prefix=True)
        suffixes = self._find_common_patterns(clean_series, prefix=False)

        # Try to infer regex (basic implementation)
        regex_pattern = self._infer_regex(clean_series)

        pattern = StringPattern(
            field_name=field_name,
            min_length=min_len,
            max_length=max_len,
            avg_length=avg_len,
            length_distribution=length_dist,
            common_prefixes=prefixes,
            common_suffixes=suffixes,
            regex_pattern=regex_pattern,
        )

        return pattern

    def _find_best_distribution(
        self, data: np.ndarray
    ) -> DistributionParams:
        """
        Find best fitting distribution.

        Returns distribution with lowest AIC.
        """
        best_fit = None
        best_aic = float("inf")

        for dist_type in self._distributions_to_try:
            try:
                fit_result = self._fit_distribution(data, dist_type)
                if fit_result.aic < best_aic:
                    best_aic = fit_result.aic
                    best_fit = fit_result
            except (ValueError, RuntimeError):
                continue

        # Fallback to normal if nothing fits
        if best_fit is None:
            best_fit = self._fit_normal(data)

        return best_fit

    def _fit_distribution(
        self, data: np.ndarray, dist_type: DistributionType
    ) -> DistributionParams:
        """Fit a specific distribution to data."""
        data = data.astype(float)

        if dist_type == DistributionType.NORMAL:
            return self._fit_normal(data)
        elif dist_type == DistributionType.LOGNORMAL:
            return self._fit_lognormal(data)
        elif dist_type == DistributionType.EXPONENTIAL:
            return self._fit_exponential(data)
        elif dist_type == DistributionType.UNIFORM:
            return self._fit_uniform(data)
        else:
            return self._fit_normal(data)

    def _fit_normal(self, data: np.ndarray) -> DistributionParams:
        """Fit normal distribution."""
        mu, sigma = stats.norm.fit(data)
        params = (mu, sigma)

        # Compute log-likelihood
        log_likelihood = np.sum(stats.norm.logpdf(data, mu, sigma))

        # KS test
        ks_stat, ks_pvalue = stats.kstest(data, lambda x: stats.norm.cdf(x, mu, sigma))

        # AIC = 2k - 2ln(L) where k=2 for normal (mean, std)
        aic = 2 * 2 - 2 * log_likelihood

        return DistributionParams(
            dist_type=DistributionType.NORMAL,
            params=params,
            log_likelihood=log_likelihood,
            aic=aic,
            ks_statistic=ks_stat,
            ks_pvalue=ks_pvalue,
        )

    def _fit_lognormal(self, data: np.ndarray) -> DistributionParams:
        """Fit lognormal distribution."""
        # Filter positive values only
        positive_data = data[data > 0]
        if len(positive_data) < 10:
            raise ValueError("Insufficient positive data for lognormal fit")

        shape, loc, scale = stats.lognorm.fit(positive_data)
        params = (shape, loc, scale)

        log_likelihood = np.sum(
            stats.lognorm.logpdf(positive_data, shape, loc=loc, scale=scale)
        )

        ks_stat, ks_pvalue = stats.kstest(
            positive_data, lambda x: stats.lognorm.cdf(x, shape, loc=loc, scale=scale)
        )

        aic = 2 * 3 - 2 * log_likelihood

        return DistributionParams(
            dist_type=DistributionType.LOGNORMAL,
            params=params,
            log_likelihood=log_likelihood,
            aic=aic,
            ks_statistic=ks_stat,
            ks_pvalue=ks_pvalue,
        )

    def _fit_exponential(self, data: np.ndarray) -> DistributionParams:
        """Fit exponential distribution."""
        loc, scale = stats.expon.fit(data)
        params = (loc, scale)

        log_likelihood = np.sum(stats.expon.logpdf(data, loc=loc, scale=scale))

        ks_stat, ks_pvalue = stats.kstest(
            data, lambda x: stats.expon.cdf(x, loc=loc, scale=scale)
        )

        aic = 2 * 2 - 2 * log_likelihood

        return DistributionParams(
            dist_type=DistributionType.EXPONENTIAL,
            params=params,
            log_likelihood=log_likelihood,
            aic=aic,
            ks_statistic=ks_stat,
            ks_pvalue=ks_pvalue,
        )

    def _fit_uniform(self, data: np.ndarray) -> DistributionParams:
        """Fit uniform distribution."""
        loc = np.min(data)
        scale = np.max(data) - loc
        params = (loc, scale)

        log_likelihood = np.sum(stats.uniform.logpdf(data, loc=loc, scale=scale))

        ks_stat, ks_pvalue = stats.kstest(
            data, lambda x: stats.uniform.cdf(x, loc=loc, scale=scale)
        )

        aic = 2 * 2 - 2 * log_likelihood

        return DistributionParams(
            dist_type=DistributionType.UNIFORM,
            params=params,
            log_likelihood=log_likelihood,
            aic=aic,
            ks_statistic=ks_stat,
            ks_pvalue=ks_pvalue,
        )

    def _detect_outliers(
        self, data: pd.Series, method: str = "iqr"
    ) -> Tuple[Optional[Tuple[float, float]], bool]:
        """
        Detect outliers using specified method.
        Returns (bounds, has_outliers)
        """
        if method == "iqr":
            Q1 = data.quantile(0.25)
            Q3 = data.quantile(0.75)
            IQR = Q3 - Q1
            lower = Q1 - 1.5 * IQR
            upper = Q3 + 1.5 * IQR
            has_outliers = ((data < lower) | (data > upper)).any()
            return (lower, upper), has_outliers

        elif method == "zscore":
            mean = data.mean()
            std = data.std()
            z_scores = np.abs((data - mean) / std)
            has_outliers = (z_scores > 3.0).any()
            return None, has_outliers

        return None, False

    def _is_multimodal(self, probabilities: list[float], threshold: float = 0.2) -> bool:
        """Check if distribution is multimodal."""
        sorted_probs = sorted(probabilities, reverse=True)
        if len(sorted_probs) < 2:
            return False
        # Check if second peak is significant
        return sorted_probs[1] / sorted_probs[0] > threshold

    def _find_common_patterns(
        self, series: pd.Series, prefix: bool = True, top_n: int = 5
    ) -> list[str]:
        """Find common prefixes or suffixes."""
        patterns = {}
        for value in series:
            value = str(value)
            if prefix and len(value) > 2:
                pattern = value[:3]
            elif not prefix and len(value) > 2:
                pattern = value[-3:]
            else:
                continue
            patterns[pattern] = patterns.get(pattern, 0) + 1

        # Sort by frequency
        sorted_patterns = sorted(patterns.items(), key=lambda x: x[1], reverse=True)
        return [p[0] for p in sorted_patterns[:top_n]]

    def _infer_regex(self, series: pd.Series) -> Optional[str]:
        """
        Infer a basic regex pattern from strings.
        Simplified implementation.
        """
        # Very basic pattern detection
        sample = str(series.iloc[0]) if len(series) > 0 else ""

        # Email pattern
        if "@" in sample and "." in sample:
            return r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

        # UUID-like pattern
        if len(sample) == 36 and sample.count("-") == 4:
            return r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"

        # Numeric ID pattern
        if sample.isdigit():
            return r"^\d+$"

        return None

    def _validate_numeric_pattern(
        self, pattern: NumericPattern, data: pd.Series
    ) -> None:
        """
        Validate numeric pattern quality.

        Self-Reflection: Is the pattern good enough for generation?
        """
        # Check KS test p-value
        if pattern.distribution.ks_pvalue < self.significance_level:
            # Distribution doesn't fit well, but we'll use it anyway
            # Could try other distributions or warn user
            pass

        # Check for too many outliers
        outlier_count = 0
        if pattern.outlier_bounds:
            lower, upper = pattern.outlier_bounds
            outlier_count = ((data < lower) | (data > upper)).sum()

        if outlier_count / len(data) > 0.1:
            # More than 10% outliers - might indicate issue
            pass
