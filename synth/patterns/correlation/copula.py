"""
Copula-based correlation analysis and generation.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Tuple
import numpy as np
import pandas as pd
from scipy import stats
from scipy.linalg import cholesky


class CopulaType(str, Enum):
    """Types of copulas for multivariate generation."""

    GAUSSIAN = "gaussian"
    T_STUDENT = "t"
    VINE = "vine"
    KDE = "kde"  # Kernel density estimation


@dataclass
class CorrelationPattern:
    """Learned correlation pattern for multivariate generation."""

    field_order: list[str]
    correlation_matrix: np.ndarray  # Correlation matrix
    copula_type: CopulaType
    quality_score: float = 1.0

    # Additional metadata
    is_positive_definite: bool = True
    eigenvalues: Optional[np.ndarray] = None
    condition_number: Optional[float] = None


class MultivariateAnalyzer:
    """
    Analyze multivariate patterns in data.

    Learns correlation structure and selects appropriate copula
    for preserving multivariate relationships.
    """

    def __init__(self, significance_level: float = 0.05):
        """Initialize analyzer."""
        self.significance_level = significance_level

    def learn_correlation(
        self,
        df: pd.DataFrame,
        numeric_columns: Optional[list[str]] = None
    ) -> CorrelationPattern:
        """
        Learn correlation pattern from numeric data.

        Args:
            df: Input dataframe
            numeric_columns: List of numeric columns (auto-detected if None)

        Returns:
            CorrelationPattern with learned correlation matrix
        """
        # Auto-detect numeric columns if not specified
        if numeric_columns is None:
            numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()

        if len(numeric_columns) < 2:
            raise ValueError("Need at least 2 numeric columns for correlation analysis")

        # Compute correlation matrix
        corr_matrix = self._compute_correlation_matrix(df[numeric_columns])

        # Check positive definiteness
        is_pd, eigenvalues = self._check_positive_definite(corr_matrix)
        condition_number = np.max(eigenvalues) / (np.min(eigenvalues) + 1e-10)

        # Select copula type
        copula_type = self._select_copula_type(df[numeric_columns], corr_matrix)

        # Compute quality score
        quality_score = self._compute_quality_score(df[numeric_columns], corr_matrix)

        return CorrelationPattern(
            field_order=numeric_columns,
            correlation_matrix=corr_matrix,
            copula_type=copula_type,
            quality_score=quality_score,
            is_positive_definite=is_pd,
            eigenvalues=eigenvalues,
            condition_number=condition_number,
        )

    def _compute_correlation_matrix(self, df: pd.DataFrame) -> np.ndarray:
        """Compute Pearson correlation matrix."""
        # Drop rows with NaN values
        clean_df = df.dropna()
        if len(clean_df) < 10:
            raise ValueError("Insufficient data for correlation analysis")

        return clean_df.corr().to_numpy()

    def _check_positive_definite(
        self,
        matrix: np.ndarray
    ) -> Tuple[bool, np.ndarray]:
        """Check if matrix is positive definite."""
        eigenvalues = np.linalg.eigvalsh(matrix)
        is_pd = np.all(eigenvalues > 0)
        return is_pd, eigenvalues

    def _select_copula_type(
        self,
        df: pd.DataFrame,
        corr_matrix: np.ndarray
    ) -> CopulaType:
        """Select appropriate copula type based on data characteristics."""
        # Start with Gaussian (default, most widely used)
        # Could extend with more sophisticated selection logic
        return CopulaType.GAUSSIAN

    def _compute_quality_score(
        self,
        df: pd.DataFrame,
        corr_matrix: np.ndarray
    ) -> float:
        """Compute quality score for correlation matrix."""
        # Check determinant (should be non-zero for full rank)
        det = np.linalg.det(corr_matrix)

        # Check condition number
        eigenvalues = np.linalg.eigvalsh(corr_matrix)
        condition_number = np.max(eigenvalues) / (np.abs(np.min(eigenvalues)) + 1e-10)

        # Quality score based on condition number and rank
        rank = np.linalg.matrix_rank(corr_matrix)
        max_rank = min(corr_matrix.shape)

        rank_score = rank / max_rank
        condition_score = 1.0 / (1.0 + np.log10(condition_number))

        return 0.5 * rank_score + 0.5 * condition_score


class CopulaGenerator:
    """
    Generate correlated data using copulas.

    Uses copula methods to preserve multivariate relationships
    during synthetic data generation.
    """

    def __init__(self, seed: Optional[int] = None):
        """Initialize generator."""
        self.seed = seed
        if seed is not None:
            np.random.seed(seed)

    def generate(
        self,
        pattern: CorrelationPattern,
        marginals: dict[str, np.ndarray],
        count: int
    ) -> pd.DataFrame:
        """
        Generate correlated samples using copulas.

        Args:
            pattern: Correlation pattern with correlation matrix
            marginals: Dictionary mapping field names to marginal distributions
            count: Number of samples to generate

        Returns:
            DataFrame with correlated samples
        """
        if pattern.copula_type == CopulaType.GAUSSIAN:
            return self._generate_gaussian_copula(pattern, marginals, count)
        else:
            raise ValueError(f"Copula type {pattern.copula_type} not yet implemented")

    def _generate_gaussian_copula(
        self,
        pattern: CorrelationPattern,
        marginals: dict[str, np.ndarray],
        count: int
    ) -> pd.DataFrame:
        """
        Generate samples using Gaussian copula.

        Algorithm:
        1. Generate correlated uniform samples using correlation matrix
        2. Transform to correlated Gaussian samples
        3. Apply inverse CDF of each marginal distribution
        """
        # Ensure correlation matrix is positive definite
        corr_matrix = self._ensure_positive_definite(pattern.correlation_matrix)

        # Generate correlated standard normal samples
        mean = np.zeros(len(pattern.field_order))
        normal_samples = np.random.multivariate_normal(
            mean,
            corr_matrix,
            size=count
        )

        # Transform to uniform using Gaussian CDF
        uniform_samples = stats.norm.cdf(normal_samples)

        # Transform uniform samples using inverse CDF of marginals
        result = pd.DataFrame()
        for i, field in enumerate(pattern.field_order):
            if field in marginals:
                # Apply inverse CDF transformation
                result[field] = self._apply_inverse_cdf(
                    uniform_samples[:, i],
                    marginals[field]
                )
            else:
                # Fallback: just use uniform samples
                result[field] = uniform_samples[:, i]

        return result

    def _ensure_positive_definite(
        self,
        matrix: np.ndarray,
        reg_param: float = 1e-6
    ) -> np.ndarray:
        """Ensure matrix is positive definite using regularization."""
        # Add small regularization term to diagonal
        n = matrix.shape[0]
        regularized = matrix + reg_param * np.eye(n)

        # Try Cholesky decomposition
        try:
            cholesky(regularized)
            return regularized
        except np.linalg.LinAlgError:
            # Use nearPD method as fallback
            return self._near_positive_definite(matrix)

    def _near_positive_definite(
        self,
        matrix: np.ndarray,
        max_iter: int = 100,
        tol: float = 1e-8
    ) -> np.ndarray:
        """Find nearest positive definite matrix."""
        # Simple approach: eigenvalue decomposition
        eigenvalues, eigenvectors = np.linalg.eigh(matrix)

        # Set negative eigenvalues to small positive value
        eigenvalues = np.maximum(eigenvalues, tol)

        # Reconstruct matrix
        return eigenvectors @ np.diag(eigenvalues) @ eigenvectors.T

    def _apply_inverse_cdf(
        self,
        uniform_samples: np.ndarray,
        marginal_data: np.ndarray
    ) -> np.ndarray:
        """
        Apply inverse CDF transformation.

        Uses empirical quantile function from marginal data.
        """
        # Compute empirical quantiles
        quantiles = np.linspace(0, 1, len(marginal_data))
        sorted_data = np.sort(marginal_data)

        # Interpolate to get inverse CDF values
        return np.interp(uniform_samples, quantiles, sorted_data)
