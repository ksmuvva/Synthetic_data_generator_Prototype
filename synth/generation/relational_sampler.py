"""
Relational sampler for multi-table synthetic data generation.

Generates multiple related tables while preserving referential integrity
and foreign key relationships.
"""

from typing import Optional, Any
import numpy as np
import pandas as pd
from dataclasses import dataclass

from synth.generation.sampler import StatisticalSampler
from synth.patterns.relational import (
    RelationalPattern,
    ForeignKeyConstraint,
    RelationType,
)
from synth.patterns.storage import Pattern
from synth.core.errors import GenerationError


@dataclass
class GenerationPlan:
    """Plan for generating multiple tables in dependency order."""

    tables: list[str]  # Tables in generation order
    dependencies: dict[str, list[str]]  # Each table's dependencies


class ForeignKeyResolver:
    """
    Resolve and enforce foreign key constraints during generation.

    Ensures that child table values reference valid parent table records.
    """

    def __init__(self, seed: Optional[int] = None):
        """Initialize resolver."""
        self.seed = seed
        if seed is not None:
            np.random.seed(seed)

    def resolve_foreign_keys(
        self,
        child_table: pd.DataFrame,
        parent_table: pd.DataFrame,
        fk: ForeignKeyConstraint,
    ) -> pd.DataFrame:
        """
        Resolve foreign key values for child table.

        Ensures all FK values in child reference valid parent records.

        Args:
            child_table: Child table DataFrame
            parent_table: Parent table DataFrame
            fk: Foreign key constraint

        Returns:
            Child table with resolved FK values
        """
        # Get parent column values (unique)
        parent_values = parent_table[fk.parent_column].dropna().unique()

        if len(parent_values) == 0:
            raise GenerationError(
                f"No valid parent values in {fk.parent_table}.{fk.parent_column}"
            )

        # Get child column
        child_col = child_table[fk.child_column].copy()

        # Replace invalid FK values with valid ones
        null_mask = child_col.isna()
        non_null_mask = ~null_mask

        # Find values that don't exist in parent
        invalid_mask = non_null_mask & ~child_col.isin(parent_values)

        # Replace invalid values with random valid parent values
        if invalid_mask.sum() > 0:
            num_invalid = invalid_mask.sum()
            replacement_values = np.random.choice(parent_values, size=num_invalid)
            child_col.loc[invalid_mask] = replacement_values

        # Handle nulls based on learned null percentage
        if fk.null_percentage > 0:
            # Ensure correct percentage of nulls
            null_count = int(len(child_col) * fk.null_percentage)
            if null_count > 0:
                # Get indices that should be null
                current_nulls = child_col.isna().sum()
                needed_nulls = max(0, null_count - current_nulls)

                if needed_nulls > 0:
                    # Randomly select indices to nullify
                    non_null_indices = child_col[~child_col.isna()].index
                    nullify_indices = np.random.choice(
                        non_null_indices, size=min(needed_nulls, len(non_null_indices)), replace=False
                    )
                    child_col.loc[nullify_indices] = np.nan

        child_table[fk.child_column] = child_col

        return child_table


class RelationalSampler(StatisticalSampler):
    """
    Generate multi-table synthetic data with referential integrity.

    Extends StatisticalSampler to handle multiple related tables
    and enforce foreign key constraints.
    """

    def __init__(self, seed: Optional[int] = None):
        """Initialize sampler."""
        super().__init__(seed=seed)
        self.fk_resolver = ForeignKeyResolver(seed=seed)

    def generate_relational(
        self,
        patterns: dict[str, Pattern],
        relational_pattern: RelationalPattern,
        counts: dict[str, int],
    ) -> dict[str, pd.DataFrame]:
        """
        Generate multiple related tables.

        Args:
            patterns: Dictionary mapping table names to their Patterns
            relational_pattern: RelationalPattern with FK constraints
            counts: Dictionary mapping table names to row counts

        Returns:
            Dictionary mapping table names to generated DataFrames
        """
        # Build generation plan (topological sort by dependencies)
        plan = self._build_generation_plan(relational_pattern)

        # Generate tables in dependency order
        generated = {}

        for table_name in plan.tables:
            # Get pattern and count
            pattern = patterns.get(table_name)
            count = counts.get(table_name, 1000)

            if pattern is None:
                raise GenerationError(f"No pattern found for table: {table_name}")

            # Generate the table
            df = self.generate(pattern, count)

            # Resolve foreign keys (after parent tables are generated)
            if table_name in plan.dependencies:
                for parent_name in plan.dependencies[table_name]:
                    # Find the FK constraint
                    for fk in relational_pattern.foreign_keys:
                        if fk.child_table == table_name and fk.parent_table == parent_name:
                            if parent_name in generated:
                                df = self.fk_resolver.resolve_foreign_keys(
                                    df, generated[parent_name], fk
                                )

            generated[table_name] = df

        return generated

    def _build_generation_plan(self, pattern: RelationalPattern) -> GenerationPlan:
        """
        Build generation plan with dependency ordering.

        Uses topological sorting to ensure parent tables are
        generated before child tables.

        Args:
            pattern: RelationalPattern

        Returns:
            GenerationPlan with ordered tables
        """
        # Build dependency graph
        dependencies = {table: [] for table in pattern.tables}

        for fk in pattern.foreign_keys:
            if fk.child_table in dependencies:
                if fk.parent_table not in dependencies[fk.child_table]:
                    dependencies[fk.child_table].append(fk.parent_table)

        # Topological sort (Kahn's algorithm)
        in_degree = {table: len(deps) for table, deps in dependencies.items()}
        queue = [table for table, degree in in_degree.items() if degree == 0]
        sorted_tables = []

        while queue:
            # Get table with no dependencies
            table = queue.pop(0)
            sorted_tables.append(table)

            # Reduce in-degree for dependent tables
            for other_table, deps in dependencies.items():
                if table in deps:
                    new_deps = [d for d in deps if d != table]
                    dependencies[other_table] = new_deps
                    in_degree[other_table] -= 1

                    if in_degree[other_table] == 0:
                        queue.append(other_table)

        # Check for cycles
        if len(sorted_tables) != len(pattern.tables):
            raise GenerationError(
                "Circular dependency detected in foreign key relationships"
            )

        return GenerationPlan(
            tables=sorted_tables,
            dependencies={t: dependencies[t] for t in sorted_tables},
        )

    def scale_relational(
        self,
        reference_tables: dict[str, pd.DataFrame],
        patterns: dict[str, Pattern],
        relational_pattern: RelationalPattern,
        scale_factor: float,
    ) -> dict[str, pd.DataFrame]:
        """
        Scale existing relational data by a factor.

        Preserves relationships and referential integrity.

        Args:
            reference_tables: Original tables
            patterns: Learned patterns
            relational_pattern: Relational pattern
            scale_factor: Scaling factor (e.g., 2.0 for 2x data)

        Returns:
            Scaled tables
        """
        counts = {
            name: max(1000, int(len(df) * scale_factor))
            for name, df in reference_tables.items()
        }

        return self.generate_relational(patterns, relational_pattern, counts)
