"""
Differential privacy for synthetic data generation.

Provides differential privacy mechanisms for privacy-preserving
data generation using noise injection and privacy budget tracking.
"""

from dataclasses import dataclass, field
from typing import Optional, Any, Callable
from enum import Enum
import numpy as np
import pandas as pd


class MechanismType(str, Enum):
    """Types of differential privacy mechanisms."""

    LAPLACE = "laplace"
    GAUSSIAN = "gaussian"
    EXPONENTIAL = "exponential"
    LOCAL = "local"


@dataclass
class PrivacyBudget:
    """Track privacy budget usage."""

    epsilon: float  # Total privacy budget
    delta: float = 1e-5  # Delta for Gaussian mechanism

    # Usage tracking
    used_epsilon: float = 0.0
    used_delta: float = 0.0

    def remaining_budget(self) -> tuple[float, float]:
        """Get remaining privacy budget."""
        return self.epsilon - self.used_epsilon, self.delta - self.used_delta

    def can_spend(self, epsilon: float, delta: float = 0.0) -> bool:
        """Check if we can spend this much privacy budget."""
        rem_eps, rem_delta = self.remaining_budget()
        return epsilon <= rem_eps and delta <= rem_delta

    def spend(self, epsilon: float, delta: float = 0.0) -> bool:
        """Spend privacy budget."""
        if not self.can_spend(epsilon, delta):
            return False
        self.used_epsilon += epsilon
        self.used_delta += delta
        return True


class DPMechanism:
    """Base class for differential privacy mechanisms."""

    def __init__(
        self,
        epsilon: float,
        delta: float = 0.0,
        sensitivity: float = 1.0,
    ):
        """
        Initialize mechanism.

        Args:
            epsilon: Privacy parameter
            delta: Delta for Gaussian mechanism
            sensitivity: Global sensitivity of the query
        """
        self.epsilon = epsilon
        self.delta = delta
        self.sensitivity = sensitivity


class LaplaceMechanism(DPMechanism):
    """
    Laplace mechanism for differential privacy.

    Adds Laplace noise calibrated to sensitivity and epsilon.
    """

    def __init__(self, epsilon: float, sensitivity: float = 1.0):
        """Initialize Laplace mechanism."""
        super().__init__(epsilon, 0.0, sensitivity)

        # Scale parameter for Laplace distribution
        self.scale = sensitivity / epsilon

    def add_noise(self, value: float | np.ndarray) -> float | np.ndarray:
        """Add Laplace noise to value(s)."""
        noise = np.random.laplace(0, self.scale, size=np.shape(value))
        return value + noise

    def query(self, data: np.ndarray, func: Callable) -> float:
        """
        Run query with differential privacy.

        Args:
            data: Input data
            func: Function to apply to data

        Returns:
            Differentially private result
        """
        result = func(data)
        return self.add_noise(result)


class GaussianMechanism(DPMechanism):
    """
    Gaussian mechanism for differential privacy.

    Adds Gaussian noise for (epsilon, delta)-DP.
    """

    def __init__(
        self,
        epsilon: float,
        delta: float = 1e-5,
        sensitivity: float = 1.0,
    ):
        """Initialize Gaussian mechanism."""
        super().__init__(epsilon, delta, sensitivity)

        # Standard deviation for Gaussian distribution
        # sigma = sensitivity * sqrt(2 * ln(1.25/delta)) / epsilon
        import math
        self.sigma = sensitivity * math.sqrt(2 * math.log(1.25 / delta)) / epsilon

    def add_noise(self, value: float | np.ndarray) -> float | np.ndarray:
        """Add Gaussian noise to value(s)."""
        noise = np.random.normal(0, self.sigma, size=np.shape(value))
        return value + noise

    def query(self, data: np.ndarray, func: Callable) -> float:
        """
        Run query with differential privacy.

        Args:
            data: Input data
            func: Function to apply to data

        Returns:
            Differentially private result
        """
        result = func(data)
        return self.add_noise(result)


class DPGenerator:
    """
    Generate synthetic data with differential privacy.

    Uses differential privacy mechanisms to generate data
    while providing formal privacy guarantees.
    """

    def __init__(
        self,
        privacy_budget: PrivacyBudget,
        mechanism_type: MechanismType = MechanismType.LAPLACE,
    ):
        """
        Initialize generator.

        Args:
            privacy_budget: Privacy budget to track
            mechanism_type: Type of DP mechanism to use
        """
        self.privacy_budget = privacy_budget
        self.mechanism_type = mechanism_type

    def generate_numeric(
        self,
        count: int,
        mean: float,
        std: float,
        min_val: Optional[float] = None,
        max_val: Optional[float] = None,
        per_record_epsilon: float = 0.1,
    ) -> np.ndarray:
        """
        Generate differentially private numeric data.

        Args:
            count: Number of records to generate
            mean: True mean (from original data)
            std: True standard deviation
            min_val: Optional minimum value
            max_val: Optional maximum value
            per_record_epsilon: Epsilon to spend per record

        Returns:
            Differentially private numeric array
        """
        # Calculate sensitivity (based on range)
        sensitivity = (max_val - min_val) if min_val is not None and max_val is not None else 4 * std

        # Create mechanism
        if self.mechanism_type == MechanismType.LAPLACE:
            mechanism = LaplaceMechanism(per_record_epsilon, sensitivity)
        else:
            mechanism = GaussianMechanism(per_record_epsilon, 1e-5, sensitivity)

        # Generate base data
        data = np.random.normal(mean, std, count)

        # Add noise to each value
        noisy_data = mechanism.add_noise(data)

        # Clip to bounds
        if min_val is not None:
            noisy_data = np.maximum(noisy_data, min_val)
        if max_val is not None:
            noisy_data = np.minimum(noisy_data, max_val)

        # Update privacy budget
        total_epsilon = per_record_epsilon * count
        self.privacy_budget.spend(total_epsilon)

        return noisy_data

    def generate_categorical(
        self,
        count: int,
        probabilities: dict[str, float],
        epsilon: float = 1.0,
    ) -> list[str]:
        """
        Generate differentially private categorical data.

        Uses the exponential mechanism for categorical selection.

        Args:
            count: Number of records to generate
            probabilities: True value probabilities
            epsilon: Privacy parameter

        Returns:
            List of categories
        """
        # Add noise to probabilities using exponential mechanism
        values = list(probabilities.keys())
        probs = np.array(list(probabilities.values()))

        # Score function: log probability
        scores = np.log(probs + 1e-10)

        # Exponential mechanism sampling
        selections = []
        for _ in range(count):
            # Compute sampling probabilities
            scaled_scores = epsilon * scores / (2 * np.max(np.abs(scores)))
            exp_scores = np.exp(scaled_scores - np.max(scaled_scores))
            sample_probs = exp_scores / exp_scores.sum()

            # Sample
            idx = np.random.choice(len(values), p=sample_probs)
            selections.append(values[idx])

        # Update privacy budget
        self.privacy_budget.spend(epsilon)

        return selections

    def generate_histogram(
        self,
        data: np.ndarray,
        bins: int,
        epsilon: float = 1.0,
    ) -> tuple[np.ndarray, np.ndarray]:
        """
        Generate differentially private histogram.

        Args:
            data: Input data
            bins: Number of bins
            epsilon: Privacy parameter

        Returns:
            (bin_counts, bin_edges)
        """
        # Compute true histogram
        counts, edges = np.histogram(data, bins=bins)

        # Add noise to counts
        if self.mechanism_type == MechanismType.LAPLACE:
            mechanism = LaplaceMechanism(epsilon, sensitivity=1.0)
        else:
            mechanism = GaussianMechanism(epsilon, 1e-5, sensitivity=1.0)

        noisy_counts = mechanism.add_noise(counts)
        noisy_counts = np.maximum(noisy_counts, 0)  # Ensure non-negative

        # Update privacy budget
        self.privacy_budget.spend(epsilon)

        return noisy_counts, edges


class LocalDP:
    """
    Local differential privacy for randomization.

    Applies local differential privacy at the data collection point.
    """

    def __init__(self, epsilon: float):
        """
        Initialize local DP.

        Args:
            epsilon: Privacy parameter
        """
        self.epsilon = epsilon

    def randomize_response(self, value: Any, domain: list[Any]) -> Any:
        """
        Randomize a value using randomized response.

        Args:
            value: True value
            domain: Domain of possible values

        Returns:
            Randomized value
        """
        # Probability of keeping true value
        p_keep = np.exp(self.epsilon) / (np.exp(self.epsilon) + len(domain) - 1)

        if np.random.random() < p_keep:
            return value
        else:
            # Random selection from other values
            other_values = [v for v in domain if v != value]
            return np.random.choice(other_values)

    def randomize_numeric(self, value: float, min_val: float, max_val: float) -> float:
        """
        Randomize numeric value using local DP.

        Args:
            value: True value
            min_val: Minimum possible value
            max_val: Maximum possible value

        Returns:
            Randomized value
        """
        # Use harmonic encoding
        range_size = max_val - min_val

        # Add noise calibrated to range
        sensitivity = range_size
        scale = sensitivity / self.epsilon

        noise = np.random.laplace(0, scale)
        noisy_value = value + noise

        # Clip to bounds
        return max(min_val, min(max_val, noisy_value))
