"""
Data quality profiling and reporting.

Provides comprehensive data quality checks and
profiling for synthetic data validation.
"""

from dataclasses import dataclass, field
from typing import Optional, Any, list
from enum import Enum
import numpy as np
import pandas as pd


class QualityStatus(str, Enum):
    """Data quality status."""

    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"


@dataclass
class QualityMetric:
    """Single quality metric."""

    name: str
    value: float
    status: QualityStatus
    threshold: float
    message: str


@dataclass
class QualityReport:
    """Comprehensive quality report."""

    overall_status: QualityStatus
    overall_score: float  # 0.0 to 1.0
    metrics: list[QualityMetric] = field(default_factory=list)

    # Category scores
    completeness_score: float = 1.0
    accuracy_score: float = 1.0
    consistency_score: float = 1.0
    validity_score: float = 1.0

    # Issues found
    issues: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)


class DataProfiler:
    """
    Profile data quality metrics.

    Computes completeness, accuracy, consistency,
    and validity metrics.
    """

    def __init__(self):
        """Initialize profiler."""

    def profile(
        self,
        df: pd.DataFrame,
        reference: Optional[pd.DataFrame] = None,
    ) -> QualityReport:
        """
        Profile data quality.

        Args:
            df: Data to profile
            reference: Optional reference for comparison

        Returns:
            QualityReport
        """
        metrics = []
        issues = []

        # Completeness metrics
        completeness = self._check_completeness(df)
        metrics.extend(completeness)

        # Consistency metrics
        consistency = self._check_consistency(df)
        metrics.extend(consistency)

        # Validity metrics
        validity = self._check_validity(df)
        metrics.extend(validity)

        # Accuracy metrics (if reference provided)
        accuracy_score = 1.0
        if reference is not None:
            accuracy = self._check_accuracy(df, reference)
            metrics.extend(accuracy)
            accuracy_score = np.mean([m.value for m in accuracy])

        # Compute category scores
        completeness_score = np.mean([m.value for m in completeness]) if completeness else 1.0
        consistency_score = np.mean([m.value for m in consistency]) if consistency else 1.0
        validity_score = np.mean([m.value for m in validity]) if validity else 1.0

        # Overall score
        overall_score = (
            completeness_score * 0.3 +
            consistency_score * 0.2 +
            validity_score * 0.2 +
            accuracy_score * 0.3
        )

        # Determine status
        if overall_score >= 0.9:
            status = QualityStatus.EXCELLENT
        elif overall_score >= 0.75:
            status = QualityStatus.GOOD
        elif overall_score >= 0.6:
            status = QualityStatus.FAIR
        else:
            status = QualityStatus.POOR

        # Generate recommendations
        recommendations = self._generate_recommendations(metrics)

        return QualityReport(
            overall_status=status,
            overall_score=overall_score,
            metrics=metrics,
            completeness_score=completeness_score,
            consistency_score=consistency_score,
            validity_score=validity_score,
            accuracy_score=accuracy_score,
            issues=issues,
            recommendations=recommendations,
        )

    def _check_completeness(self, df: pd.DataFrame) -> list[QualityMetric]:
        """Check data completeness."""
        metrics = []

        for col in df.columns:
            null_pct = df[col].isna().sum() / len(df)
            completeness = 1.0 - null_pct

            status = self._score_to_status(completeness)

            metrics.append(
                QualityMetric(
                    name=f"completeness_{col}",
                    value=completeness,
                    status=status,
                    threshold=0.95,
                    message=f"Column {col}: {completeness:.1%} complete",
                )
            )

        return metrics

    def _check_consistency(self, df: pd.DataFrame) -> list[QualityMetric]:
        """Check data consistency."""
        metrics = []

        # Check for duplicate rows
        dup_pct = df.duplicated().sum() / len(df)
        uniqueness = 1.0 - dup_pct

        metrics.append(
            QualityMetric(
                name="uniqueness",
                value=uniqueness,
                status=self._score_to_status(uniqueness),
                threshold=0.9,
                message=f"Row uniqueness: {uniqueness:.1%}",
            )
        )

        return metrics

    def _check_validity(self, df: pd.DataFrame) -> list[QualityMetric]:
        """Check data validity."""
        metrics = []

        for col in df.columns:
            # Check for infinite values in numeric columns
            if pd.api.types.is_numeric_dtype(df[col]):
                inf_pct = (np.isinf(df[col])).sum() / len(df)
                validity = 1.0 - inf_pct

                metrics.append(
                    QualityMetric(
                        name=f"validity_{col}",
                        value=validity,
                        status=self._score_to_status(validity),
                        threshold=1.0,
                        message=f"Column {col}: {validity:.1%} valid (no inf values)",
                    )
                )

        return metrics

    def _check_accuracy(
        self, df: pd.DataFrame, reference: pd.DataFrame
    ) -> list[QualityMetric]:
        """Check accuracy compared to reference."""
        metrics = []

        # Compare column distributions
        for col in df.columns:
            if col not in reference.columns:
                continue

            # Compare ranges for numeric
            if pd.api.types.is_numeric_dtype(df[col]):
                ref_min, ref_max = reference[col].min(), reference[col].max()
                syn_min, syn_max = df[col].min(), df[col].max()

                # Check if synthetic is within reference range
                in_range = (syn_min >= ref_min) and (syn_max <= ref_max)

                metrics.append(
                    QualityMetric(
                        name=f"range_accuracy_{col}",
                        value=1.0 if in_range else 0.5,
                        status=QualityStatus.GOOD if in_range else QualityStatus.FAIR,
                        threshold=1.0,
                        message=f"Column {col}: {'within' if in_range else 'outside'} reference range",
                    )
                )

        return metrics

    def _score_to_status(self, score: float) -> QualityStatus:
        """Convert score to status."""
        if score >= 0.9:
            return QualityStatus.EXCELLENT
        elif score >= 0.75:
            return QualityStatus.GOOD
        elif score >= 0.6:
            return QualityStatus.FAIR
        else:
            return QualityStatus.POOR

    def _generate_recommendations(self, metrics: list[QualityMetric]) -> list[str]:
        """Generate recommendations from metrics."""
        recommendations = []

        for metric in metrics:
            if metric.value < metric.threshold:
                recommendations.append(
                    f"Improve {metric.name}: {metric.message}"
                )

        return recommendations


class AnomalyDetector:
    """
    Detect anomalies in data.

    Identifies outliers and unusual patterns.
    """

    def __init__(self, threshold: float = 3.0):
        """
        Initialize detector.

        Args:
            threshold: Z-score threshold for anomaly detection
        """
        self.threshold = threshold

    def detect(self, df: pd.DataFrame) -> dict[str, list[int]]:
        """
        Detect anomalies in dataframe.

        Args:
            df: Input dataframe

        Returns:
            Dictionary mapping column names to lists of anomalous row indices
        """
        anomalies = {}

        for col in df.columns:
            if pd.api.types.is_numeric_dtype(df[col]):
                # Z-score method
                z_scores = np.abs((df[col] - df[col].mean()) / (df[col].std() + 1e-10))
                anomalous_rows = df.index[z_scores > self.threshold].tolist()

                if anomalous_rows:
                    anomalies[col] = anomalous_rows

        return anomalies
