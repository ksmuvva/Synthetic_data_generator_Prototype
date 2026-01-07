"""
Semantic pattern analysis for string fields.

Analyzes string fields to extract semantic patterns
and entity types for intelligent generation.
"""

from dataclasses import dataclass, field
from typing import Optional, Any, list
from enum import Enum
import re

import numpy as np
import pandas as pd


class EntityType(str, Enum):
    """Semantic entity types."""

    PERSON = "person"
    ORGANIZATION = "organization"
    LOCATION = "location"
    DATE = "date"
    EMAIL = "email"
    PHONE = "phone"
    URL = "url"
    ADDRESS = "address"
    PRODUCT = "product"
    IDENTIFIER = "identifier"
    TEXT = "text"
    UNKNOWN = "unknown"


@dataclass
class SemanticAnalysis:
    """Result of semantic analysis of a field."""

    field_name: str
    entity_type: EntityType
    confidence: float

    # Format information
    format_pattern: Optional[str] = None
    example_values: list[str] = field(default_factory=list)

    # Statistics
    avg_length: float = 0.0
    min_length: int = 0
    max_length: int = 0
    unique_count: int = 0

    # Generation hints
    suggested_strategy: str = "faker"  # faker, template, markov


class SemanticAnalyzer:
    """
    Analyze semantic patterns in string fields.

    Detects entity types, formats, and suggests
    appropriate generation strategies.
    """

    def __init__(self):
        """Initialize analyzer."""
        self.patterns = {
            EntityType.EMAIL: re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'),
            EntityType.PHONE: re.compile(r'^\+?[\d\s\-\(\)]{10,}$'),
            EntityType.URL: re.compile(r'^https?://'),
            EntityType.DATE: re.compile(r'^\d{4}-\d{2}-\d{2}$|^\d{2}/\d{2}/\d{4}$'),
            EntityType.IDENTIFIER: re.compile(r'^[A-Z0-9\-_]{10,}$'),
        }

        self.field_keywords = {
            EntityType.PERSON: ["name", "first", "last", "full", "person"],
            EntityType.ORGANIZATION: ["company", "org", "business", "employer"],
            EntityType.LOCATION: ["city", "state", "country", "address", "location"],
            EntityType.EMAIL: ["email", "mail"],
            EntityType.PHONE: ["phone", "tel", "mobile"],
            EntityType.ADDRESS: ["address", "street", "zip", "postal"],
            EntityType.DATE: ["date", "time", "timestamp"],
            EntityType.PRODUCT: ["product", "item", "sku"],
            EntityType.IDENTIFIER: ["id", "uuid", "key"],
        }

    def analyze(
        self,
        df: pd.DataFrame,
        column: str,
        max_samples: int = 1000,
    ) -> SemanticAnalysis:
        """
        Analyze semantic patterns in a string column.

        Args:
            df: Input dataframe
            column: Column to analyze
            max_samples: Maximum values to analyze

        Returns:
            SemanticAnalysis with detected patterns
        """
        # Get values
        values = df[column].dropna().astype(str).tolist()
        sample_values = values[:max_samples] if len(values) > max_samples else values

        # Detect entity type
        entity_type = self._detect_entity_type(column, sample_values)
        confidence = self._estimate_confidence(column, sample_values, entity_type)

        # Extract format pattern
        format_pattern = self._extract_format_pattern(sample_values, entity_type)

        # Compute statistics
        lengths = [len(v) for v in sample_values]
        avg_length = np.mean(lengths) if lengths else 0
        min_length = int(min(lengths)) if lengths else 0
        max_length = int(max(lengths)) if lengths else 0
        unique_count = len(set(sample_values))

        # Suggest strategy
        strategy = self._suggest_strategy(entity_type, unique_count, len(sample_values))

        # Get example values
        examples = list(set(sample_values))[:5]

        return SemanticAnalysis(
            field_name=column,
            entity_type=entity_type,
            confidence=confidence,
            format_pattern=format_pattern,
            example_values=examples,
            avg_length=avg_length,
            min_length=min_length,
            max_length=max_length,
            unique_count=unique_count,
            suggested_strategy=strategy,
        )

    def _detect_entity_type(self, column: str, values: list[str]) -> EntityType:
        """Detect entity type from column name and values."""
        # Check column name keywords
        col_lower = column.lower()
        for entity_type, keywords in self.field_keywords.items():
            if any(kw in col_lower for kw in keywords):
                return entity_type

        # Check values for patterns
        if len(values) == 0:
            return EntityType.UNKNOWN

        # Count pattern matches
        pattern_counts = {}
        for entity_type, pattern in self.patterns.items():
            matches = sum(1 for v in values if pattern.match(v.strip()))
            pattern_counts[entity_type] = matches / len(values)

        # Find best match
        best_type = EntityType.UNKNOWN
        best_ratio = 0.0

        for entity_type, ratio in pattern_counts.items():
            if ratio > best_ratio and ratio > 0.5:
                best_type = entity_type
                best_ratio = ratio

        return best_type

    def _estimate_confidence(
        self, column: str, values: list[str], entity_type: EntityType
    ) -> float:
        """Estimate confidence in entity type detection."""
        if entity_type == EntityType.UNKNOWN:
            return 0.3

        # High confidence if field name matches
        col_lower = column.lower()
        for keywords in self.field_keywords.values():
            if any(kw in col_lower for kw in keywords):
                return 0.9

        # Medium confidence if pattern match
        if entity_type in self.patterns:
            pattern = self.patterns[entity_type]
            match_ratio = sum(1 for v in values if pattern.match(v.strip())) / len(values)
            return 0.7 + 0.2 * match_ratio

        return 0.6

    def _extract_format_pattern(
        self, values: list[str], entity_type: EntityType
    ) -> Optional[str]:
        """Extract format pattern from values."""
        if len(values) == 0:
            return None

        # Use first few values to infer pattern
        samples = values[:min(10, len(values))]

        if entity_type == EntityType.EMAIL:
            # Extract email format
            if samples:
                parts = samples[0].split("@")
                if len(parts) == 2:
                    return f"{{{parts[0][0]}*}@{parts[1]}"

        elif entity_type == EntityType.PHONE:
            # Extract phone format
            if samples:
                return samples[0]  # Use first as template

        elif entity_type == EntityType.DATE:
            # Detect date format
            for sample in samples:
                if "-" in sample:
                    return "YYYY-MM-DD"
                elif "/" in sample:
                    return "MM/DD/YYYY"

        elif entity_type == EntityType.IDENTIFIER:
            # Check for UUID-like format
            if samples and re.match(r'^[0-9a-f\-]{36}$', samples[0].lower()):
                return "UUID"

        return None

    def _suggest_strategy(
        self, entity_type: EntityType, unique_count: int, total_count: int
    ) -> str:
        """Suggest generation strategy."""
        # High uniqueness suggests use Faker
        if unique_count / total_count > 0.8:
            if entity_type in [EntityType.EMAIL, EntityType.PERSON, EntityType.ORGANIZATION]:
                return "faker"

        # Low uniqueness suggests categorical
        if unique_count < 50:
            return "categorical"

        # Default
        return "faker"
