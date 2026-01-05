"""
Validation engine for synthetic data quality.

Program of Thoughts:
1. Schema validation (types, constraints)
2. Statistical tests (KS, Chi-Square)
3. Compute quality score
4. Generate validation report
"""

import numpy as np
import pandas as pd
from scipy import stats
from typing import Optional, Any
from dataclasses import dataclass, field
from enum import Enum

from synth.core.errors import ValidationError
from synth.patterns.schema import Schema, FieldType


class ValidationStatus(str, Enum):
    """Validation result status."""

    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"


@dataclass
class TestResult:
    """Result of a single validation test."""

    test_name: str
    status: ValidationStatus
    metric: Optional[float] = None
    threshold: Optional[float] = None
    message: str = ""
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationResult:
    """Complete validation result."""

    overall_status: ValidationStatus
    quality_score: float
    test_results: list[TestResult] = field(default_factory=list)

    # Component scores
    schema_score: float = 1.0
    statistical_score: float = 1.0
    constraint_score: float = 1.0

    # Recommendations
    recommendations: list[str] = field(default_factory=list)


class ValidationEngine:
    """
    Validate synthetic data quality.

    Self-Reflection:
    1. Are tests appropriate for data type?
    2. Are thresholds reasonable?
    3. Is quality score meaningful?
    """

    def __init__(
        self,
        quality_threshold: float = 0.85,
        ks_threshold: float = 0.05,  # p-value threshold
        chi2_threshold: float = 0.05,  # p-value threshold
    ):
        self.quality_threshold = quality_threshold
        self.ks_threshold = ks_threshold
        self.chi2_threshold = chi2_threshold

    def validate(
        self,
        synthetic: pd.DataFrame,
        reference: pd.DataFrame,
        schema: Optional[Schema] = None,
    ) -> ValidationResult:
        """
        Run full validation suite.

        PoT Steps:
        1. Schema validation
        2. Statistical tests
        3. Constraint validation
        4. Compute overall score
        5. Generate recommendations
        """
        test_results = []

        # 1. Schema validation
        schema_results, schema_score = self._validate_schema(
            synthetic, reference, schema
        )
        test_results.extend(schema_results)

        # 2. Statistical tests
        stat_results, stat_score = self._validate_statistical(synthetic, reference)
        test_results.extend(stat_results)

        # 3. Constraint validation
        constraint_results, constraint_score = self._validate_constraints(
            synthetic, reference
        )
        test_results.extend(constraint_results)

        # Compute overall score
        weights = {"schema": 0.25, "statistical": 0.50, "constraint": 0.25}
        overall_score = (
            schema_score * weights["schema"]
            + stat_score * weights["statistical"]
            + constraint_score * weights["constraint"]
        )

        # Determine status
        if overall_score >= self.quality_threshold:
            status = ValidationStatus.PASS
        elif overall_score >= self.quality_threshold * 0.8:
            status = ValidationStatus.WARNING
        else:
            status = ValidationStatus.FAIL

        # Generate recommendations
        recommendations = self._generate_recommendations(test_results)

        return ValidationResult(
            overall_status=status,
            quality_score=overall_score,
            test_results=test_results,
            schema_score=schema_score,
            statistical_score=stat_score,
            constraint_score=constraint_score,
            recommendations=recommendations,
        )

    def _validate_schema(
        self,
        synthetic: pd.DataFrame,
        reference: pd.DataFrame,
        schema: Optional[Schema],
    ) -> tuple[list[TestResult], float]:
        """Validate schema conformance."""
        results = []
        score = 1.0

        # Check column count
        if len(synthetic.columns) != len(reference.columns):
            results.append(
                TestResult(
                    test_name="column_count",
                    status=ValidationStatus.FAIL,
                    message=f"Column count mismatch: synthetic={len(synthetic.columns)}, reference={len(reference.columns)}",
                )
            )
            score -= 0.3
        else:
            results.append(
                TestResult(
                    test_name="column_count",
                    status=ValidationStatus.PASS,
                    metric=1.0,
                )
            )

        # Check column names
        if set(synthetic.columns) != set(reference.columns):
            results.append(
                TestResult(
                    test_name="column_names",
                    status=ValidationStatus.FAIL,
                    message="Column names don't match",
                )
            )
            score -= 0.2
        else:
            results.append(
                TestResult(
                    test_name="column_names",
                    status=ValidationStatus.PASS,
                    metric=1.0,
                )
            )

        # Check data types
        type_match_count = 0
        for col in reference.columns:
            if col in synthetic.columns:
                ref_dtype = reference[col].dtype
                syn_dtype = synthetic[col].dtype
                if ref_dtype == syn_dtype or (
                    pd.api.types.is_numeric_dtype(ref_dtype)
                    and pd.api.types.is_numeric_dtype(syn_dtype)
                ):
                    type_match_count += 1

        type_score = type_match_count / len(reference.columns) if len(reference.columns) > 0 else 0
        results.append(
            TestResult(
                test_name="data_types",
                status=ValidationStatus.PASS if type_score > 0.9 else ValidationStatus.WARNING,
                metric=type_score,
                threshold=0.9,
                message=f"{type_match_count}/{len(reference.columns)} columns match types",
            )
        )
        score *= type_score

        return results, max(0.0, score)

    def _validate_statistical(
        self, synthetic: pd.DataFrame, reference: pd.DataFrame
    ) -> tuple[list[TestResult], float]:
        """Validate statistical similarity."""
        results = []
        scores = []

        for col in reference.columns:
            if col not in synthetic.columns:
                continue

            ref_series = reference[col].dropna()
            syn_series = synthetic[col].dropna()

            if len(ref_series) == 0 or len(syn_series) == 0:
                continue

            # Numeric: KS test
            if pd.api.types.is_numeric_dtype(ref_series):
                try:
                    ks_stat, ks_pvalue = stats.ks_2samp(ref_series, syn_series)
                    passed = ks_pvalue > self.ks_threshold
                    scores.append(1.0 if passed else ks_pvalue)

                    results.append(
                        TestResult(
                            test_name=f"ks_test_{col}",
                            status=ValidationStatus.PASS if passed else ValidationStatus.FAIL,
                            metric=ks_pvalue,
                            threshold=self.ks_threshold,
                            message=f"KS p-value: {ks_pvalue:.4f}",
                            details={"statistic": ks_stat},
                        )
                    )
                except Exception as e:
                    scores.append(0.5)
                    results.append(
                        TestResult(
                            test_name=f"ks_test_{col}",
                            status=ValidationStatus.WARNING,
                            message=f"KS test failed: {str(e)}",
                        )
                    )

            # Categorical: Chi-Square test
            else:
                try:
                    # Get value counts
                    ref_counts = ref_series.value_counts()
                    syn_counts = syn_series.value_counts()

                    # Align categories
                    all_categories = set(ref_counts.index) | set(syn_counts.index)
                    for cat in all_categories:
                        if cat not in ref_counts:
                            ref_counts[cat] = 0
                        if cat not in syn_counts:
                            syn_counts[cat] = 0

                    # Perform chi-square test
                    chi2, chi2_pvalue, _, _ = stats.chi2_contingency(
                        [ref_counts.values, syn_counts.values]
                    )
                    passed = chi2_pvalue > self.chi2_threshold
                    scores.append(1.0 if passed else chi2_pvalue)

                    results.append(
                        TestResult(
                            test_name=f"chi2_test_{col}",
                            status=ValidationStatus.PASS if passed else ValidationStatus.FAIL,
                            metric=chi2_pvalue,
                            threshold=self.chi2_threshold,
                            message=f"Chi-square p-value: {chi2_pvalue:.4f}",
                            details={"statistic": chi2},
                        )
                    )
                except Exception as e:
                    scores.append(0.5)
                    results.append(
                        TestResult(
                            test_name=f"chi2_test_{col}",
                            status=ValidationStatus.WARNING,
                            message=f"Chi-square test failed: {str(e)}",
                        )
                    )

        # Average score
        avg_score = sum(scores) / len(scores) if scores else 0.5

        return results, avg_score

    def _validate_constraints(
        self, synthetic: pd.DataFrame, reference: pd.DataFrame
    ) -> tuple[list[TestResult], float]:
        """Validate constraint satisfaction."""
        results = []
        score = 1.0

        # Check range constraints
        for col in reference.columns:
            if col not in synthetic.columns:
                continue

            ref_series = reference[col].dropna()
            syn_series = synthetic[col].dropna()

            if pd.api.types.is_numeric_dtype(ref_series):
                ref_min = ref_series.min()
                ref_max = ref_series.max()
                syn_min = syn_series.min()
                syn_max = syn_series.max()

                # Check if synthetic is within reference range (with tolerance)
                tolerance = (ref_max - ref_min) * 0.1  # 10% tolerance
                in_range = (syn_min >= ref_min - tolerance) and (
                    syn_max <= ref_max + tolerance
                )

                if not in_range:
                    score -= 0.1
                    results.append(
                        TestResult(
                            test_name=f"range_{col}",
                            status=ValidationStatus.WARNING,
                            message=f"Synthetic range [{syn_min:.2f}, {syn_max:.2f}] exceeds reference [{ref_min:.2f}, {ref_max:.2f}]",
                        )
                    )

        # Check null percentages
        for col in reference.columns:
            if col not in synthetic.columns:
                continue

            ref_null_pct = reference[col].isna().sum() / len(reference)
            syn_null_pct = synthetic[col].isna().sum() / len(synthetic)

            if abs(ref_null_pct - syn_null_pct) > 0.05:  # 5% tolerance
                score -= 0.05
                results.append(
                    TestResult(
                        test_name=f"null_percentage_{col}",
                        status=ValidationStatus.WARNING,
                        message=f"Null percentage difference: {abs(ref_null_pct - syn_null_pct):.2%}",
                    )
                )

        return results, max(0.0, score)

    def _generate_recommendations(
        self, test_results: list[TestResult]
    ) -> list[str]:
        """Generate recommendations based on test results."""
        recommendations = []

        failed_tests = [t for t in test_results if t.status == ValidationStatus.FAIL]
        warning_tests = [t for t in test_results if t.status == ValidationStatus.WARNING]

        if failed_tests:
            recommendations.append(f"Address {len(failed_tests)} failed tests")

        if warning_tests:
            recommendations.append(f"Review {len(warning_tests)} warnings")

        # Specific recommendations
        for test in failed_tests:
            if "ks_test" in test.test_name:
                recommendations.append(
                    f"Distribution mismatch in {test.test_name.replace('ks_test_', '')}: consider adjusting generation parameters"
                )

        return recommendations
