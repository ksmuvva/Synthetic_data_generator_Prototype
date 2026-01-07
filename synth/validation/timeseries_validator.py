"""
Time-series validator for synthetic time-series data.

Validates temporal characteristics, trend preservation,
and seasonality patterns.
"""

from typing import Any, Optional
from dataclasses import dataclass, field
from enum import Enum

import numpy as np
import pandas as pd
from scipy import stats

from synth.patterns.timeseries import TimeSeriesPattern, TrendType, SeasonalityType
from synth.validation.engine import ValidationStatus, TestResult


class TimeSeriesStatus(str, Enum):
    """Time-series validation status."""

    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"


@dataclass
class TimeSeriesResult:
    """Result of time-series validation."""

    status: TimeSeriesStatus
    quality_score: float  # 0.0 to 1.0

    # Component scores
    trend_score: float = 1.0
    seasonality_score: float = 1.0
    autocorrelation_score: float = 1.0
    distribution_score: float = 1.0

    # Test results
    test_results: list[TestResult] = field(default_factory=list)

    # Recommendations
    recommendations: list[str] = field(default_factory=list)


class TimeSeriesValidator:
    """
    Validate synthetic time-series data quality.

    Checks temporal characteristics, statistical properties,
    and pattern preservation.
    """

    def __init__(
        self,
        trend_tolerance: float = 0.2,
        seasonality_tolerance: float = 0.3,
        acf_tolerance: float = 0.2,
    ):
        """
        Initialize validator.

        Args:
            trend_tolerance: Allowed deviation in trend parameters
            seasonality_tolerance: Allowed deviation in seasonality parameters
            acf_tolerance: Allowed deviation in autocorrelation
        """
        self.trend_tolerance = trend_tolerance
        self.seasonality_tolerance = seasonality_tolerance
        self.acf_tolerance = acf_tolerance

    def validate(
        self,
        synthetic: pd.DataFrame,
        reference: pd.DataFrame,
        pattern: TimeSeriesPattern,
    ) -> TimeSeriesResult:
        """
        Validate time-series quality.

        Args:
            synthetic: Generated time-series data
            reference: Original reference data
            pattern: Learned time-series pattern

        Returns:
            TimeSeriesResult with validation details
        """
        test_results = []

        # Prepare time series
        syn_ts = synthetic[pattern.column_name].values
        ref_ts = reference[pattern.column_name].values

        # 1. Validate trend preservation
        trend_result, trend_score = self._validate_trend(syn_ts, ref_ts, pattern)
        test_results.extend(trend_result)

        # 2. Validate seasonality preservation
        seasonality_result, seasonality_score = self._validate_seasonality(
            syn_ts, ref_ts, pattern
        )
        test_results.extend(seasonality_result)

        # 3. Validate autocorrelation preservation
        acf_result, acf_score = self._validate_autocorrelation(syn_ts, ref_ts, pattern)
        test_results.extend(acf_result)

        # 4. Validate distribution preservation
        dist_result, dist_score = self._validate_distribution(syn_ts, ref_ts)
        test_results.extend(dist_result)

        # Compute overall score
        weights = {
            "trend": 0.25,
            "seasonality": 0.25,
            "autocorrelation": 0.30,
            "distribution": 0.20,
        }
        overall_score = (
            trend_score * weights["trend"]
            + seasonality_score * weights["seasonality"]
            + acf_score * weights["autocorrelation"]
            + dist_score * weights["distribution"]
        )

        # Determine status
        if overall_score >= 0.85:
            status = TimeSeriesStatus.PASSED
        elif overall_score >= 0.70:
            status = TimeSeriesStatus.WARNING
        else:
            status = TimeSeriesStatus.FAILED

        # Generate recommendations
        recommendations = self._generate_recommendations(test_results, overall_score)

        return TimeSeriesResult(
            status=status,
            quality_score=overall_score,
            trend_score=trend_score,
            seasonality_score=seasonality_score,
            autocorrelation_score=acf_score,
            distribution_score=dist_score,
            test_results=test_results,
            recommendations=recommendations,
        )

    def _validate_trend(
        self, syn_ts: np.ndarray, ref_ts: np.ndarray, pattern: TimeSeriesPattern
    ) -> tuple[list[TestResult], float]:
        """Validate trend preservation."""
        results = []

        # Detect trends
        x_ref = np.arange(len(ref_ts))
        x_syn = np.arange(len(syn_ts))

        ref_slope, ref_intercept, _, _, _ = stats.linregress(x_ref, ref_ts)
        syn_slope, syn_intercept, _, _, _ = stats.linregress(x_syn, syn_ts)

        # Compare slopes
        if pattern.trend_type != TrendType.NONE:
            slope_diff = abs(syn_slope - ref_slope) / (abs(ref_slope) + 1e-10)

            if slope_diff <= self.trend_tolerance:
                status = ValidationStatus.PASS
                score = 1.0 - slope_diff
            else:
                status = ValidationStatus.FAIL
                score = max(0.0, 1.0 - slope_diff)

            results.append(
                TestResult(
                    test_name="trend_slope",
                    status=status,
                    metric=score,
                    threshold=1.0 - self.trend_tolerance,
                    message=f"Slope difference: {slope_diff:.2%} (ref: {ref_slope:.4f}, syn: {syn_slope:.4f})",
                )
            )
        else:
            # No trend expected
            score = 1.0
            results.append(
                TestResult(
                    test_name="trend_slope",
                    status=ValidationStatus.PASS,
                    metric=1.0,
                    message="No trend detected in reference",
                )
            )

        return results, score

    def _validate_seasonality(
        self, syn_ts: np.ndarray, ref_ts: np.ndarray, pattern: TimeSeriesPattern
    ) -> tuple[list[TestResult], float]:
        """Validate seasonality preservation."""
        results = []

        if pattern.seasonality_type == SeasonalityType.NONE:
            return results, 1.0

        # Compare amplitude
        ref_amp = np.std(ref_ts - np.mean(ref_ts))
        syn_amp = np.std(syn_ts - np.mean(syn_ts))

        amp_diff = abs(syn_amp - ref_amp) / (ref_amp + 1e-10)

        if amp_diff <= self.seasonality_tolerance:
            status = ValidationStatus.PASS
            score = 1.0 - amp_diff
        else:
            status = ValidationStatus.WARNING
            score = max(0.0, 1.0 - amp_diff)

        results.append(
            TestResult(
                test_name="seasonality_amplitude",
                status=status,
                metric=score,
                threshold=1.0 - self.seasonality_tolerance,
                message=f"Amplitude difference: {amp_diff:.2%} (ref: {ref_amp:.4f}, syn: {syn_amp:.4f})",
            )
        )

        return results, score

    def _validate_autocorrelation(
        self, syn_ts: np.ndarray, ref_ts: np.ndarray, pattern: TimeSeriesPattern
    ) -> tuple[list[TestResult], float]:
        """Validate autocorrelation preservation."""
        results = []

        # Compute ACF
        from statsmodels.tsa.stattools import acf

        max_lag = min(len(pattern.acf), len(syn_ts) // 4)
        if max_lag < 2:
            return results, 1.0

        ref_acf = acf(ref_ts, nlags=max_lag, alpha=None)
        syn_acf = acf(syn_ts, nlags=max_lag, alpha=None)

        # Compare ACF values
        acf_diffs = np.abs(ref_acf - syn_acf)
        mean_diff = np.mean(acf_diffs)

        if mean_diff <= self.acf_tolerance:
            status = ValidationStatus.PASS
            score = 1.0 - mean_diff
        else:
            status = ValidationStatus.WARNING
            score = max(0.0, 1.0 - mean_diff)

        results.append(
            TestResult(
                test_name="autocorrelation",
                status=status,
                metric=score,
                threshold=1.0 - self.acf_tolerance,
                message=f"Mean ACF difference: {mean_diff:.4f}",
                details={
                    "reference_acf": ref_acf.tolist(),
                    "synthetic_acf": syn_acf.tolist(),
                },
            )
        )

        return results, score

    def _validate_distribution(
        self, syn_ts: np.ndarray, ref_ts: np.ndarray
    ) -> tuple[list[TestResult], float]:
        """Validate distribution preservation."""
        results = []

        # Kolmogorov-Smirnov test
        ks_stat, ks_pvalue = stats.ks_2samp(ref_ts, syn_ts)

        if ks_pvalue > 0.05:
            status = ValidationStatus.PASS
            score = min(1.0, ks_pvalue)
        else:
            status = ValidationStatus.WARNING
            score = ks_pvalue

        results.append(
            TestResult(
                test_name="distribution_ks_test",
                status=status,
                metric=score,
                threshold=0.05,
                message=f"KS test p-value: {ks_pvalue:.4f}",
                details={"ks_statistic": ks_stat},
            )
        )

        # Compare mean and std
        mean_diff = abs(np.mean(ref_ts) - np.mean(syn_ts)) / (np.std(ref_ts) + 1e-10)
        std_diff = abs(np.std(ref_ts) - np.std(syn_ts)) / (np.std(ref_ts) + 1e-10)

        # Score based on mean and std differences
        stat_score = 1.0 - 0.5 * (mean_diff + std_diff)
        stat_score = max(0.0, stat_score)

        results.append(
            TestResult(
                test_name="statistical_moments",
                status=ValidationStatus.PASS if stat_score > 0.8 else ValidationStatus.WARNING,
                metric=stat_score,
                threshold=0.8,
                message=f"Mean diff: {mean_diff:.2%}, Std diff: {std_diff:.2%}",
            )
        )

        return results, stat_score

    def _generate_recommendations(
        self, test_results: list[TestResult], overall_score: float
    ) -> list[str]:
        """Generate recommendations based on validation results."""
        recommendations = []

        if overall_score < 0.70:
            recommendations.append("Time-series quality is below threshold. Review generation parameters.")

        for test in test_results:
            if test.status == ValidationStatus.FAIL:
                if "trend" in test.test_name:
                    recommendations.append("Trend not preserved. Consider adjusting trend parameters.")
                elif "seasonality" in test.test_name:
                    recommendations.append("Seasonality not preserved. Check seasonality period and amplitude.")
                elif "autocorrelation" in test.test_name:
                    recommendations.append("Autocorrelation pattern mismatch. Review AR/MA order.")
                elif "distribution" in test.test_name:
                    recommendations.append("Distribution mismatch. Check noise parameters.")

        return recommendations
