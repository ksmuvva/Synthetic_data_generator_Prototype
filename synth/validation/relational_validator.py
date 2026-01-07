"""
Referential integrity validator for multi-table synthetic data.

Validates foreign key constraints and relationships between tables.
"""

from typing import Any
from dataclasses import dataclass, field
from enum import Enum

import pandas as pd

from synth.patterns.relational import RelationalPattern, ForeignKeyConstraint
from synth.validation.engine import ValidationStatus, TestResult


class IntegrityStatus(str, Enum):
    """Referential integrity validation status."""

    INTEGRITY_PASSED = "passed"
    INTEGRITY_FAILED = "failed"
    INTEGRITY_WARNING = "warning"


@dataclass
class IntegrityResult:
    """Result of referential integrity validation."""

    status: IntegrityStatus
    integrity_score: float  # 0.0 to 1.0
    foreign_key_results: list["ForeignKeyResult"] = field(default_factory=list)

    # Summary statistics
    total_fks: int = 0
    valid_fks: int = 0
    total_violations: int = 0

    # Recommendations
    recommendations: list[str] = field(default_factory=list)


@dataclass
class ForeignKeyResult:
    """Result of validating a single foreign key."""

    constraint: ForeignKeyConstraint
    status: IntegrityStatus
    violations: list[str] = field(default_factory=list)

    # Statistics
    total_records: int = 0
    orphaned_records: int = 0
    null_records: int = 0
    integrity_percentage: float = 100.0


class ReferentialIntegrityValidator:
    """
    Validate referential integrity in multi-table synthetic data.

    Checks that foreign key constraints are properly maintained
    across generated tables.
    """

    def __init__(
        self,
        violation_tolerance: float = 0.01,  # Allow 1% violations by default
    ):
        """
        Initialize validator.

        Args:
            violation_tolerance: Maximum allowed percentage of FK violations
        """
        self.violation_tolerance = violation_tolerance

    def validate(
        self,
        synthetic_tables: dict[str, pd.DataFrame],
        relational_pattern: RelationalPattern,
    ) -> IntegrityResult:
        """
        Validate referential integrity across all tables.

        Args:
            synthetic_tables: Generated tables
            relational_pattern: Learned relational pattern

        Returns:
            IntegrityResult with validation details
        """
        fk_results = []
        total_violations = 0

        for fk in relational_pattern.foreign_keys:
            fk_result = self._validate_foreign_key(synthetic_tables, fk)
            fk_results.append(fk_result)
            total_violations += fk_result.orphaned_records

        # Compute overall score
        total_fks = len(fk_results)
        valid_fks = sum(1 for r in fk_results if r.status == IntegrityStatus.INTEGRITY_PASSED)

        integrity_score = valid_fks / total_fks if total_fks > 0 else 1.0

        # Determine overall status
        if integrity_score >= 1.0 - self.violation_tolerance:
            status = IntegrityStatus.INTEGRITY_PASSED
        elif integrity_score >= 0.8:
            status = IntegrityStatus.INTEGRITY_WARNING
        else:
            status = IntegrityStatus.INTEGRITY_FAILED

        # Generate recommendations
        recommendations = self._generate_recommendations(fk_results)

        return IntegrityResult(
            status=status,
            integrity_score=integrity_score,
            foreign_key_results=fk_results,
            total_fks=total_fks,
            valid_fks=valid_fks,
            total_violations=total_violations,
            recommendations=recommendations,
        )

    def _validate_foreign_key(
        self,
        tables: dict[str, pd.DataFrame],
        fk: ForeignKeyConstraint,
    ) -> ForeignKeyResult:
        """
        Validate a single foreign key constraint.

        Args:
            tables: Generated tables
            fk: Foreign key constraint to validate

        Returns:
            ForeignKeyResult with validation details
        """
        violations = []

        # Check if tables exist
        if fk.child_table not in tables:
            return ForeignKeyResult(
                constraint=fk,
                status=IntegrityStatus.INTEGRITY_FAILED,
                violations=[f"Child table '{fk.child_table}' not found"],
                total_records=0,
                orphaned_records=0,
                null_records=0,
                integrity_percentage=0.0,
            )

        if fk.parent_table not in tables:
            return ForeignKeyResult(
                constraint=fk,
                status=IntegrityStatus.INTEGRITY_FAILED,
                violations=[f"Parent table '{fk.parent_table}' not found"],
                total_records=0,
                orphaned_records=0,
                null_records=0,
                integrity_percentage=0.0,
            )

        child_df = tables[fk.child_table]
        parent_df = tables[fk.parent_table]

        # Check if columns exist
        if fk.child_column not in child_df.columns:
            return ForeignKeyResult(
                constraint=fk,
                status=IntegrityStatus.INTEGRITY_FAILED,
                violations=[f"Child column '{fk.child_column}' not found"],
                total_records=0,
                orphaned_records=0,
                null_records=0,
                integrity_percentage=0.0,
            )

        if fk.parent_column not in parent_df.columns:
            return ForeignKeyResult(
                constraint=fk,
                status=IntegrityStatus.INTEGRITY_FAILED,
                violations=[f"Parent column '{fk.parent_column}' not found"],
                total_records=0,
                orphaned_records=0,
                null_records=0,
                integrity_percentage=0.0,
            )

        # Get child values
        child_values = child_df[fk.child_column]
        parent_values = parent_df[fk.parent_column].dropna().unique()

        total_records = len(child_values)
        null_records = child_values.isna().sum()
        non_null_records = total_records - null_records

        # Find orphaned records (non-null values not in parent)
        if non_null_records > 0:
            orphan_mask = ~child_values.isna() & ~child_values.isin(parent_values)
            orphaned_records = orphan_mask.sum()
        else:
            orphaned_records = 0

        # Compute integrity percentage
        if non_null_records > 0:
            integrity_percentage = ((non_null_records - orphaned_records) / non_null_records) * 100
        else:
            integrity_percentage = 100.0

        # Determine status
        if orphaned_records == 0:
            status = IntegrityStatus.INTEGRITY_PASSED
        elif orphaned_records / non_null_records <= self.violation_tolerance:
            status = IntegrityStatus.INTEGRITY_WARNING
            violations.append(
                f"{orphaned_records} orphaned records ({orphaned_records / non_null_records:.2%})"
            )
        else:
            status = IntegrityStatus.INTEGRITY_FAILED
            violations.append(
                f"{orphaned_records} orphaned records ({orphaned_records / non_null_records:.2%})"
            )

        # Check null percentage
        if fk.null_percentage > 0:
            expected_nulls = total_records * fk.null_percentage
            null_diff = abs(null_records - expected_nulls) / total_records

            if null_diff > 0.05:  # 5% tolerance
                violations.append(
                    f"Null percentage mismatch: expected {fk.null_percentage:.1%}, "
                    f"got {null_records / total_records:.1%}"
                )

        return ForeignKeyResult(
            constraint=fk,
            status=status,
            violations=violations,
            total_records=total_records,
            orphaned_records=orphaned_records,
            null_records=null_records,
            integrity_percentage=integrity_percentage,
        )

    def _generate_recommendations(
        self, fk_results: list["ForeignKeyResult"]
    ) -> list[str]:
        """Generate recommendations based on validation results."""
        recommendations = []

        failed_fks = [r for r in fk_results if r.status == IntegrityStatus.INTEGRITY_FAILED]
        warning_fks = [r for r in fk_results if r.status == IntegrityStatus.INTEGRITY_WARNING]

        if failed_fks:
            recommendations.append(
                f"Fix {len(failed_fks)} failed foreign key constraints"
            )

        if warning_fks:
            recommendations.append(
                f"Review {len(warning_fks)} foreign key constraints with warnings"
            )

        # Specific recommendations
        for fk_result in fk_results:
            if fk_result.orphaned_records > 0:
                recommendations.append(
                    f"Address {fk_result.orphaned_records} orphaned records in "
                    f"{fk_result.constraint.child_table}.{fk_result.constraint.child_column}"
                )

        return recommendations

    def to_test_results(
        self, integrity_result: IntegrityResult
    ) -> list[TestResult]:
        """
        Convert integrity result to validation test results.

        Args:
            integrity_result: Integrity validation result

        Returns:
            List of TestResult objects
        """
        test_results = []

        for fk_result in integrity_result.foreign_key_results:
            status_map = {
                IntegrityStatus.INTEGRITY_PASSED: ValidationStatus.PASS,
                IntegrityStatus.INTEGRITY_WARNING: ValidationStatus.WARNING,
                IntegrityStatus.INTEGRITY_FAILED: ValidationStatus.FAIL,
            }

            test_results.append(
                TestResult(
                    test_name=f"fk_{fk_result.constraint.child_table}_{fk_result.constraint.child_column}",
                    status=status_map.get(fk_result.status, ValidationStatus.FAIL),
                    metric=fk_result.integrity_percentage,
                    threshold=100.0 * (1.0 - self.violation_tolerance),
                    message=f"Referential integrity: {fk_result.integrity_percentage:.1f}%",
                    details={
                        "orphaned_records": fk_result.orphaned_records,
                        "null_records": fk_result.null_records,
                        "violations": fk_result.violations,
                    },
                )
            )

        return test_results
