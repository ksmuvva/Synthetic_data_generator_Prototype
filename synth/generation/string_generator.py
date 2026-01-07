"""
Smart string generation using Faker and templates.

Generates realistic string data using Faker library
and learned patterns from source data.
"""

from dataclasses import dataclass, field
from typing import Optional, Any, list
from enum import Enum
import re
import random
from faker import Faker
import numpy as np
import pandas as pd


class StringGenerationStrategy(str, Enum):
    """Strategies for string generation."""

    FAKER = "faker"  # Use Faker library
    TEMPLATE = "template"  # Use learned templates
    MARKOV = "markov"  # Use Markov chains
    SEMANTIC = "semantic"  # Use semantic patterns


@dataclass
class StringPattern:
    """Pattern for string generation."""

    field_name: str
    strategy: StringGenerationStrategy
    length_distribution: dict  # Min, max, mean length

    # Template pattern (for TEMPLATE strategy)
    template: Optional[str] = None

    # Faker provider (for FAKER strategy)
    faker_provider: Optional[str] = None

    # Sample values (for MARKOV strategy)
    sample_values: list[str] = field(default_factory=list)


class TemplateGenerator:
    """
    Generate strings based on learned templates.

    Extracts and applies templates from string data.
    """

    def __init__(self, seed: Optional[int] = None):
        """Initialize generator."""
        self.seed = seed
        if seed is not None:
            random.seed(seed)
            Faker.seed(seed)

    def learn_template(self, values: list[str]) -> Optional[str]:
        """
        Learn a template from string values.

        Args:
            values: List of string values

        Returns:
            Extracted template or None
        """
        if len(values) == 0:
            return None

        # Analyze patterns
        patterns = []

        for val in values[:100]:  # Sample first 100
            # Replace numbers with {n}
            pattern = re.sub(r'\d+', '{n}', val)
            # Replace uppercase words with {word}
            pattern = re.sub(r'[A-Z][A-Z]+', '{WORD}', pattern)
            # Replace email-like patterns
            pattern = re.sub(r'\w+@\w+\.\w+', '{email}', pattern)
            # Replace dates
            pattern = re.sub(r'\d{4}-\d{2}-\d{2}', '{date}', pattern)

            patterns.append(pattern)

        # Find most common pattern
        from collections import Counter
        pattern_counts = Counter(patterns)

        if pattern_counts:
            most_common = pattern_counts.most_common(1)[0][0]

            # Convert to template format
            return most_common.replace('{n}', '{number}').replace('{WORD}', '{uppercase}')

        return None

    def generate(
        self,
        template: str,
        count: int,
    ) -> list[str]:
        """
        Generate strings from template.

        Args:
            template: Template string
            count: Number of strings to generate

        Returns:
            List of generated strings
        """
        results = []

        for _ in range(count):
            result = template

            # Replace placeholders
            result = result.replace('{number}', str(random.randint(1, 10000)))
            result = result.replace('{email}', self._generate_fake_email())
            result = result.replace('{date}', self._generate_fake_date())
            result = result.replace('{uppercase}', self._generate_fake_word().upper())

            results.append(result)

        return results

    def _generate_fake_email(self) -> str:
        """Generate fake email."""
        fake = Faker()
        return fake.email()

    def _generate_fake_date(self) -> str:
        """Generate fake date."""
        fake = Faker()
        return fake.date()

    def _generate_fake_word(self) -> str:
        """Generate fake word."""
        fake = Faker()
        return fake.word()


class FakerGenerator:
    """
    Generate strings using Faker library.

    Maps field types to appropriate Faker providers.
    """

    FIELD_TYPE_MAP = {
        "email": "email",
        "name": "name",
        "first_name": "first_name",
        "last_name": "last_name",
        "full_name": "name",
        "username": "user_name",
        "password": "password",
        "phone": "phone_number",
        "telephone": "phone_number",
        "address": "address",
        "street": "street_address",
        "city": "city",
        "state": "state",
        "zip": "postcode",
        "postal_code": "postcode",
        "country": "country",
        "company": "company",
        "job": "job",
        "text": "text",
        "sentence": "sentence",
        "paragraph": "paragraph",
        "url": "url",
        "ipv4": "ipv4",
        "ipv6": "ipv6",
        "mac_address": "mac_address",
        "user_agent": "user_agent",
        "credit_card": "credit_card_number",
        "ssn": "ssn",
        "date": "date",
        "time": "time",
        "datetime": "date_time",
        "uuid": "uuid4",
    }

    def __init__(self, locale: str = "en_US", seed: Optional[int] = None):
        """
        Initialize generator.

        Args:
            locale: Locale for Faker
            seed: Random seed
        """
        self.locale = locale
        self.seed = seed

        if seed is not None:
            Faker.seed(seed)

        self.fake = Faker(locale)

    def generate(
        self,
        field_name: str,
        count: int,
        provider: Optional[str] = None,
    ) -> list[str]:
        """
        Generate strings using Faker.

        Args:
            field_name: Name of field (used to auto-detect provider)
            count: Number of strings to generate
            provider: Explicit Faker provider (overrides auto-detect)

        Returns:
            List of generated strings
        """
        # Determine provider
        if provider:
            faker_method = provider
        else:
            faker_method = self._detect_provider(field_name)

        # Generate using provider
        results = []
        for _ in range(count):
            try:
                value = self._call_faker_method(faker_method)
                results.append(str(value))
            except (AttributeError, TypeError):
                # Fallback to simple word
                results.append(self.fake.word())

        return results

    def _detect_provider(self, field_name: str) -> str:
        """Auto-detect Faker provider from field name."""
        field_lower = field_name.lower()

        # Direct match
        if field_lower in self.FIELD_TYPE_MAP:
            return self.FIELD_TYPE_MAP[field_lower]

        # Partial match
        for key, provider in self.FIELD_TYPE_MAP.items():
            if key in field_lower or field_lower in key:
                return provider

        # Default
        return "word"

    def _call_faker_method(self, method_name: str) -> Any:
        """Call a Faker method."""
        method = getattr(self.fake, method_name, None)

        if method is None:
            # Try variations
            method = getattr(self.fake, method_name.replace("_", ""), None)

        if method and callable(method):
            return method()

        return self.fake.word()


class MarkovChainGenerator:
    """
    Generate strings using Markov chains.

    Learns character-level or word-level transitions
    from training data.
    """

    def __init__(self, order: int = 2, seed: Optional[int] = None):
        """
        Initialize generator.

        Args:
            order: Order of Markov chain
            seed: Random seed
        """
        self.order = order
        self.seed = seed
        self.transitions = {}

    def train(self, values: list[str], level: str = "character") -> None:
        """
        Train Markov chain on values.

        Args:
            values: Training strings
            level: "character" or "word"
        """
        self.transitions = {}
        self.level = level

        for val in values:
            if level == "character":
                tokens = list(val)
            else:
                tokens = val.split()

            # Build transition matrix
            for i in range(len(tokens) - self.order):
                context = tuple(tokens[i:i + self.order])
                next_token = tokens[i + self.order]

                if context not in self.transitions:
                    self.transitions[context] = {}

                if next_token not in self.transitions[context]:
                    self.transitions[context][next_token] = 0

                self.transitions[context][next_token] += 1

    def generate(
        self,
        count: int,
        min_length: int = 5,
        max_length: int = 20,
    ) -> list[str]:
        """
        Generate strings using Markov chain.

        Args:
            count: Number of strings to generate
            min_length: Minimum length
            max_length: Maximum length

        Returns:
            List of generated strings
        """
        if not self.transitions:
            return [""] * count

        results = []

        for _ in range(count):
            # Random starting context
            context = random.choice(list(self.transitions.keys()))
            result = list(context)

            for _ in range(max_length - self.order):
                if context not in self.transitions:
                    break

                # Sample next token
                next_tokens = list(self.transitions[context].keys())
                weights = list(self.transitions[context].values())
                total = sum(weights)

                if total == 0:
                    break

                probs = [w / total for w in weights]
                next_token = random.choices(next_tokens, weights=probs)[0]

                result.append(next_token)
                context = tuple(list(context[1:]) + [next_token])

                # Check for termination
                if len(result) >= min_length and random.random() < 0.1:
                    break

            if self.level == "character":
                results.append("".join(result))
            else:
                results.append(" ".join(result))

        return results


class SmartStringGenerator:
    """
    Smart string generation using multiple strategies.

    Combines Faker, templates, and Markov chains for
    realistic string generation.
    """

    def __init__(self, locale: str = "en_US", seed: Optional[int] = None):
        """
        Initialize generator.

        Args:
            locale: Locale for Faker
            seed: Random seed
        """
        self.locale = locale
        self.seed = seed

        self.faker_gen = FakerGenerator(locale, seed)
        self.template_gen = TemplateGenerator(seed)
        self.markov_gen = MarkovChainGenerator(seed=seed)

    def generate(
        self,
        pattern: StringPattern,
        count: int,
    ) -> list[str]:
        """
        Generate strings based on pattern.

        Args:
            pattern: Learned string pattern
            count: Number of strings to generate

        Returns:
            List of generated strings
        """
        if pattern.strategy == StringGenerationStrategy.FAKER:
            return self.faker_gen.generate(
                pattern.field_name,
                count,
                pattern.faker_provider,
            )

        elif pattern.strategy == StringGenerationStrategy.TEMPLATE:
            if pattern.template:
                return self.template_gen.generate(pattern.template, count)

        elif pattern.strategy == StringGenerationStrategy.MARKOV:
            # Train Markov chain on sample values
            if pattern.sample_values:
                self.markov_gen.train(pattern.sample_values)
                return self.markov_gen.generate(count)

        # Fallback: Faker
        return self.faker_gen.generate(pattern.field_name, count)
