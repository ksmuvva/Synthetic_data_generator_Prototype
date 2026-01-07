"""
Time-series sampler for generating synthetic time-series data.

Generates realistic time-series data preserving trends, seasonality,
and autocorrelation patterns.
"""

from typing import Optional
import numpy as np
import pandas as pd
from dataclasses import dataclass

from synth.patterns.timeseries import (
    TimeSeriesPattern,
    TrendType,
    SeasonalityType,
)
from synth.generation.sampler import StatisticalSampler
from synth.core.errors import GenerationError


class TimeSeriesGenerator:
    """
    Generate synthetic time-series data.

    Creates time-series data with learned trends, seasonality,
    and noise characteristics.
    """

    def __init__(self, seed: Optional[int] = None):
        """Initialize generator."""
        self.seed = seed
        if seed is not None:
            np.random.seed(seed)

    def generate(
        self,
        pattern: TimeSeriesPattern,
        count: int,
        start_date: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Generate time-series data.

        Args:
            pattern: Learned time-series pattern
            count: Number of time points to generate
            start_date: Optional start date (uses pattern start if None)

        Returns:
            DataFrame with time and value columns
        """
        # Create time index
        if start_date:
            start = pd.Timestamp(start_date)
        else:
            start = pd.Timestamp(pattern.start_time) if pattern.start_time else pd.Timestamp.now()

        time_index = pd.date_range(start=start, periods=count, freq=pattern.frequency)

        # Initialize values
        values = np.zeros(count)

        # Add trend
        values = self._add_trend(values, pattern)

        # Add seasonality
        values = self._add_seasonality(values, pattern)

        # Add noise
        values = self._add_noise(values, pattern)

        # Add autocorrelation
        values = self._add_autocorrelation(values, pattern)

        # Apply bounds
        if pattern.min_value is not None:
            values = np.maximum(values, pattern.min_value)
        if pattern.max_value is not None:
            values = np.minimum(values, pattern.max_value)

        # Create DataFrame
        df = pd.DataFrame({
            pattern.time_column: time_index,
            pattern.column_name: values,
        })

        return df

    def _add_trend(self, values: np.ndarray, pattern: TimeSeriesPattern) -> np.ndarray:
        """Add trend component."""
        x = np.arange(len(values))

        if pattern.trend_type == TrendType.LINEAR:
            return values + pattern.trend_slope * x + pattern.trend_intercept
        elif pattern.trend_type == TrendType.EXPONENTIAL:
            return values + np.exp(pattern.trend_slope * x) * pattern.trend_intercept
        elif pattern.trend_type == TrendType.LOGARITHMIC:
            return values + pattern.trend_slope * np.log(x + 1) + pattern.trend_intercept
        else:
            return values + pattern.mean

    def _add_seasonality(self, values: np.ndarray, pattern: TimeSeriesPattern) -> np.ndarray:
        """Add seasonal component."""
        if pattern.seasonality_type == SeasonalityType.NONE:
            return values

        if pattern.seasonality_period <= 0:
            return values

        x = np.arange(len(values))
        seasonal = pattern.seasonality_amplitude * np.sin(
            2 * np.pi * x / pattern.seasonality_period + pattern.seasonality_phase
        )

        return values + seasonal

    def _add_noise(self, values: np.ndarray, pattern: TimeSeriesPattern) -> np.ndarray:
        """Add noise component."""
        noise_params = pattern.noise_params

        if pattern.noise_type == "gaussian":
            noise = np.random.normal(
                noise_params.get("mean", 0.0),
                noise_params.get("std", 1.0),
                len(values)
            )
        elif pattern.noise_type == "laplacian":
            noise = np.random.laplace(
                noise_params.get("mean", 0.0),
                noise_params.get("scale", 1.0),
                len(values)
            )
        else:
            # Default to gaussian
            noise = np.random.normal(0, pattern.std, len(values))

        return values + noise

    def _add_autocorrelation(self, values: np.ndarray, pattern: TimeSeriesPattern) -> np.ndarray:
        """Add autocorrelation using AR model."""
        if pattern.ar_order == 0 or len(pattern.acf) == 0:
            return values

        # Simple AR(1) model
        phi = pattern.acf[1] if len(pattern.acf) > 1 else 0.5

        for i in range(1, len(values)):
            values[i] = phi * values[i-1] + (1 - phi) * values[i]

        return values


class ARIMAGenerator:
    """
    Generate time-series using ARIMA models.

    Uses ARIMA parameters learned from data to generate
    realistic autocorrelated time-series.
    """

    def __init__(self, seed: Optional[int] = None):
        """Initialize generator."""
        self.seed = seed
        if seed is not None:
            np.random.seed(seed)

    def generate(
        self,
        pattern: TimeSeriesPattern,
        count: int,
    ) -> np.ndarray:
        """
        Generate using ARIMA model.

        Args:
            pattern: Time-series pattern with ARIMA parameters
            count: Number of time points to generate

        Returns:
            Generated time-series values
        """
        if pattern.arima_params is None:
            # Fall back to simple AR model
            return self._generate_ar(pattern, count)

        # Generate using ARIMA
        p = pattern.ar_order
        d = pattern.arima_params.get("d", 0)
        q = pattern.ma_order

        # Start with noise
        noise = np.random.normal(0, pattern.std, count + max(p, q))

        # Apply MA
        if q > 0:
            ma_coeffs = pattern.arima_params.get("ma_coeffs", [0.5] * q)
            for i in range(q, len(noise)):
                noise[i] = sum(ma_coeffs[j] * noise[i-j-1] for j in range(min(q, i)))

        # Apply AR
        if p > 0:
            ar_coeffs = pattern.arima_params.get("ar_coeffs", [0.5] * p)
            values = noise.copy()
            for i in range(p, len(values)):
                values[i] = sum(ar_coeffs[j] * values[i-j-1] for j in range(min(p, i))) + noise[i]
        else:
            values = noise

        # Apply differencing
        if d > 0:
            for _ in range(d):
                values = np.cumsum(values)

        return values[:count]

    def _generate_ar(self, pattern: TimeSeriesPattern, count: int) -> np.ndarray:
        """Generate using simple AR model."""
        if pattern.ar_order == 0:
            return np.random.normal(pattern.mean, pattern.std, count)

        # Use PACF for AR coefficients
        ar_coeffs = pattern.pacf[:pattern.ar_order] if len(pattern.pacf) > pattern.ar_order else [0.5]

        values = np.zeros(count)
        values[0] = pattern.mean

        for i in range(1, count):
            ar_part = sum(
                ar_coeffs[j] * (values[i-j-1] - pattern.mean)
                for j in range(min(pattern.ar_order, i))
            )
            noise = np.random.normal(0, pattern.std)
            values[i] = pattern.mean + ar_part + noise

        return values


class ProphetGenerator:
    """
    Generate time-series using Prophet-like models.

    Combines trend, seasonality, and holiday effects
    for realistic time-series generation.
    """

    def __init__(self, seed: Optional[int] = None):
        """Initialize generator."""
        self.seed = seed
        if seed is not None:
            np.random.seed(seed)

    def generate(
        self,
        pattern: TimeSeriesPattern,
        count: int,
        start_date: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Generate using Prophet-style model.

        Args:
            pattern: Time-series pattern
            count: Number of time points
            start_date: Optional start date

        Returns:
            DataFrame with time and value columns
        """
        # Create time index
        if start_date:
            start = pd.Timestamp(start_date)
        else:
            start = pd.Timestamp(pattern.start_time) if pattern.start_time else pd.Timestamp.now()

        time_index = pd.date_range(start=start, periods=count, freq=pattern.frequency)

        # Initialize
        values = np.zeros(count)

        # Add growth trend (logistic or linear)
        values = self._add_growth(values, pattern)

        # Add seasonality (Fourier series)
        values = self._add_fourier_seasonality(values, pattern)

        # Add noise
        values = self._add_noise(values, pattern)

        # Create DataFrame
        df = pd.DataFrame({
            pattern.time_column: time_index,
            pattern.column_name: values,
        })

        return df

    def _add_growth(self, values: np.ndarray, pattern: TimeSeriesPattern) -> np.ndarray:
        """Add growth trend."""
        x = np.arange(len(values))

        if pattern.trend_type == TrendType.EXPONENTIAL:
            # Saturating logistic growth
            k = pattern.max_value if pattern.max_value else pattern.mean * 2
            m = len(values) / 2
            sigma = pattern.trend_slope if pattern.trend_slope > 0 else 0.1

            growth = k / (1 + np.exp(-sigma * (x - m)))
            return values + growth
        else:
            # Linear growth
            return values + pattern.trend_slope * x + pattern.trend_intercept

    def _add_fourier_seasonality(self, values: np.ndarray, pattern: TimeSeriesPattern) -> np.ndarray:
        """Add seasonality using Fourier series."""
        if pattern.seasonality_type == SeasonalityType.NONE:
            return values

        period = pattern.seasonality_period
        if period <= 0:
            return values

        x = np.arange(len(values))
        n_terms = min(5, period // 2)  # Number of Fourier terms

        seasonal = np.zeros_like(values, dtype=float)

        for i in range(1, n_terms + 1):
            seasonal += (pattern.seasonality_amplitude / i) * np.sin(
                2 * np.pi * i * x / period + pattern.seasonality_phase
            )

        return values + seasonal

    def _add_noise(self, values: np.ndarray, pattern: TimeSeriesPattern) -> np.ndarray:
        """Add heteroscedastic noise."""
        noise_params = pattern.noise_params
        base_std = noise_params.get("std", pattern.std)

        # Add some heteroscedasticity (variance grows with value)
        std = base_std * (1 + 0.1 * np.abs(values) / (np.abs(values).mean() + 1e-10))

        noise = np.random.normal(0, 1, len(values)) * std

        return values + noise
