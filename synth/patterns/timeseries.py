"""
Time-series pattern learning and generation.

This module provides time-series specific pattern detection,
including trend, seasonality, and autocorrelation analysis.
"""

from dataclasses import dataclass, field
from typing import Optional, Any, Tuple
from enum import Enum
import numpy as np
import pandas as pd
from scipy import stats
from scipy.fft import fft, fftfreq


class SeasonalityType(str, Enum):
    """Types of seasonality patterns."""

    NONE = "none"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    CUSTOM = "custom"


class TrendType(str, Enum):
    """Types of trend patterns."""

    NONE = "none"
    LINEAR = "linear"
    EXPONENTIAL = "exponential"
    LOGARITHMIC = "logarithmic"
    POLYNOMIAL = "polynomial"


@dataclass
class TimeSeriesPattern:
    """
    Complete time-series pattern for generation.

    Contains trend, seasonality, autocorrelation, and noise
    characteristics for realistic time-series generation.
    """

    column_name: str

    # Time information
    time_column: str
    frequency: str  # pandas frequency alias (e.g., 'D', 'H', 'M')
    start_time: Optional[str] = None
    end_time: Optional[str] = None

    # Trend parameters
    trend_type: TrendType = TrendType.NONE
    trend_slope: float = 0.0
    trend_intercept: float = 0.0

    # Seasonality parameters
    seasonality_type: SeasonalityType = SeasonalityType.NONE
    seasonality_period: int = 0
    seasonality_amplitude: float = 0.0
    seasonality_phase: float = 0.0

    # Autocorrelation parameters
    acf: list[float] = field(default_factory=list)  # Autocorrelation function
    pacf: list[float] = field(default_factory=list)  # Partial autocorrelation
    ar_order: int = 0  # Auto-regressive order
    ma_order: int = 0  # Moving average order

    # Noise parameters
    noise_type: str = "gaussian"  # gaussian, laplacian, student_t
    noise_params: dict = field(default_factory=dict)  # mean, std, df, etc.

    # Statistical properties
    mean: float = 0.0
    std: float = 1.0
    min_value: Optional[float] = None
    max_value: Optional[float] = None

    # ARIMA parameters (if fitted)
    arima_params: Optional[dict] = None  # (p, d, q) and coefficients


class TimeSeriesAnalyzer:
    """
    Analyze time-series data to extract patterns.

    Detects trends, seasonality, autocorrelation, and noise
    characteristics for realistic time-series generation.
    """

    def __init__(self, significance_level: float = 0.05):
        """
        Initialize analyzer.

        Args:
            significance_level: Threshold for statistical tests
        """
        self.significance_level = significance_level

    def analyze(
        self,
        df: pd.DataFrame,
        value_column: str,
        time_column: str,
        max_lag: int = 50,
    ) -> TimeSeriesPattern:
        """
        Analyze time-series data and extract patterns.

        Args:
            df: Input dataframe
            value_column: Column containing time-series values
            time_column: Column containing timestamps
            max_lag: Maximum lag for ACF/PACF analysis

        Returns:
            TimeSeriesPattern with extracted characteristics
        """
        # Prepare time series
        ts = self._prepare_timeseries(df, value_column, time_column)

        # Detect frequency
        frequency = self._detect_frequency(df[time_column])

        # Analyze trend
        trend_type, slope, intercept = self._detect_trend(ts)

        # Analyze seasonality
        seasonality_type, period, amplitude, phase = self._detect_seasonality(ts, frequency)

        # Compute ACF and PACF
        acf, pacf, ar_order, ma_order = self._compute_autocorrelation(ts, max_lag)

        # Analyze noise
        noise_type, noise_params = self._analyze_noise(ts, trend_type, slope, seasonality_type)

        # Get statistics
        mean, std, min_val, max_val = ts.mean(), ts.std(), ts.min(), ts.max()

        return TimeSeriesPattern(
            column_name=value_column,
            time_column=time_column,
            frequency=frequency,
            start_time=str(df[time_column].min()),
            end_time=str(df[time_column].max()),
            trend_type=trend_type,
            trend_slope=slope,
            trend_intercept=intercept,
            seasonality_type=seasonality_type,
            seasonality_period=period,
            seasonality_amplitude=amplitude,
            seasonality_phase=phase,
            acf=acf,
            pacf=pacf,
            ar_order=ar_order,
            ma_order=ma_order,
            noise_type=noise_type,
            noise_params=noise_params,
            mean=mean,
            std=std,
            min_value=min_val,
            max_value=max_val,
        )

    def _prepare_timeseries(
        self, df: pd.DataFrame, value_column: str, time_column: str
    ) -> pd.Series:
        """Prepare time series for analysis."""
        # Ensure time column is datetime
        df = df.copy()
        df[time_column] = pd.to_datetime(df[time_column])

        # Sort by time
        df = df.sort_values(time_column)

        # Remove nulls
        df = df.dropna(subset=[value_column])

        return df[value_column].reset_index(drop=True)

    def _detect_frequency(self, time_series: pd.Series) -> str:
        """Detect the frequency of time series."""
        # Convert to datetime if not already
        if not pd.api.types.is_datetime64_any_dtype(time_series):
            time_series = pd.to_datetime(time_series)

        # Calculate time differences
        time_diffs = time_series.diff().dropna()

        if len(time_diffs) == 0:
            return "D"  # Default to daily

        # Get median time difference
        median_diff = time_diffs.median()

        # Map to pandas frequency alias
        if median_diff.total_seconds() < 3600:  # Less than 1 hour
            return "S"  # Second-level
        elif median_diff.total_seconds() < 86400:  # Less than 1 day
            return "H"  # Hourly
        elif median_diff.total_seconds() < 86400 * 7:  # Less than 1 week
            return "D"  # Daily
        elif median_diff.total_seconds() < 86400 * 30:  # Less than 1 month
            return "W"  # Weekly
        elif median_diff.total_seconds() < 86400 * 365:  # Less than 1 year
            return "M"  # Monthly
        else:
            return "Y"  # Yearly

    def _detect_trend(self, ts: pd.Series) -> Tuple[TrendType, float, float]:
        """Detect trend type and parameters."""
        x = np.arange(len(ts))
        y = ts.values

        # Fit linear trend
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)

        # Determine if trend is significant
        if p_value < self.significance_level and abs(r_value) > 0.3:
            # Check for exponential trend
            log_y = np.log(y - y.min() + 1)
            log_slope, _, log_r, log_p, _ = stats.linregress(x, log_y)

            if log_p < self.significance_level and abs(log_r) > abs(r_value):
                return TrendType.EXPONENTIAL, log_slope, np.exp(intercept)
            else:
                return TrendType.LINEAR, slope, intercept
        else:
            return TrendType.NONE, 0.0, 0.0

    def _detect_seasonality(
        self, ts: pd.Series, frequency: str
    ) -> Tuple[SeasonalityType, int, float, float]:
        """Detect seasonality type and parameters."""
        if len(ts) < 20:
            return SeasonalityType.NONE, 0, 0.0, 0.0

        # Estimate period based on frequency
        period_guess = self._guess_period(frequency, len(ts))

        if period_guess is None or period_guess >= len(ts) // 2:
            return SeasonalityType.NONE, 0, 0.0, 0.0

        # Perform FFT to detect seasonality
        values = ts.values
        values = values - np.mean(values)

        fft_vals = fft(values)
        power = np.abs(fft_vals) ** 2
        freqs = fftfreq(len(values))

        # Find dominant frequency (excluding DC component)
        positive_freqs = freqs[1:len(freqs)//2]
        positive_power = power[1:len(power)//2]

        if len(positive_power) == 0:
            return SeasonalityType.NONE, 0, 0.0, 0.0

        dominant_idx = np.argmax(positive_power)
        dominant_freq = positive_freqs[dominant_idx]

        if dominant_freq == 0:
            return SeasonalityType.NONE, 0, 0.0, 0.0

        # Estimate period
        detected_period = int(1.0 / dominant_freq) if dominant_freq > 0 else period_guess

        # Estimate amplitude using sine fitting
        t = np.arange(len(values))
        if detected_period < len(values):
            try:
                # Fit A*sin(2*pi*t/period + phi)
                from scipy.optimize import curve_fit

                def sine_func(x, A, phi):
                    return A * np.sin(2 * np.pi * x / detected_period + phi)

                try:
                    params, _ = curve_fit(sine_func, t, values, p0=[np.std(values), 0.0])
                    amplitude, phase = params
                except:
                    amplitude, phase = np.std(values), 0.0
            except:
                amplitude, phase = np.std(values), 0.0
        else:
            amplitude, phase = np.std(values), 0.0

        # Determine seasonality type
        seasonality_type = SeasonalityType.NONE
        if detected_period > 0:
            if period_guess == 24:
                seasonality_type = SeasonalityType.DAILY
            elif period_guess == 7:
                seasonality_type = SeasonalityType.WEEKLY
            elif period_guess == 30:
                seasonality_type = SeasonalityType.MONTHLY
            elif period_guess == 90:
                seasonality_type = SeasonalityType.QUARTERLY
            elif period_guess == 365:
                seasonality_type = SeasonalityType.YEARLY
            else:
                seasonality_type = SeasonalityType.CUSTOM

        return seasonality_type, detected_period, abs(amplitude), phase

    def _guess_period(self, frequency: str, data_length: int) -> Optional[int]:
        """Guess seasonality period based on frequency."""
        period_map = {
            "S": 86400,  # Seconds in a day
            "H": 24,  # Hours in a day
            "D": 7,  # Days in a week
            "W": 4,  # Weeks in a month
            "M": 12,  # Months in a year
        }
        return period_map.get(frequency)

    def _compute_autocorrelation(
        self, ts: pd.Series, max_lag: int
    ) -> Tuple[list[float], list[float], int, int]:
        """Compute ACF and PACF, estimate AR/MA orders."""
        from statsmodels.tsa.stattools import acf, pacf

        # Compute ACF and PACF
        acf_values = acf(ts, nlags=max_lag, alpha=None)
        pacf_values = pacf(ts, nlags=min(max_lag, len(ts)//4), alpha=None)

        # Estimate AR order (PACF cutoff)
        ar_order = 0
        for i in range(1, len(pacf_values)):
            if abs(pacf_values[i]) > 0.1:  # Threshold
                ar_order = i

        # Estimate MA order (ACF cutoff)
        ma_order = 0
        for i in range(1, len(acf_values)):
            if abs(acf_values[i]) > 0.1:  # Threshold
                ma_order = i

        return acf_values.tolist(), pacf_values.tolist(), ar_order, ma_order

    def _analyze_noise(
        self, ts: pd.Series, trend_type: TrendType, slope: float,
        seasonality_type: SeasonalityType
    ) -> Tuple[str, dict]:
        """Analyze noise characteristics."""
        # Detrend and deseasonalize
        residuals = ts.copy().values
        x = np.arange(len(ts))

        # Remove trend
        if trend_type == TrendType.LINEAR:
            residuals = residuals - (slope * x + ts.mean())
        elif trend_type == TrendType.EXPONENTIAL:
            residuals = residuals - (np.exp(slope * x) * ts.mean())

        # Test noise distribution
        # Kolmogorov-Smirnov test for normality
        _, ks_p = stats.kstest(residuals, "norm")

        if ks_p > self.significance_level:
            return "gaussian", {"mean": 0.0, "std": np.std(residuals)}
        else:
            # Test for Laplacian (exponential decay)
            # Fall back to gaussian if no clear pattern
            return "gaussian", {"mean": 0.0, "std": np.std(residuals)}
