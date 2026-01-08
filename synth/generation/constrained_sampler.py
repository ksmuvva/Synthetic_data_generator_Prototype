"""
Constrained sampler for rule-based synthetic data generation.

Generates synthetic data while enforcing business rules,
constraints, and relationships between fields.
"""

from typing import Optional, Any, Callable, List
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
import pandas as pd
from scipy import stats

from synth.generation.sampler import StatisticalSampler
from synth.patterns.storage import Pattern
from synth.patterns.schema import FieldType
from synth.core.errors import GenerationError


class ConstraintType(str, Enum):
    """Types of constraints."""

    RANGE = "range"  # Value must be in range [min, max]
    ENUM = "enum"  # Value must be from set
    REGEX = "regex"  # String must match regex
    CUSTOM = "custom"  # Custom validation function
    DEPENDENCY = "dependency"  # Depends on other field
    UNIQUENESS = "uniqueness"  # Values must be unique
    NOT_NULL = "not_null"  # Values cannot be null


@dataclass
class Constraint:
    """A constraint on a field."""

    name: str
    constraint_type: ConstraintType
    field_name: str

    # Constraint parameters
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    allowed_values: Optional[list[Any]] = None
    regex_pattern: Optional[str] = None
    validation_function: Optional[Callable[[Any], bool]] = None
    depends_on: Optional[str] = None
    dependency_function: Optional[Callable[[pd.DataFrame], pd.DataFrame]] = None

    # Error handling
    error_message: Optional[str] = None
    strict: bool = True  # If True, raise error; if False, adjust value


@dataclass
class ConstraintSet:
    """Collection of constraints for a schema."""

    constraints: List[Constraint] = field(default_factory=list)
    global_constraints: List[Constraint] = field(default_factory=list)

    def get_constraints_for_field(self, field_name: str) -> List[Constraint]:
        """Get all constraints for a specific field."""
        return [c for c in self.constraints if c.field_name == field_name]

    def has_dependency(self, field_name: str) -> bool:
        """Check if field has dependency constraints."""
        return any(
            c.depends_on == field_name
            for c in self.constraints
            if c.depends_on is not None
        )


class ConstraintValidator:
    """
    Validate data against constraints.
    """

    def __init__(self, strict: bool = True):
        """
        Initialize validator.

        Args:
            strict: If True, raise errors; if False, return violations
        """
        self.strict = strict

    def validate(
        self,
        df: pd.DataFrame,
        constraints: List[Constraint],
    ) -> list[str]:
        """
        Validate DataFrame against constraints.

        Args:
            df: DataFrame to validate
            constraints: List of constraints

        Returns:
            List of validation error messages

        Raises:
            GenerationError: If strict=True and validation fails
        """
        violations = []

        for constraint in constraints:
            violation = self._validate_constraint(df, constraint)
            if violation:
                violations.append(violation)

        if violations and self.strict:
            raise GenerationError(
                f"Constraint validation failed:\n" + "\n".join(violations)
            )

        return violations

    def _validate_constraint(
        self,
        df: pd.DataFrame,
        constraint: Constraint,
    ) -> Optional[str]:
        """Validate a single constraint."""
        if constraint.field_name not in df.columns:
            return f"Field '{constraint.field_name}' not found in data"

        column = df[constraint.field_name]

        if constraint.constraint_type == ConstraintType.RANGE:
            return self._validate_range(column, constraint)
        elif constraint.constraint_type == ConstraintType.ENUM:
            return self._validate_enum(column, constraint)
        elif constraint.constraint_type == ConstraintType.REGEX:
            return self._validate_regex(column, constraint)
        elif constraint.constraint_type == ConstraintType.UNIQUENESS:
            return self._validate_uniqueness(column, constraint)
        elif constraint.constraint_type == ConstraintType.NOT_NULL:
            return self._validate_not_null(column, constraint)

        return None

    def _validate_range(self, column: pd.Series, constraint: Constraint) -> Optional[str]:
        """Validate range constraint."""
        if constraint.min_value is not None:
            violations = (column < constraint.min_value).sum()
            if violations > 0:
                return f"{violations} values below minimum {constraint.min_value} in '{constraint.field_name}'"

        if constraint.max_value is not None:
            violations = (column > constraint.max_value).sum()
            if violations > 0:
                return f"{violations} values above maximum {constraint.max_value} in '{constraint.field_name}'"

        return None

    def _validate_enum(self, column: pd.Series, constraint: Constraint) -> Optional[str]:
        """Validate enum constraint."""
        if constraint.allowed_values is None:
            return None

        invalid = ~column.isin(constraint.allowed_values)
        violations = invalid.sum() - column.isna().sum()

        if violations > 0:
            return f"{violations} invalid values in '{constraint.field_name}' (not in {constraint.allowed_values})"

        return None

    def _validate_regex(self, column: pd.Series, constraint: Constraint) -> Optional[str]:
        """Validate regex constraint."""
        if constraint.regex_pattern is None:
            return None

        import re
        pattern = re.compile(constraint.regex_pattern)

        non_null = column.dropna()
        non_matching = non_null[~non_null.astype(str).str.match(pattern)]

        if len(non_matching) > 0:
            return f"{len(non_matching)} values don't match pattern '{constraint.regex_pattern}' in '{constraint.field_name}'"

        return None

    def _validate_uniqueness(self, column: pd.Series, constraint: Constraint) -> Optional[str]:
        """Validate uniqueness constraint."""
        duplicates = column.duplicated().sum()

        if duplicates > 0:
            return f"{duplicates} duplicate values in '{constraint.field_name}'"

        return None

    def _validate_not_null(self, column: pd.Series, constraint: Constraint) -> Optional[str]:
        """Validate not null constraint."""
        nulls = column.isna().sum()

        if nulls > 0:
            return f"{nulls} null values in '{constraint.field_name}' (should not be null)"

        return None


class ConstraintEnforcer:
    """
    Enforce constraints on generated data.

    Adjusts data to satisfy constraints while maintaining
    statistical properties as much as possible.
    """

    def __init__(self, max_iterations: int = 100):
        """
        Initialize enforcer.

        Args:
            max_iterations: Maximum iterations to satisfy constraints
        """
        self.max_iterations = max_iterations

    def enforce(
        self,
        df: pd.DataFrame,
        constraints: List[Constraint],
    ) -> pd.DataFrame:
        """
        Enforce constraints on DataFrame.

        Args:
            df: Input DataFrame
            constraints: List of constraints

        Returns:
            DataFrame with constraints enforced
        """
        result = df.copy()

        # Sort constraints by priority (dependencies last)
        sorted_constraints = self._sort_constraints(constraints)

        for constraint in sorted_constraints:
            result = self._enforce_constraint(result, constraint)

        return result

    def _sort_constraints(self, constraints: List[Constraint]) -> List[Constraint]:
        """Sort constraints so dependencies are processed last."""
        # Put dependencies at the end
        non_deps = [c for c in constraints if c.depends_on is None]
        deps = [c for c in constraints if c.depends_on is not None]

        return non_deps + deps

    def _enforce_constraint(
        self,
        df: pd.DataFrame,
        constraint: Constraint,
    ) -> pd.DataFrame:
        """Enforce a single constraint."""
        if constraint.constraint_type == ConstraintType.RANGE:
            return self._enforce_range(df, constraint)
        elif constraint.constraint_type == ConstraintType.ENUM:
            return self._enforce_enum(df, constraint)
        elif constraint.constraint_type == ConstraintType.REGEX:
            return self._enforce_regex(df, constraint)
        elif constraint.constraint_type == ConstraintType.UNIQUENESS:
            return self._enforce_uniqueness(df, constraint)
        elif constraint.constraint_type == ConstraintType.DEPENDENCY:
            return self._enforce_dependency(df, constraint)

        return df

    def _enforce_range(self, df: pd.DataFrame, constraint: Constraint) -> pd.DataFrame:
        """Enforce range constraint."""
        column = df[constraint.field_name].copy()

        if constraint.min_value is not None:
            column.loc[column < constraint.min_value] = constraint.min_value

        if constraint.max_value is not None:
            column.loc[column > constraint.max_value] = constraint.max_value

        df[constraint.field_name] = column
        return df

    def _enforce_enum(self, df: pd.DataFrame, constraint: Constraint) -> pd.DataFrame:
        """Enforce enum constraint."""
        if constraint.allowed_values is None:
            return df

        column = df[constraint.field_name]

        # Replace invalid values with closest valid one
        invalid_mask = ~column.isin(constraint.allowed_values) & ~column.isna()

        if invalid_mask.sum() > 0:
            # Replace with mode of allowed values
            if len(constraint.allowed_values) > 0:
                replacement = constraint.allowed_values[0]
                df.loc[invalid_mask, constraint.field_name] = replacement

        return df

    def _enforce_regex(self, df: pd.DataFrame, constraint: Constraint) -> pd.DataFrame:
        """Enforce regex constraint."""
        if constraint.regex_pattern is None:
            return df

        import re

        pattern = re.compile(constraint.regex_pattern)
        column = df[constraint.field_name]

        # Check non-null values
        non_null_mask = column.notna()
        non_matching = non_null_mask & ~column.astype(str).str.match(pattern)

        if non_matching.sum() > 0:
            # Generate matching values
            df.loc[non_matching, constraint.field_name] = self._generate_matching_value(
                pattern, non_matching.sum()
            )

        return df

    def _generate_matching_value(self, pattern, count: int) -> list[str]:
        """Generate values matching regex pattern."""
        # Simplified: return placeholder values
        # In production, would use regex generation library
        return [f"value_{i}" for i in range(count)]

    def _enforce_uniqueness(self, df: pd.DataFrame, constraint: Constraint) -> pd.DataFrame:
        """Enforce uniqueness constraint."""
        column = df[constraint.field_name]

        # Find duplicates
        duplicates = column.duplicated(keep='first')

        if duplicates.sum() > 0:
            # Replace duplicates with unique values
            if pd.api.types.is_numeric_dtype(column):
                # For numeric, add small increment
                for idx in column[duplicates].index:
                    original = column[idx]
                    while column.equals(original).sum() > 1 or pd.isna(original):
                        original += 0.001
                    column[idx] = original
            else:
                # For strings, add suffix
                counts = {}
                for idx in column[duplicates].index:
                    val = column[idx]
                    count = counts.get(val, 1)
                    column[idx] = f"{val}_{count}"
                    counts[val] = count + 1

            df[constraint.field_name] = column

        return df

    def _enforce_dependency(self, df: pd.DataFrame, constraint: Constraint) -> pd.DataFrame:
        """Enforce dependency constraint."""
        if constraint.dependency_function is None or constraint.depends_on is None:
            return df

        return constraint.dependency_function(df)


class ConstrainedSampler(StatisticalSampler):
    """
    Generate synthetic data with constraints.

    Extends StatisticalSampler to enforce business rules
    and constraints during generation.
    """

    def __init__(self, seed: Optional[int] = None, max_iterations: int = 100):
        """
        Initialize constrained sampler.

        Args:
            seed: Random seed
            max_iterations: Maximum iterations for constraint satisfaction
        """
        super().__init__(seed=seed)
        self.max_iterations = max_iterations
        self.validator = ConstraintValidator(strict=False)
        self.enforcer = ConstraintEnforcer(max_iterations)

    def generate_with_constraints(
        self,
        pattern: Pattern,
        count: int,
        constraints: List[Constraint],
    ) -> pd.DataFrame:
        """
        Generate data satisfying constraints.

        Args:
            pattern: Pattern for generation
            count: Number of records
            constraints: List of constraints

        Returns:
            DataFrame with constraint-satisfying data
        """
        # Generate initial data
        df = self.generate(pattern, count)

        # Iteratively enforce constraints
        for iteration in range(self.max_iterations):
            # Check violations
            violations = self.validator.validate(df, constraints)

            if not violations:
                # All constraints satisfied
                break

            # Enforce constraints
            df = self.enforcer.enforce(df, constraints)

        # Final validation
        violations = self.validator.validate(df, constraints)
        if violations:
            # Log warning but return best effort
            import warnings
            warnings.warn(
                f"Could not fully satisfy constraints after {self.max_iterations} iterations. "
                f"Remaining violations: {len(violations)}"
            )

        return df

    def _generate_column(
        self,
        pattern: Pattern,
        field_name: str,
        field_type: FieldType,
        field_info: dict,
        count: int,
    ) -> list[Any]:
        """Generate column with awareness of constraints."""
        # Check for constraints on this field
        # For now, use parent generation
        return super()._generate_column(pattern, field_name, field_type, field_info, count)
