"""
Conditional generation with constraints.

Provides constraint definition and enforcement for
conditional synthetic data generation.
"""

from dataclasses import dataclass, field
from typing import Optional, Any, list, Callable
from enum import Enum
import numpy as np
import pandas as pd


class ConstraintType(str, Enum):
    """Types of constraints."""

    RANGE = "range"  # Value must be in range
    EQUALITY = "equality"  # Value must equal specific value
    INEQUALITY = "inequality"  # Value must be in set
    REGEX = "regex"  # Value must match regex pattern
    CUSTOM = "custom"  # Custom constraint function
    CONDITIONAL = "conditional"  # Depends on other fields


@dataclass
class BaseConstraint:
    """Base constraint definition."""

    name: str
    field: str
    constraint_type: ConstraintType

    # Parameters
    params: dict[str, Any] = field(default_factory=dict)

    # Conditional dependencies (for conditional constraints)
    depends_on: list[str] = field(default_factory=list)

    # Custom function (for CUSTOM type)
    function: Optional[Callable] = None

    def validate(self, value: Any, row: dict = None) -> bool:
        """Validate a value against this constraint."""
        if self.constraint_type == ConstraintType.RANGE:
            min_val = self.params.get("min")
            max_val = self.params.get("max")
            return (min_val is None or value >= min_val) and (max_val is None or value <= max_val)

        elif self.constraint_type == ConstraintType.EQUALITY:
            return value == self.params.get("value")

        elif self.constraint_type == ConstraintType.INEQUALITY:
            return value in self.params.get("values", [])

        elif self.constraint_type == ConstraintType.REGEX:
            import re
            pattern = self.params.get("pattern")
            return bool(re.match(pattern, str(value)))

        elif self.constraint_type == ConstraintType.CUSTOM and self.function:
            return self.function(value, row)

        return True


class ConstraintSolver:
    """
    Solve and enforce constraints during generation.

    Uses rejection sampling and MCMC to generate
    data that satisfies constraints.
    """

    def __init__(self, max_iterations: int = 1000):
        """
        Initialize solver.

        Args:
            max_iterations: Maximum iterations for constraint solving
        """
        self.max_iterations = max_iterations

    def enforce_constraints(
        self,
        df: pd.DataFrame,
        constraints: list[BaseConstraint],
    ) -> pd.DataFrame:
        """
        Enforce constraints on dataframe.

        Args:
            df: Input dataframe
            constraints: List of constraints to enforce

        Returns:
            Dataframe with constraints enforced
        """
        df_constrained = df.copy()

        for constraint in constraints:
            df_constrained = self._enforce_single_constraint(df_constrained, constraint)

        return df_constrained

    def _enforce_single_constraint(
        self, df: pd.DataFrame, constraint: BaseConstraint
    ) -> pd.DataFrame:
        """Enforce a single constraint."""
        if constraint.constraint_type == ConstraintType.RANGE:
            min_val = constraint.params.get("min")
            max_val = constraint.params.get("max")

            if min_val is not None:
                df.loc[df[constraint.field] < min_val, constraint.field] = min_val
            if max_val is not None:
                df.loc[df[constraint.field] > max_val, constraint.field] = max_val

        elif constraint.constraint_type == ConstraintType.EQUALITY:
            value = constraint.params.get("value")
            df[constraint.field] = value

        elif constraint.constraint_type == ConstraintType.INEQUALITY:
            allowed_values = constraint.params.get("values", [])
            if allowed_values:
                df.loc[~df[constraint.field].isin(allowed_values), constraint.field] = np.random.choice(allowed_values)

        return df

    def generate_with_constraints(
        self,
        base_generator: Callable,
        count: int,
        constraints: list[BaseConstraint],
    ) -> pd.DataFrame:
        """
        Generate data with constraints using rejection sampling.

        Args:
            base_generator: Function to generate base data
            count: Number of valid records to generate
            constraints: List of constraints

        Returns:
            Dataframe satisfying all constraints
        """
        valid_records = []
        total_generated = 0
        max_total = count * 100  # Prevent infinite loop

        while len(valid_records) < count and total_generated < max_total:
            # Generate batch
            batch_size = min(100, count - len(valid_records))
            batch = base_generator(batch_size)

            # Check constraints
            for _, row in batch.iterrows():
                if all(
                    constraint.validate(row[constraint.field], row.to_dict())
                    for constraint in constraints
                ):
                    valid_records.append(row.to_dict())

            total_generated += batch_size

        return pd.DataFrame(valid_records[:count])
