"""
Pattern storage and management.

Program of Thoughts:
1. Define Pattern data structure
2. Serialize learned patterns to JSON
3. Deserialize patterns from JSON
4. Save/load patterns from disk
5. Version tracking
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
import json
import hashlib
import numpy as np

from synth.patterns.schema import Schema, Field, FieldType
from synth.patterns.statistical import (
    NumericPattern,
    CategoricalPattern,
    StringPattern,
    DistributionParams,
    DistributionType,
)
from synth.core.errors import PatternError


@dataclass
class Pattern:
    """
    Complete pattern definition for generation.

    Contains schema and statistical patterns learned from data.
    """

    pattern_id: str
    source_files: list[str] = field(default_factory=list)
    learned_at: str = ""

    # Schema information
    schema: Optional[dict] = None  # Serialized Schema
    row_count: int = 0

    # Field patterns (indexed by field name)
    numeric_patterns: dict[str, dict] = field(default_factory=dict)
    categorical_patterns: dict[str, dict] = field(default_factory=dict)
    string_patterns: dict[str, dict] = field(default_factory=dict)

    # NEW: Correlation patterns for multivariate generation
    correlation_patterns: Optional[dict] = None

    # NEW: Relational patterns for multi-table generation
    relational_patterns: Optional[dict] = None

    # Metadata
    quality_metrics: dict[str, float] = field(default_factory=dict)
    version: str = "1.0"

    def __post_init__(self):
        """Set learned_at if not provided."""
        if not self.learned_at:
            self.learned_at = datetime.now().isoformat()


class PatternStorage:
    """
    Manage pattern storage and retrieval.

    Self-Reflection:
    1. Is serialization reversible?
    2. Are all important attributes preserved?
    3. Is format backward compatible?
    """

    def __init__(self, storage_dir: Path = Path("patterns")):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def save_pattern(self, pattern: Pattern, filename: Optional[str] = None) -> Path:
        """
        Save pattern to JSON file.

        PoT Steps:
        1. Serialize pattern to dict
        2. Convert to JSON
        3. Write to file
        4. Return file path
        """
        if filename is None:
            filename = f"{pattern.pattern_id}.json"

        filepath = self.storage_dir / filename

        # Serialize pattern
        pattern_dict = self._serialize_pattern(pattern)

        # Write to file with nice formatting
        with open(filepath, "w") as f:
            json.dump(pattern_dict, f, indent=2, default=self._json_serializer)

        return filepath

    def load_pattern(self, filename: str) -> Pattern:
        """
        Load pattern from JSON file.

        PoT Steps:
        1. Read file
        2. Parse JSON
        3. Deserialize to Pattern object
        4. Validate structure
        """
        filepath = self.storage_dir / filename

        if not filepath.exists():
            raise PatternError(f"Pattern file not found: {filepath}")

        with open(filepath) as f:
            pattern_dict = json.load(f)

        pattern = self._deserialize_pattern(pattern_dict)

        # Validate pattern
        self._validate_pattern(pattern)

        return pattern

    def list_patterns(self) -> list[str]:
        """List all available pattern files."""
        return [f.name for f in self.storage_dir.glob("*.json")]

    def delete_pattern(self, filename: str) -> bool:
        """Delete a pattern file."""
        filepath = self.storage_dir / filename
        if filepath.exists():
            filepath.unlink()
            return True
        return False

    def _serialize_pattern(self, pattern: Pattern) -> dict[str, Any]:
        """Serialize pattern to dict for JSON storage."""
        serialized = {
            "pattern_id": pattern.pattern_id,
            "source_files": pattern.source_files,
            "learned_at": pattern.learned_at,
            "schema": pattern.schema,
            "row_count": pattern.row_count,
            "numeric_patterns": pattern.numeric_patterns,
            "categorical_patterns": pattern.categorical_patterns,
            "string_patterns": pattern.string_patterns,
            "quality_metrics": pattern.quality_metrics,
            "version": pattern.version,
        }

        # Add correlation patterns if present
        if pattern.correlation_patterns:
            serialized["correlation_patterns"] = pattern.correlation_patterns

        # Add relational patterns if present
        if pattern.relational_patterns:
            serialized["relational_patterns"] = pattern.relational_patterns

        return serialized

    def _deserialize_pattern(self, data: dict[str, Any]) -> Pattern:
        """Deserialize dict to Pattern object."""
        return Pattern(
            pattern_id=data["pattern_id"],
            source_files=data.get("source_files", []),
            learned_at=data.get("learned_at", ""),
            schema=data.get("schema"),
            row_count=data.get("row_count", 0),
            numeric_patterns=data.get("numeric_patterns", {}),
            categorical_patterns=data.get("categorical_patterns", {}),
            string_patterns=data.get("string_patterns", {}),
            correlation_patterns=data.get("correlation_patterns"),
            relational_patterns=data.get("relational_patterns"),
            quality_metrics=data.get("quality_metrics", {}),
            version=data.get("version", "1.0"),
        )

    def _json_serializer(self, obj: Any) -> Any:
        """Custom JSON serializer for special types."""
        if isinstance(obj, FieldType):
            return obj.value
        if isinstance(obj, DistributionType):
            return obj.value
        if isinstance(obj, (datetime,)):
            return obj.isoformat()
        if isinstance(obj, np.bool_):
            return bool(obj)
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

    def _validate_pattern(self, pattern: Pattern) -> None:
        """
        Validate loaded pattern structure.

        Self-Reflection: Check for data corruption or format issues
        """
        if not pattern.pattern_id:
            raise PatternError("Pattern has no ID")

        if not pattern.schema and not (
            pattern.numeric_patterns
            or pattern.categorical_patterns
            or pattern.string_patterns
        ):
            raise PatternError("Pattern has no data")


def create_pattern_from_analysis(
    pattern_id: str,
    schema: Schema,
    numeric_patterns: dict[str, NumericPattern],
    categorical_patterns: dict[str, CategoricalPattern],
    string_patterns: dict[str, StringPattern],
    source_files: list[str],
) -> Pattern:
    """
    Create a Pattern from analysis results.

    PoT Steps:
    1. Extract schema dict
    2. Serialize numeric patterns
    3. Serialize categorical patterns
    4. Serialize string patterns
    5. Create Pattern object
    """
    # Serialize schema
    schema_dict = _serialize_schema(schema)

    # Serialize numeric patterns
    numeric_dict = {
        name: _serialize_numeric_pattern(p)
        for name, p in numeric_patterns.items()
    }

    # Serialize categorical patterns
    categorical_dict = {
        name: _serialize_categorical_pattern(p)
        for name, p in categorical_patterns.items()
    }

    # Serialize string patterns
    string_dict = {
        name: _serialize_string_pattern(p)
        for name, p in string_patterns.items()
    }

    # Compute quality metrics
    quality_metrics = _compute_quality_metrics(
        schema, numeric_patterns, categorical_patterns
    )

    return Pattern(
        pattern_id=pattern_id,
        source_files=source_files,
        schema=schema_dict,
        row_count=schema.row_count,
        numeric_patterns=numeric_dict,
        categorical_patterns=categorical_dict,
        string_patterns=string_dict,
        quality_metrics=quality_metrics,
    )


def _serialize_schema(schema: Schema) -> dict:
    """Serialize Schema to dict."""
    return {
        "row_count": schema.row_count,
        "fields": [
            {
                "name": f.name,
                "type": f.type.value,
                "nullable": f.nullable,
                "unique": f.unique,
                "null_count": f.null_count,
                "null_percentage": f.null_percentage,
                "unique_count": f.unique_count,
                "mean": f.mean,
                "std": f.std,
                "min_value": f.min_value,
                "max_value": f.max_value,
                "median": f.median,
                "quartiles": f.quartiles,
                "value_counts": f.value_counts,
                "mode": f.mode,
                "min_length": f.min_length,
                "max_length": f.max_length,
                "avg_length": f.avg_length,
                "sample_values": f.sample_values,
            }
            for f in schema.fields
        ],
    }


def _serialize_numeric_pattern(pattern: NumericPattern) -> dict:
    """Serialize NumericPattern to dict."""
    return {
        "field_name": pattern.field_name,
        "distribution": {
            "dist_type": pattern.distribution.dist_type.value,
            "params": pattern.distribution.params,
            "log_likelihood": pattern.distribution.log_likelihood,
            "aic": pattern.distribution.aic,
            "ks_statistic": pattern.distribution.ks_statistic,
            "ks_pvalue": pattern.distribution.ks_pvalue,
        },
        "outlier_method": pattern.outlier_method,
        "outlier_threshold": pattern.outlier_threshold,
        "has_outliers": pattern.has_outliers,
        "outlier_bounds": pattern.outlier_bounds,
    }


def _serialize_categorical_pattern(pattern: CategoricalPattern) -> dict:
    """Serialize CategoricalPattern to dict."""
    return {
        "field_name": pattern.field_name,
        "probabilities": pattern.probabilities,
        "is_multimodal": pattern.is_multimodal,
        "entropy": pattern.entropy,
    }


def _serialize_string_pattern(pattern: StringPattern) -> dict:
    """Serialize StringPattern to dict."""
    return {
        "field_name": pattern.field_name,
        "min_length": pattern.min_length,
        "max_length": pattern.max_length,
        "avg_length": pattern.avg_length,
        "length_distribution": {
            "dist_type": pattern.length_distribution.dist_type.value,
            "params": pattern.length_distribution.params,
        },
        "common_prefixes": pattern.common_prefixes,
        "common_suffixes": pattern.common_suffixes,
        "regex_pattern": pattern.regex_pattern,
    }


def _compute_quality_metrics(
    schema: Schema,
    numeric_patterns: dict[str, NumericPattern],
    categorical_patterns: dict[str, CategoricalPattern],
) -> dict[str, float]:
    """Compute quality metrics for the pattern."""
    metrics = {}

    # Completeness: percentage of non-null values
    total_nulls = sum(f.null_count for f in schema.fields)
    total_values = schema.row_count * len(schema.fields)
    metrics["completeness"] = 1.0 - (total_nulls / total_values if total_values > 0 else 1.0)

    # Distribution fit quality (average KS p-value)
    ks_pvalues = [
        p.distribution.ks_pvalue
        for p in numeric_patterns.values()
        if p.distribution.ks_pvalue > 0
    ]
    if ks_pvalues:
        metrics["avg_distribution_pvalue"] = sum(ks_pvalues) / len(ks_pvalues)
    else:
        metrics["avg_distribution_pvalue"] = 0.0

    # Pattern diversity (average entropy for categorical)
    entropies = [p.entropy for p in categorical_patterns.values()]
    if entropies:
        metrics["avg_categorical_entropy"] = sum(entropies) / len(entropies)
    else:
        metrics["avg_categorical_entropy"] = 0.0

    return metrics
