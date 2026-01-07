"""
Semantic string generation using entity recognition.

Generates semantically meaningful strings by recognizing
entity types and using appropriate generation strategies.
"""

from dataclasses import dataclass, field
from typing import Optional, Any, list
from enum import Enum
import re

import pandas as pd


class EntityType(str, Enum):
    """Types of named entities."""

    PERSON = "person"
    ORGANIZATION = "organization"
    LOCATION = "location"
    DATE = "date"
    EMAIL = "email"
    PHONE = "phone"
    URL = "url"
    ADDRESS = "address"
    CREDIT_CARD = "credit_card"
    SSN = "ssn"
    IP_ADDRESS = "ip_address"
    PRODUCT = "product"
    EVENT = "event"
    QUANTITY = "quantity"
    UNKNOWN = "unknown"


@dataclass
class SemanticPattern:
    """Semantic pattern for string generation."""

    field_name: str
    entity_type: EntityType
    confidence: float  # 0.0 to 1.0

    # Generation parameters
    format_template: Optional[str] = None
    locale: str = "en_US"

    # Context information
    related_fields: list[str] = field(default_factory=list)


@dataclass
class EntityAnnotation:
    """Annotation of an entity in text."""

    text: str
    entity_type: EntityType
    start: int
    end: int
    confidence: float


class EntityRecognizer:
    """
    Recognize named entities in text.

    Uses pattern matching and heuristics to identify
    entity types in string data.
    """

    # Entity patterns
    EMAIL_PATTERN = re.compile(
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    )
    PHONE_PATTERN = re.compile(
        r'\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'
    )
    URL_PATTERN = re.compile(
        r'\bhttps?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b'
    )
    SSN_PATTERN = re.compile(
        r'\b\d{3}-\d{2}-\d{4}\b|\b\d{9}\b'
    )
    IP_PATTERN = re.compile(
        r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'
    )
    CREDIT_CARD_PATTERN = re.compile(
        r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'
    )
    DATE_PATTERN = re.compile(
        r'\b\d{4}-\d{2}-\d{2}\b|\b\d{2}/\d{2}/\d{4}\b'
    )

    def __init__(self):
        """Initialize recognizer."""
        self.field_keywords = {
            EntityType.PERSON: ["name", "person", "customer", "user"],
            EntityType.ORGANIZATION: ["company", "organization", "employer", "business"],
            EntityType.LOCATION: ["city", "state", "country", "address", "location"],
            EntityType.DATE: ["date", "time", "datetime", "timestamp"],
            EntityType.EMAIL: ["email", "mail"],
            EntityType.PHONE: ["phone", "telephone", "mobile"],
            EntityType.ADDRESS: ["address", "street", "zip"],
            EntityType.PRODUCT: ["product", "item", "sku"],
        }

    def recognize_entity_type(
        self,
        values: list[str],
        field_name: Optional[str] = None,
    ) -> EntityType:
        """
        Recognize entity type from field name and values.

        Args:
            values: Sample values
            field_name: Optional field name

        Returns:
            Detected entity type
        """
        if field_name:
            # Check field name
            field_lower = field_name.lower()
            for entity_type, keywords in self.field_keywords.items():
                if any(kw in field_lower for kw in keywords):
                    return entity_type

        # Check values for patterns
        if len(values) == 0:
            return EntityType.UNKNOWN

        sample = str(values[0]) if values else ""

        # Pattern matching
        if self.EMAIL_PATTERN.match(sample):
            return EntityType.EMAIL
        elif self.PHONE_PATTERN.match(sample):
            return EntityType.PHONE
        elif self.URL_PATTERN.match(sample):
            return EntityType.URL
        elif self.SSN_PATTERN.match(sample):
            return EntityType.SSN
        elif self.IP_PATTERN.match(sample):
            return EntityType.IP_ADDRESS
        elif self.CREDIT_CARD_PATTERN.match(sample):
            return EntityType.CREDIT_CARD
        elif self.DATE_PATTERN.match(sample):
            return EntityType.DATE

        return EntityType.UNKNOWN

    def annotate_entities(self, text: str) -> list[EntityAnnotation]:
        """
        Annotate entities in text.

        Args:
            text: Input text

        Returns:
            List of entity annotations
        """
        annotations = []

        # Check each pattern
        patterns = [
            (self.EMAIL_PATTERN, EntityType.EMAIL, 0.95),
            (self.PHONE_PATTERN, EntityType.PHONE, 0.9),
            (self.URL_PATTERN, EntityType.URL, 0.95),
            (self.SSN_PATTERN, EntityType.SSN, 0.95),
            (self.IP_PATTERN, EntityType.IP_ADDRESS, 0.9),
            (self.DATE_PATTERN, EntityType.DATE, 0.85),
        ]

        for pattern, entity_type, confidence in patterns:
            for match in pattern.finditer(text):
                annotations.append(
                    EntityAnnotation(
                        text=match.group(),
                        entity_type=entity_type,
                        start=match.start(),
                        end=match.end(),
                        confidence=confidence,
                    )
                )

        return annotations


class SemanticStringGenerator:
    """
    Generate semantically meaningful strings.

    Uses entity recognition to generate appropriate
    strings based on semantic type.
    """

    def __init__(self, locale: str = "en_US", seed: Optional[int] = None):
        """
        Initialize generator.

        Args:
            locale: Locale for generation
            seed: Random seed
        """
        from synth.generation.string_generator import FakerGenerator

        self.locale = locale
        self.seed = seed
        self.faker_gen = FakerGenerator(locale, seed)
        self.recognizer = EntityRecognizer()

    def generate(
        self,
        pattern: SemanticPattern,
        count: int,
    ) -> list[str]:
        """
        Generate strings based on semantic pattern.

        Args:
            pattern: Semantic pattern
            count: Number of strings to generate

        Returns:
            List of generated strings
        """
        if pattern.entity_type == EntityType.EMAIL:
            return self.faker_gen.generate("email", count)

        elif pattern.entity_type == EntityType.PERSON:
            return self.faker_gen.generate("name", count)

        elif pattern.entity_type == EntityType.PHONE:
            return self.faker_gen.generate("phone", count)

        elif pattern.entity_type == EntityType.ADDRESS:
            return self.faker_gen.generate("address", count)

        elif pattern.entity_type == EntityType.ORGANIZATION:
            return self.faker_gen.generate("company", count)

        elif pattern.entity_type == EntityType.LOCATION:
            return [self.faker_gen.fake.city() for _ in range(count)]

        elif pattern.entity_type == EntityType.DATE:
            return [self.faker_gen.fake.date() for _ in range(count)]

        elif pattern.entity_type == EntityType.URL:
            return [self.faker_gen.fake.url() for _ in range(count)]

        else:
            # Fallback
            return self.faker_gen.generate(pattern.field_name, count)

    def learn_pattern(
        self,
        values: list[str],
        field_name: str,
    ) -> SemanticPattern:
        """
        Learn semantic pattern from values.

        Args:
            values: Sample values
            field_name: Field name

        Returns:
            Learned semantic pattern
        """
        entity_type = self.recognizer.recognize_entity_type(values, field_name)

        # Estimate confidence based on pattern match
        confidence = 0.7
        if entity_type != EntityType.UNKNOWN:
            confidence = 0.9

        return SemanticPattern(
            field_name=field_name,
            entity_type=entity_type,
            confidence=confidence,
            locale=self.locale,
        )
