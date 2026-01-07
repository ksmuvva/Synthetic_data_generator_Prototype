"""
PII recognition and field masking.

Provides PII detection and masking capabilities for
privacy-preserving data handling.
"""

from dataclasses import dataclass, field
from typing import Optional, Any, Pattern
from enum import Enum
import re
import numpy as np
import pandas as pd


class PIICategory(str, Enum):
    """Categories of PII."""

    NAME = "name"
    EMAIL = "email"
    PHONE = "phone"
    SSN = "ssn"
    CREDIT_CARD = "credit_card"
    ADDRESS = "address"
    IP_ADDRESS = "ip_address"
    DATE_OF_BIRTH = "date_of_birth"
    PASSPORT = "passport"
    DRIVER_LICENSE = "driver_license"
    ACCOUNT_NUMBER = "account_number"
    MEDICAL_RECORD = "medical_record"


class MaskingMethod(str, Enum):
    """Methods for masking PII."""

    REDACT = "retract"  # Replace with ***
    HASH = "hash"  # Replace with hash
    TOKENIZE = "tokenize"  # Replace with token
    MASK = "mask"  # Partial masking (e.g., j***@gmail.com)
    NOISE = "noise"  # Add noise to numeric values
    GENERALIZE = "generalize"  # Generalize to broader category


@dataclass
class PIIField:
    """Field containing PII."""

    field_name: str
    category: PIICategory
    confidence: float  # 0.0 to 1.0
    masking_method: MaskingMethod = MaskingMethod.MASK


@dataclass
class MaskingRule:
    """Rule for masking a field."""

    field_name: str
    method: MaskingMethod
    parameters: dict[str, Any] = field(default_factory=dict)


class PIIRecognizer:
    """
    Recognize PII in data.

    Uses pattern matching and heuristics to detect PII fields.
    """

    # PII patterns
    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    PHONE_PATTERN = re.compile(r'^\+?[\d\s\-\(\)]{10,}$')
    SSN_PATTERN = re.compile(r'^\d{3}-\d{2}-\d{4}$|^\d{9}$')
    CREDIT_CARD_PATTERN = re.compile(r'^\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}$')
    IP_PATTERN = re.compile(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$')

    def __init__(self):
        """Initialize recognizer."""
        self.field_keywords = {
            PIICategory.NAME: ["name", "first_name", "last_name", "full_name"],
            PIICategory.EMAIL: ["email", "email_address", "mail"],
            PIICategory.PHONE: ["phone", "telephone", "mobile", "cell"],
            PIICategory.SSN: ["ssn", "social_security", "social"],
            PIICategory.CREDIT_CARD: ["credit_card", "card_number", "cc_number"],
            PIICategory.ADDRESS: ["address", "street", "city", "state", "zip"],
            PIICategory.IP_ADDRESS: ["ip", "ip_address"],
            PIICategory.DATE_OF_BIRTH: ["dob", "birth_date", "birthday"],
            PIICategory.PASSPORT: ["passport", "passport_number"],
            PIICategory.DRIVER_LICENSE: ["driver_license", "dl_number", "license"],
            PIICategory.ACCOUNT_NUMBER: ["account", "account_number", "acct"],
        }

    def recognize_fields(self, df: pd.DataFrame) -> list[PIIField]:
        """
        Recognize PII fields in dataframe.

        Args:
            df: Input dataframe

        Returns:
            List of detected PII fields
        """
        pii_fields = []

        for col in df.columns:
            pii_type = self._detect_pii_type(df, col)

            if pii_type:
                confidence = self._estimate_confidence(df, col, pii_type)

                pii_fields.append(
                    PIIField(
                        field_name=col,
                        category=pii_type,
                        confidence=confidence,
                    )
                )

        return pii_fields

    def _detect_pii_type(self, df: pd.DataFrame, column: str) -> Optional[PIICategory]:
        """Detect PII type for a column."""
        col_lower = column.lower()

        # Check field name patterns
        for pii_type, keywords in self.field_keywords.items():
            if any(kw in col_lower for kw in keywords):
                return pii_type

        # Check data patterns
        sample_values = df[column].dropna().head(100)

        if len(sample_values) == 0:
            return None

        # Convert to string for pattern matching
        str_values = sample_values.astype(str)

        # Check email pattern
        if str_values.str.match(self.EMAIL_PATTERN, na=False).mean() > 0.8:
            return PIICategory.EMAIL

        # Check phone pattern
        if str_values.str.match(self.PHONE_PATTERN, na=False).mean() > 0.5:
            return PIICategory.PHONE

        # Check SSN pattern
        if str_values.str.match(self.SSN_PATTERN, na=False).mean() > 0.5:
            return PIICategory.SSN

        # Check credit card pattern
        if str_values.str.match(self.CREDIT_CARD_PATTERN, na=False).mean() > 0.5:
            return PIICategory.CREDIT_CARD

        # Check IP pattern
        if str_values.str.match(self.IP_PATTERN, na=False).mean() > 0.5:
            return PIICategory.IP_ADDRESS

        return None

    def _estimate_confidence(self, df: pd.DataFrame, column: str, pii_type: PIICategory) -> float:
        """Estimate confidence in PII detection."""
        col_lower = column.lower()

        # High confidence if field name contains PII keywords
        for keywords in self.field_keywords.values():
            if any(kw in col_lower for kw in keywords):
                return 0.9

        # Medium confidence if pattern match
        return 0.7


class FieldMasker:
    """
    Mask PII fields using various methods.

    Applies masking techniques to protect PII data.
    """

    def __init__(self):
        """Initialize masker."""
        self.recognizer = PIIRecognizer()

    def mask_dataframe(
        self,
        df: pd.DataFrame,
        pii_fields: Optional[list[PIIField]] = None,
        default_method: MaskingMethod = MaskingMethod.MASK,
    ) -> pd.DataFrame:
        """
        Mask PII fields in dataframe.

        Args:
            df: Input dataframe
            pii_fields: List of PII fields (auto-detected if None)
            default_method: Default masking method

        Returns:
            Dataframe with masked PII
        """
        df_masked = df.copy()

        # Auto-detect PII if not provided
        if pii_fields is None:
            pii_fields = self.recognizer.recognize_fields(df)

        # Apply masking
        for pii_field in pii_fields:
            if pii_field.field_name not in df.columns:
                continue

            method = pii_field.masking_method or default_method
            df_masked[pii_field.field_name] = self._mask_column(
                df[pii_field.field_name],
                pii_field.category,
                method,
            )

        return df_masked

    def _mask_column(
        self,
        series: pd.Series,
        category: PIICategory,
        method: MaskingMethod,
    ) -> pd.Series:
        """Mask a single column."""
        if method == MaskingMethod.REDACT:
            return series.apply(lambda x: "***REDACTED***" if pd.notna(x) else x)

        elif method == MaskingMethod.MASK:
            return self._partial_mask(series, category)

        elif method == MaskingMethod.HASH:
            return series.apply(
                lambda x: hash(str(x)) & 0xFFFFFFFF if pd.notna(x) else x
            )

        elif method == MaskingMethod.NOISE:
            return self._add_noise(series, category)

        else:
            return series

    def _partial_mask(self, series: pd.Series, category: PIICategory) -> pd.Series:
        """Apply partial masking."""
        def mask_value(value):
            if pd.isna(value):
                return value

            value = str(value)

            if category == PIICategory.EMAIL:
                # j***@gmail.com
                parts = value.split("@")
                if len(parts) == 2:
                    return parts[0][0] + "***@" + parts[1]
                return "***"

            elif category == PIICategory.PHONE:
                # +1 ***-***-1234
                if len(value) >= 4:
                    return "***" + value[-4:]
                return "***"

            elif category in (PIICategory.SSN, PIICategory.CREDIT_CARD):
                # ***-**-1234
                if len(value) >= 4:
                    return "***" + value[-4:]
                return "***"

            elif category == PIICategory.NAME:
                # J***
                if len(value) > 0:
                    return value[0] + "***"
                return "***"

            else:
                # Default: show first and last character
                if len(value) > 1:
                    return value[0] + "***" + value[-1]
                return "***"

        return series.apply(mask_value)

    def _add_noise(self, series: pd.Series, category: PIICategory) -> pd.Series:
        """Add noise to numeric PII."""
        if not pd.api.types.is_numeric_dtype(series):
            return series

        std = series.std()
        noise = np.random.normal(0, 0.01 * std, len(series))

        return series + noise


class DataMasker:
    """
    Complete data masking solution.

    Combines PII recognition and masking for comprehensive
    privacy protection.
    """

    def __init__(self):
        """Initialize data masker."""
        self.recognizer = PIIRecognizer()
        self.masker = FieldMasker()

    def analyze_and_mask(
        self,
        df: pd.DataFrame,
        masking_rules: Optional[list[MaskingRule]] = None,
        auto_detect: bool = True,
    ) -> tuple[pd.DataFrame, list[PIIField]]:
        """
        Analyze and mask PII in dataframe.

        Args:
            df: Input dataframe
            masking_rules: Optional explicit masking rules
            auto_detect: Auto-detect PII fields

        Returns:
            (Masked dataframe, detected PII fields)
        """
        # Detect PII fields
        pii_fields = []
        if auto_detect:
            pii_fields = self.recognizer.recognize_fields(df)

        # Apply explicit rules if provided
        if masking_rules:
            for rule in masking_rules:
                if rule.field_name in df.columns:
                    pii_fields.append(
                        PIIField(
                            field_name=rule.field_name,
                            category=PIICategory.ACCOUNT_NUMBER,  # Default category
                            confidence=1.0,
                            masking_method=rule.method,
                        )
                    )

        # Apply masking
        df_masked = self.masker.mask_dataframe(df, pii_fields)

        return df_masked, pii_fields
