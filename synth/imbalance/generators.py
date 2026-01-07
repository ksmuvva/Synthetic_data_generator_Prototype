"""
Class imbalance handling for synthetic data.

Provides SMOTE and other techniques for handling
imbalanced datasets in synthetic data generation.
"""

from dataclasses import dataclass, field
from typing import Optional, Any
from enum import Enum
import numpy as np
import pandas as pd


class ImbalanceMethod(str, Enum):
    """Methods for handling imbalance."""

    SMOTE = "smote"  # Synthetic Minority Over-sampling Technique
    ADASYN = "adasyn"  # Adaptive Synthetic Sampling
    OVERSAMPLING = "oversampling"  # Random oversampling
    UNDERSAMPLING = "undersampling"  # Random undersampling
    CLASS_WEIGHTS = "class_weights"  # Weighted sampling


@dataclass
class ImbalancePattern:
    """Pattern of class imbalance."""

    target_column: str
    minority_classes: list[Any]
    majority_classes: list[Any]

    # Statistics
    imbalance_ratio: float = 0.0  # minority/majority ratio
    minority_count: int = 0
    majority_count: int = 0


class SMOTEGenerator:
    """
    Generate synthetic samples using SMOTE.

    Creates synthetic minority samples by interpolating
    between existing minority instances.
    """

    def __init__(self, k_neighbors: int = 5, seed: Optional[int] = None):
        """
        Initialize generator.

        Args:
            k_neighbors: Number of nearest neighbors
            seed: Random seed
        """
        self.k_neighbors = k_neighbors
        self.seed = seed
        if seed is not None:
            np.random.seed(seed)

    def generate(
        self,
        df: pd.DataFrame,
        target_column: str,
        target_class: Any,
        count: int,
    ) -> pd.DataFrame:
        """
        Generate synthetic minority samples.

        Args:
            df: Input dataframe
            target_column: Target/class column
            target_class: Class to generate samples for
            count: Number of samples to generate

        Returns:
            Dataframe with new synthetic samples
        """
        # Get minority samples
        minority_df = df[df[target_column] == target_class].copy()

        if len(minority_df) == 0:
            return pd.DataFrame()

        # Get feature columns (excluding target)
        feature_cols = [c for c in df.columns if c != target_column]

        # Convert to numpy
        X = minority_df[feature_cols].values

        # Generate samples
        synthetic_samples = []
        for _ in range(count):
            # Randomly select a sample
            idx = np.random.randint(0, len(X))
            sample = X[idx]

            # Find k nearest neighbors
            distances = np.linalg.norm(X - sample, axis=1)
            nearest_indices = np.argsort(distances)[1:self.k_neighbors + 1]

            # Randomly select a neighbor
            neighbor_idx = np.random.choice(nearest_indices)
            neighbor = X[neighbor_idx]

            # Interpolate
            alpha = np.random.random()
            synthetic = sample + alpha * (neighbor - sample)

            synthetic_samples.append(synthetic)

        # Create dataframe
        synthetic_df = pd.DataFrame(synthetic_samples, columns=feature_cols)
        synthetic_df[target_column] = target_class

        return synthetic_df


class RareClassGenerator:
    """
    Generate samples for rare classes.

    Uses weighted sampling and augmentation to generate
    realistic rare class samples.
    """

    def __init__(self, seed: Optional[int] = None):
        """Initialize generator."""
        self.seed = seed
        if seed is not None:
            np.random.seed(seed)

    def generate(
        self,
        df: pd.DataFrame,
        target_column: str,
        target_class: Any,
        count: int,
        method: ImbalanceMethod = ImbalanceMethod.OVERSAMPLING,
    ) -> pd.DataFrame:
        """
        Generate rare class samples.

        Args:
            df: Input dataframe
            target_column: Target/class column
            target_class: Rare class to generate
            count: Number of samples
            method: Generation method

        Returns:
            Generated samples
        """
        class_df = df[df[target_column] == target_class].copy()

        if len(class_df) == 0:
            return pd.DataFrame()

        if method == ImbalanceMethod.OVERSAMPLING:
            return self._oversample(class_df, count, target_column)

        elif method == ImbalanceMethod.CLASS_WEIGHTS:
            return self._weighted_sample(class_df, count, target_column)

        return class_df

    def _oversample(
        self, class_df: pd.DataFrame, count: int, target_column: str
    ) -> pd.DataFrame:
        """Random oversampling with slight variation."""
        samples = []

        while len(samples) < count:
            # Sample with replacement
            sample = class_df.sample(n=1, replace=True)

            # Add small noise to numeric columns
            for col in sample.columns:
                if col != target_column and pd.api.types.is_numeric_dtype(sample[col]):
                    noise = np.random.normal(0, 0.01 * sample[col].std())
                    sample[col] = sample[col] + noise

            samples.append(sample)

        return pd.concat(samples, ignore_index=True)

    def _weighted_sample(
        self, class_df: pd.DataFrame, count: int, target_column: str
    ) -> pd.DataFrame:
        """Weighted sampling."""
        return class_df.sample(n=count, replace=True)


class ImbalanceHandler:
    """
    Handle class imbalance in synthetic data.

    Provides methods to detect and correct class imbalance.
    """

    def __init__(self):
        """Initialize handler."""
        self.smote_gen = SMOTEGenerator()
        self.rare_gen = RareClassGenerator()

    def detect_imbalance(
        self,
        df: pd.DataFrame,
        target_column: str,
        threshold: float = 0.2,
    ) -> Optional[ImbalancePattern]:
        """
        Detect class imbalance.

        Args:
            df: Input dataframe
            target_column: Target/class column
            threshold: Imbalance threshold

        Returns:
            ImbalancePattern if imbalance detected, None otherwise
        """
        value_counts = df[target_column].value_counts()

        if len(value_counts) < 2:
            return None

        # Find minority and majority classes
        minority_class = value_counts.idxmin()
        majority_class = value_counts.idxmax()

        minority_count = value_counts.min()
        majority_count = value_counts.max()

        imbalance_ratio = minority_count / majority_count

        if imbalance_ratio < threshold:
            return ImbalancePattern(
                target_column=target_column,
                minority_classes=[minority_class],
                majority_classes=[majority_class],
                imbalance_ratio=imbalance_ratio,
                minority_count=minority_count,
                majority_count=majority_count,
            )

        return None

    def balance_dataset(
        self,
        df: pd.DataFrame,
        target_column: str,
        method: ImbalanceMethod = ImbalanceMethod.SMOTE,
    ) -> pd.DataFrame:
        """
        Balance imbalanced dataset.

        Args:
            df: Input dataframe
            target_column: Target/class column
            method: Balancing method

        Returns:
            Balanced dataframe
        """
        pattern = self.detect_imbalance(df, target_column)

        if not pattern:
            return df

        balanced_dfs = [df]

        # Generate samples for minority classes
        for minority_class in pattern.minority_classes:
            target_count = pattern.majority_count

            if method == ImbalanceMethod.SMOTE:
                synthetic = self.smote_gen.generate(
                    df, target_column, minority_class,
                    target_count - pattern.minority_count
                )
            else:
                synthetic = self.rare_gen.generate(
                    df, target_column, minority_class,
                    target_count - pattern.minority_count,
                    method
                )

            balanced_dfs.append(synthetic)

        return pd.concat(balanced_dfs, ignore_index=True)
