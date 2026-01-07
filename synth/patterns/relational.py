"""
Relational pattern learning for multi-table synthetic data.

This module provides foreign key detection and referential integrity
preservation for multi-table database schemas.
"""

from dataclasses import dataclass, field
from typing import Optional, Any
from enum import Enum
import numpy as np
import pandas as pd


class RelationType(str, Enum):
    """Types of relationships between tables."""

    ONE_TO_ONE = "one_to_one"
    ONE_TO_MANY = "one_to_many"
    MANY_TO_MANY = "many_to_many"


@dataclass
class ForeignKeyConstraint:
    """
    Foreign key constraint between two tables.

    Represents a relationship where a column in the child table
    references a column in the parent table.
    """

    child_table: str
    child_column: str
    parent_table: str
    parent_column: str

    # Relationship statistics
    relation_type: RelationType = RelationType.ONE_TO_MANY
    null_percentage: float = 0.0
    unique_percentage: float = 1.0  # Percentage of unique values in child

    # Cardinality statistics
    parent_count: int = 0
    child_count: int = 0
    avg_children_per_parent: float = 0.0
    max_children_per_parent: int = 0


@dataclass
class RelationalPattern:
    """
    Complete relational schema pattern.

    Contains all foreign key relationships and table cardinalities
    for preserving referential integrity during generation.
    """

    tables: list[str]  # List of table names
    foreign_keys: list[ForeignKeyConstraint] = field(default_factory=list)

    # Metadata
    total_relationships: int = 0
    quality_score: float = 1.0


class RelationalAnalyzer:
    """
    Analyze relational patterns in multi-table data.

    Detects foreign key relationships and learns cardinality patterns
    for referential integrity preservation.
    """

    def __init__(self, similarity_threshold: float = 0.95):
        """
        Initialize analyzer.

        Args:
            similarity_threshold: Minimum similarity for column name matching
        """
        self.similarity_threshold = similarity_threshold

    def analyze_schema(
        self,
        tables: dict[str, pd.DataFrame],
        explicit_constraints: Optional[dict[str, Any]] = None
    ) -> RelationalPattern:
        """
        Analyze relational schema and detect relationships.

        Args:
            tables: Dictionary mapping table names to DataFrames
            explicit_constraints: Optional explicit FK definitions

        Returns:
            RelationalPattern with detected relationships
        """
        foreign_keys = []

        # Start with explicit constraints if provided
        if explicit_constraints:
            for fk_def in explicit_constraints.get("foreign_keys", []):
                fk = ForeignKeyConstraint(
                    child_table=fk_def["child_table"],
                    child_column=fk_def["child_column"],
                    parent_table=fk_def["parent_table"],
                    parent_column=fk_def["parent_column"],
                )
                # Compute statistics for explicit FKs
                fk = self._compute_fk_statistics(fk, tables)
                foreign_keys.append(fk)

        # Detect potential foreign keys automatically
        detected_fks = self._detect_foreign_keys(tables)
        foreign_keys.extend(detected_fks)

        # Compute quality score
        quality_score = self._compute_quality_score(tables, foreign_keys)

        return RelationalPattern(
            tables=list(tables.keys()),
            foreign_keys=foreign_keys,
            total_relationships=len(foreign_keys),
            quality_score=quality_score,
        )

    def _detect_foreign_keys(
        self, tables: dict[str, pd.DataFrame]
    ) -> list[ForeignKeyConstraint]:
        """Detect foreign key relationships automatically."""
        detected = []

        # Get all table pairs
        table_names = list(tables.keys())

        for child_table in table_names:
            for parent_table in table_names:
                if child_table == parent_table:
                    continue

                child_df = tables[child_table]
                parent_df = tables[parent_table]

                # Find potential foreign keys
                potential_fks = self._find_column_matches(child_df, parent_df)

                for child_col, parent_col in potential_fks:
                    fk = ForeignKeyConstraint(
                        child_table=child_table,
                        child_column=child_col,
                        parent_table=parent_table,
                        parent_column=parent_col,
                    )

                    # Compute statistics and validate
                    fk = self._compute_fk_statistics(fk, tables)

                    # Only keep if it's a valid relationship
                    if self._is_valid_foreign_key(fk, child_df, parent_df):
                        detected.append(fk)

        return detected

    def _find_column_matches(
        self, child_df: pd.DataFrame, parent_df: pd.DataFrame
    ) -> list[tuple[str, str]]:
        """Find matching column names between tables."""
        matches = []

        child_cols = child_df.columns.tolist()
        parent_cols = parent_df.columns.tolist()

        # Look for exact name matches
        for child_col in child_cols:
            for parent_col in parent_cols:
                if child_col.lower() == parent_col.lower():
                    matches.append((child_col, parent_col))

        # Look for common FK naming patterns
        for child_col in child_cols:
            for parent_col in parent_cols:
                if child_col.lower().endswith("_id") or child_col.lower().endswith("id"):
                    # Remove _id suffix and check for match
                    child_base = child_col.lower().replace("_id", "").replace("id", "")
                    parent_base = parent_col.lower().replace("_id", "").replace("id", "")
                    if child_base == parent_base and child_base:
                        if (child_col, parent_col) not in matches:
                            matches.append((child_col, parent_col))

        return matches

    def _compute_fk_statistics(
        self, fk: ForeignKeyConstraint, tables: dict[str, pd.DataFrame]
    ) -> ForeignKeyConstraint:
        """Compute statistics for a foreign key relationship."""
        child_df = tables[fk.child_table]
        parent_df = tables[fk.parent_table]

        child_col = child_df[fk.child_column]
        parent_col = parent_df[fk.parent_column]

        # Null percentage
        fk.null_percentage = child_col.isna().sum() / len(child_col)

        # Unique values in child
        unique_child = child_col.dropna().nunique()
        fk.unique_percentage = unique_child / len(child_col.dropna()) if len(child_col.dropna()) > 0 else 0

        # Cardinality statistics
        fk.parent_count = parent_col.dropna().nunique()
        fk.child_count = len(child_col.dropna())

        # Children per parent statistics
        if fk.parent_count > 0:
            value_counts = child_col.dropna().value_counts()
            fk.avg_children_per_parent = value_counts.mean()
            fk.max_children_per_parent = value_counts.max()

        # Determine relationship type
        if fk.parent_count == len(child_df):
            fk.relation_type = RelationType.ONE_TO_ONE
        else:
            fk.relation_type = RelationType.ONE_TO_MANY

        return fk

    def _is_valid_foreign_key(
        self, fk: ForeignKeyConstraint, child_df: pd.DataFrame, parent_df: pd.DataFrame
    ) -> bool:
        """Validate if a detected relationship is a valid foreign key."""
        child_vals = child_df[fk.child_column].dropna()
        parent_vals = parent_df[fk.parent_column].dropna()

        # Check if most child values exist in parent
        if len(child_vals) == 0 or len(parent_vals) == 0:
            return False

        # At least 80% of child values should exist in parent
        match_ratio = child_vals.isin(parent_vals).sum() / len(child_vals)

        return match_ratio >= 0.8


class RelationalValidator:
    """
    Validate referential integrity in synthetic data.

    Checks that foreign key constraints are satisfied in
    generated multi-table data.
    """

    def validate(
        self,
        synthetic_tables: dict[str, pd.DataFrame],
        pattern: RelationalPattern,
    ) -> dict[str, Any]:
        """
        Validate referential integrity.

        Args:
            synthetic_tables: Generated tables
            pattern: Learned relational pattern

        Returns:
            Validation results with integrity scores
        """
        results = {
            "valid_fks": [],
            "invalid_fks": [],
            "integrity_score": 1.0,
            "violations": [],
        }

        total_fks = len(pattern.foreign_keys)
        if total_fks == 0:
            return results

        valid_count = 0

        for fk in pattern.foreign_keys:
            fk_valid, violations = self._validate_fk(synthetic_tables, fk)

            if fk_valid:
                results["valid_fks"].append(
                    f"{fk.child_table}.{fk.child_column} -> {fk.parent_table}.{fk.parent_column}"
                )
                valid_count += 1
            else:
                results["invalid_fks"].append(
                    f"{fk.child_table}.{fk.child_column} -> {fk.parent_table}.{fk.parent_column}"
                )
                results["violations"].extend(violations)

        # Compute integrity score
        results["integrity_score"] = valid_count / total_fks if total_fks > 0 else 1.0

        return results

    def _validate_fk(
        self, tables: dict[str, pd.DataFrame], fk: ForeignKeyConstraint
    ) -> tuple[bool, list[str]]:
        """Validate a single foreign key constraint."""
        violations = []

        if fk.child_table not in tables or fk.parent_table not in tables:
            return False, [f"Missing table: {fk.child_table} or {fk.parent_table}"]

        child_df = tables[fk.child_table]
        parent_df = tables[fk.parent_table]

        if fk.child_column not in child_df.columns or fk.parent_column not in parent_df.columns:
            return False, [f"Missing column: {fk.child_column} or {fk.parent_column}"]

        child_vals = child_df[fk.child_column].dropna()
        parent_vals = parent_df[fk.parent_column].dropna()

        # Check for orphaned records
        orphans = child_vals[~child_vals.isin(parent_vals)]
        orphan_count = len(orphans)

        if orphan_count > 0:
            violations.append(
                f"{orphan_count} orphaned records in {fk.child_table}.{fk.child_column}"
            )

        return len(violations) == 0, violations
