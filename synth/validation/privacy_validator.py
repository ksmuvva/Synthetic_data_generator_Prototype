"""
Privacy validator for synthetic data.

Validates privacy guarantees including k-anonymity,
l-diversity, and differential privacy.
"""

from dataclasses import dataclass, field
from typing import Optional, Any
from enum import Enum

import numpy as np
import pandas as pd

from synth.privacy.anonymizer import (
    KAnonymityChecker,
    LDiversityChecker,
    QuasiIdentifier,
    AnonymityResult,
)
from synth.privacy.differential_privacy import PrivacyBudget
from synth.privacy.masking import PIIRecognizer, PIIField, PIICategory
from synth.validation.engine import ValidationStatus, TestResult


class PrivacyStatus(str, Enum):
    """Privacy validation status."""

    PROTECTED = "protected"
    VULNERABLE = "vulnerable"
    WARNING = "warning"


@dataclass
class PrivacyResult:
    """Result of privacy validation."""

    status: PrivacyStatus
    privacy_score: float  # 0.0 to 1.0

    # K-anonymity results
    k_anonymity_result: Optional[AnonymityResult] = None

    # L-diversity results
    l_diversity_result: Optional[AnonymityResult] = None

    # Differential privacy results
    dp_budget_used: Optional[float] = None
    dp_budget_remaining: Optional[float] = None

    # PII leakage
    pii_leakage: list[str] = field(default_factory=list)

    # Test results
    test_results: list[TestResult] = field(default_factory=list)

    # Recommendations
    recommendations: list[str] = field(default_factory=list)


class PrivacyValidator:
    """
    Validate privacy guarantees in synthetic data.

    Checks k-anonymity, l-diversity, differential privacy,
    and PII protection.
    """

    def __init__(
        self,
        quasi_identifiers: Optional[list[QuasiIdentifier]] = None,
        sensitive_column: Optional[str] = None,
    ):
        """
        Initialize validator.

        Args:
            quasi_identifiers: List of quasi-identifier fields
            sensitive_column: Sensitive attribute for l-diversity
        """
        self.quasi_identifiers = quasi_identifiers or []
        self.sensitive_column = sensitive_column

        # Initialize checkers
        if self.quasi_identifiers:
            self.k_checker = KAnonymityChecker(self.quasi_identifiers)
        else:
            self.k_checker = None

        if self.quasi_identifiers and self.sensitive_column:
            self.l_checker = LDiversityChecker(self.quasi_identifiers, self.sensitive_column)
        else:
            self.l_checker = None

    def validate(
        self,
        synthetic: pd.DataFrame,
        k_threshold: int = 5,
        l_threshold: int = 3,
        check_pii: bool = True,
    ) -> PrivacyResult:
        """
        Validate privacy of synthetic data.

        Args:
            synthetic: Generated synthetic data
            k_threshold: Required k-anonymity value
            l_threshold: Required l-diversity value
            check_pii: Check for PII leakage

        Returns:
            PrivacyResult with validation details
        """
        test_results = []
        privacy_score = 1.0
        pii_leakage = []

        # 1. Check k-anonymity
        k_result = None
        if self.k_checker:
            k_result = self.k_checker.check(synthetic, k_threshold)

            if k_result.status.value == "not_anonymized":
                privacy_score -= 0.4
            elif k_result.status.value == "partially_anonymized":
                privacy_score -= 0.2

            test_results.append(
                TestResult(
                    test_name="k_anonymity",
                    status=self._anonymity_status_to_validation(k_result.status),
                    metric=k_result.k_value,
                    threshold=k_threshold,
                    message=f"K-anonymity: {k_result.k_value} (required: {k_threshold})",
                    details={
                        "violating_records": k_result.violating_records,
                        "violation_percentage": k_result.violation_percentage,
                    },
                )
            )

        # 2. Check l-diversity
        l_result = None
        if self.l_checker:
            l_result = self.l_checker.check(synthetic, l_threshold)

            if l_result.status.value == "not_anonymized":
                privacy_score -= 0.3
            elif l_result.status.value == "partially_anonymized":
                privacy_score -= 0.15

            test_results.append(
                TestResult(
                    test_name="l_diversity",
                    status=self._anonymity_status_to_validation(l_result.status),
                    metric=l_result.l_value,
                    threshold=l_threshold,
                    message=f"L-diversity: {l_result.l_value} (required: {l_threshold})",
                    details={
                        "violating_records": l_result.violating_records,
                        "violation_percentage": l_result.violation_percentage,
                    },
                )
            )

        # 3. Check for PII leakage
        if check_pii:
            pii_leakage = self._check_pii_leakage(synthetic)

            if pii_leakage:
                privacy_score -= 0.2

            test_results.append(
                TestResult(
                    test_name="pii_leakage",
                    status=ValidationStatus.FAIL if pii_leakage else ValidationStatus.PASS,
                    metric=1.0 - len(pii_leakage) / max(len(synthetic.columns), 1),
                    threshold=0.0,
                    message=f"PII leakage detected in {len(pii_leakage)} fields" if pii_leakage else "No PII leakage detected",
                    details={"leaked_fields": pii_leakage},
                )
            )

        # Determine overall status
        privacy_score = max(0.0, privacy_score)

        if privacy_score >= 0.85:
            status = PrivacyStatus.PROTECTED
        elif privacy_score >= 0.60:
            status = PrivacyStatus.WARNING
        else:
            status = PrivacyStatus.VULNERABLE

        # Generate recommendations
        recommendations = self._generate_recommendations(
            k_result, l_result, pii_leakage, privacy_score
        )

        return PrivacyResult(
            status=status,
            privacy_score=privacy_score,
            k_anonymity_result=k_result,
            l_diversity_result=l_result,
            pii_leakage=pii_leakage,
            test_results=test_results,
            recommendations=recommendations,
        )

    def _anonymity_status_to_validation(self, anonymity_status) -> ValidationStatus:
        """Convert anonymity status to validation status."""
        status_map = {
            "anonymized": ValidationStatus.PASS,
            "partially_anonymized": ValidationStatus.WARNING,
            "not_anonymized": ValidationStatus.FAIL,
        }
        return status_map.get(anonymity_status.value, ValidationStatus.FAIL)

    def _check_pii_leakage(self, df: pd.DataFrame) -> list[str]:
        """Check for PII leakage in synthetic data."""
        recognizer = PIIRecognizer()
        pii_fields = recognizer.recognize_fields(df)

        # Filter high-confidence PII
        leaked = [f.field_name for f in pii_fields if f.confidence > 0.7]

        return leaked

    def _generate_recommendations(
        self,
        k_result: Optional[AnonymityResult],
        l_result: Optional[AnonymityResult],
        pii_leakage: list[str],
        privacy_score: float,
    ) -> list[str]:
        """Generate privacy recommendations."""
        recommendations = []

        if privacy_score < 0.60:
            recommendations.append("Privacy score is critically low. Immediate action required.")

        # K-anonymity recommendations
        if k_result and k_result.k_value < 5:
            recommendations.append(
                f"K-anonymity not achieved (k={k_result.k_value}). "
                "Consider generalization or suppression of quasi-identifiers."
            )

            if k_result.generalizations_needed:
                recommendations.append("Suggested generalizations:")
                for field, suggestion in k_result.generalizations_needed.items():
                    recommendations.append(f"  - {field}: {suggestion}")

        # L-diversity recommendations
        if l_result and l_result.l_value < 3:
            recommendations.append(
                f"L-diversity not achieved (l={l_result.l_value}). "
                "Consider adding diversity to sensitive attributes."
            )

        # PII recommendations
        if pii_leakage:
            recommendations.append(
                f"PII leakage detected in fields: {', '.join(pii_leakage)}. "
                "Apply masking or removal."
            )

        return recommendations

    def validate_differential_privacy(
        self,
        privacy_budget: PrivacyBudget,
    ) -> list[TestResult]:
        """
        Validate differential privacy budget.

        Args:
            privacy_budget: Privacy budget to validate

        Returns:
            List of test results
        """
        results = []

        remaining_eps, remaining_delta = privacy_budget.remaining_budget()

        # Check if budget is exhausted
        if remaining_eps <= 0:
            status = ValidationStatus.FAIL
            message = f"Privacy budget exhausted: used {privacy_budget.used_epsilon:.2f}"
        elif remaining_eps < privacy_budget.epsilon * 0.1:
            status = ValidationStatus.WARNING
            message = f"Privacy budget nearly exhausted: {remaining_eps:.2f} remaining"
        else:
            status = ValidationStatus.PASS
            message = f"Privacy budget OK: {remaining_eps:.2f} / {privacy_budget.epsilon:.2f} remaining"

        results.append(
            TestResult(
                test_name="differential_privacy_budget",
                status=status,
                metric=remaining_eps / privacy_budget.epsilon,
                threshold=0.1,
                message=message,
                details={
                    "used_epsilon": privacy_budget.used_epsilon,
                    "remaining_epsilon": remaining_eps,
                    "used_delta": privacy_budget.used_delta,
                    "remaining_delta": remaining_delta,
                },
            )
        )

        return results


class MembershipInferenceValidator:
    """
    Validate resistance to membership inference attacks.

    Checks if synthetic data leaks information about
    which records were in the training set.
    """

    def __init__(self):
        """Initialize validator."""

    def validate(
        self,
        synthetic: pd.DataFrame,
        reference: pd.DataFrame,
    ) -> TestResult:
        """
        Validate resistance to membership inference.

        Args:
            synthetic: Synthetic data
            reference: Original reference data

        Returns:
            Test result
        """
        # Compute distance metrics between distributions
        syn_stats = synthetic.describe()
        ref_stats = reference.describe()

        # Compare means
        mean_diff = 0
        for col in syn_stats.columns:
            if col in ref_stats:
                mean_diff += abs(syn_stats.loc["mean", col] - ref_stats.loc["mean", col])

        mean_diff /= max(len(syn_stats.columns), 1)

        # Determine status
        if mean_diff < 0.1:
            status = ValidationStatus.WARNING
            message = f"Distributions very similar (diff: {mean_diff:.4f}). May be vulnerable to membership inference."
        else:
            status = ValidationStatus.PASS
            message = f"Distributions sufficiently different (diff: {mean_diff:.4f})."

        return TestResult(
            test_name="membership_inference_resistance",
            status=status,
            metric=mean_diff,
            threshold=0.1,
            message=message,
        )
