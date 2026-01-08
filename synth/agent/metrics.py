"""
Metrics Collection System for the True AI Agent.

Provides comprehensive metrics tracking for:
- Performance metrics (latency, throughput)
- Quality metrics (validation scores, similarity)
- Resource metrics (memory, CPU, disk)
- Request metrics (success rate, error rate)
"""

import time
import psutil
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
import json
from collections import defaultdict

from synth.agent.config import MetricsConfig, get_config


@dataclass
class Metric:
    """Single metric measurement."""
    name: str
    value: float
    timestamp: datetime
    tags: Dict[str, str] = field(default_factory=dict)
    unit: Optional[str] = None


@dataclass
class MetricSummary:
    """Summary statistics for a metric."""
    name: str
    count: int
    min: float
    max: float
    avg: float
    sum: float
    unit: Optional[str] = None


class MetricsCollector:
    """
    Collects and aggregates metrics for the SYNTH AI Agent.

    Example:
        ```python
        from synth.agent.metrics import get_metrics_collector

        collector = get_metrics_collector()

        # Record a metric
        collector.record_metric("request_count", 1.0, tags={"type": "generate"})

        # Time an operation
        with collector.timer("data_generation"):
            generate_data()

        # Get summary
        summary = collector.get_summary("request_count")
        ```
    """

    def __init__(self, config: Optional[MetricsConfig] = None):
        """
        Initialize metrics collector.

        Args:
            config: Metrics configuration (uses global config if None)
        """
        self.config = config or get_config().metrics

        # Metric storage
        self._metrics: Dict[str, List[Metric]] = defaultdict(list)
        self._timings: Dict[str, List[float]] = defaultdict(list)
        self._counters: Dict[str, float] = defaultdict(float)

        # Start time for uptime
        self._start_time = time.time()

    def record_metric(
        self,
        name: str,
        value: float,
        tags: Optional[Dict[str, str]] = None,
        unit: Optional[str] = None
    ):
        """
        Record a metric value.

        Args:
            name: Metric name
            value: Metric value
            tags: Optional tags for categorization
            unit: Optional unit of measurement
        """
        if not self.config.enabled:
            return

        metric = Metric(
            name=name,
            value=value,
            timestamp=datetime.now(),
            tags=tags or {},
            unit=unit
        )

        self._metrics[name].append(metric)

    def increment_counter(
        self,
        name: str,
        delta: float = 1.0,
        tags: Optional[Dict[str, str]] = None
    ):
        """
        Increment a counter metric.

        Args:
            name: Counter name
            delta: Amount to increment (default: 1.0)
            tags: Optional tags for categorization
        """
        if not self.config.enabled:
            return

        self._counters[name] += delta

        # Also record as a metric
        self.record_metric(name, self._counters[name], tags=tags)

    def record_timing(
        self,
        name: str,
        duration_seconds: float,
        tags: Optional[Dict[str, str]] = None
    ):
        """
        Record a timing measurement.

        Args:
            name: Timing name
            duration_seconds: Duration in seconds
            tags: Optional tags for categorization
        """
        if not self.config.enabled:
            return

        self._timings[name].append(duration_seconds)
        self.record_metric(name, duration_seconds, tags=tags, unit="seconds")

    def get_metric(self, name: str) -> List[Metric]:
        """
        Get all values for a metric.

        Args:
            name: Metric name

        Returns:
            List of metric values
        """
        return self._metrics.get(name, [])

    def get_summary(self, name: str) -> Optional[MetricSummary]:
        """
        Get summary statistics for a metric.

        Args:
            name: Metric name

        Returns:
            MetricSummary or None if metric doesn't exist
        """
        metrics = self._metrics.get(name, [])

        if not metrics:
            return None

        values = [m.value for m in metrics]

        return MetricSummary(
            name=name,
            count=len(values),
            min=min(values),
            max=max(values),
            avg=sum(values) / len(values),
            sum=sum(values),
            unit=metrics[0].unit
        )

    def get_all_summaries(self) -> Dict[str, MetricSummary]:
        """
        Get summaries for all metrics.

        Returns:
            Dictionary of metric summaries
        """
        summaries = {}

        for name in self._metrics:
            summary = self.get_summary(name)
            if summary:
                summaries[name] = summary

        return summaries

    def get_counter(self, name: str) -> float:
        """
        Get current counter value.

        Args:
            name: Counter name

        Returns:
            Current counter value
        """
        return self._counters.get(name, 0.0)

    def get_all_counters(self) -> Dict[str, float]:
        """
        Get all counter values.

        Returns:
            Dictionary of counter values
        """
        return dict(self._counters)

    def get_timing_stats(self, name: str) -> Optional[Dict[str, float]]:
        """
        Get timing statistics for a named operation.

        Args:
            name: Timing name

        Returns:
            Dictionary with timing statistics
        """
        timings = self._timings.get(name, [])

        if not timings:
            return None

        return {
            "name": name,
            "count": len(timings),
            "total": sum(timings),
            "avg": sum(timings) / len(timings),
            "min": min(timings),
            "max": max(timings),
        }

    def get_all_timing_stats(self) -> Dict[str, Dict[str, float]]:
        """
        Get timing statistics for all operations.

        Returns:
            Dictionary of timing statistics
        """
        return {
            name: self.get_timing_stats(name)
            for name in self._timings
            if self.get_timing_stats(name) is not None
        }

    @contextmanager
    def timer(self, name: str, tags: Optional[Dict[str, str]] = None):
        """
        Context manager for timing operations.

        Args:
            name: Operation name
            tags: Optional tags for categorization

        Example:
            ```python
            with collector.timer("data_generation"):
                generate_data()
            ```
        """
        start_time = time.time()

        try:
            yield

        finally:
            duration = time.time() - start_time
            self.record_timing(name, duration, tags=tags)

    def clear_metric(self, name: str):
        """
        Clear all values for a metric.

        Args:
            name: Metric name
        """
        if name in self._metrics:
            del self._metrics[name]
        if name in self._timings:
            del self._timings[name]
        if name in self._counters:
            del self._counters[name]

    def clear_all_metrics(self):
        """Clear all metrics."""
        self._metrics.clear()
        self._timings.clear()
        self._counters.clear()

    def get_uptime_seconds(self) -> float:
        """
        Get collector uptime in seconds.

        Returns:
            Uptime in seconds
        """
        return time.time() - self._start_time

    def get_metrics_by_tag(self, tag_key: str, tag_value: str) -> List[Metric]:
        """
        Get metrics filtered by tag.

        Args:
            tag_key: Tag key
            tag_value: Tag value

        Returns:
            List of matching metrics
        """
        matching = []

        for metric_list in self._metrics.values():
            for metric in metric_list:
                if metric.tags.get(tag_key) == tag_value:
                    matching.append(metric)

        return matching

    def export_metrics(self) -> Dict[str, Any]:
        """
        Export all metrics as a dictionary.

        Returns:
            Dictionary with all metrics
        """
        return {
            "summaries": {
                name: {
                    "count": s.count,
                    "min": s.min,
                    "max": s.max,
                    "avg": s.avg,
                    "sum": s.sum,
                    "unit": s.unit,
                }
                for name, s in self.get_all_summaries().items()
            },
            "counters": self.get_all_counters(),
            "timings": self.get_all_timing_stats(),
            "uptime_seconds": self.get_uptime_seconds(),
            "exported_at": datetime.now().isoformat(),
        }

    def save_metrics(self, path: Optional[str] = None):
        """
        Save metrics to file.

        Args:
            path: Path to save metrics (uses config default if None)
        """
        if path is None:
            path = self.config.storage_path

        # Ensure directory exists
        Path(path).parent.mkdir(parents=True, exist_ok=True)

        # Export and save
        data = self.export_metrics()

        with open(path, "w") as f:
            json.dump(data, f, indent=2, default=str)


class PerformanceMetrics:
    """
    Performance-specific metrics collector.

    Tracks:
    - Request latency
    - Throughput
    - Resource usage
    """

    def __init__(self, collector: MetricsCollector):
        """
        Initialize performance metrics.

        Args:
            collector: Base metrics collector
        """
        self.collector = collector

    def record_request_latency(self, duration_seconds: float, request_type: str):
        """Record request latency."""
        self.collector.record_timing(
            "request_latency",
            duration_seconds,
            tags={"request_type": request_type}
        )

    def record_request_completion(self, success: bool, request_type: str):
        """Record request completion."""
        self.collector.increment_counter(
            "requests_total",
            tags={
                "request_type": request_type,
                "status": "success" if success else "failure"
            }
        )

    def get_throughput(self) -> Dict[str, float]:
        """Calculate throughput metrics."""
        uptime = self.collector.get_uptime_seconds()
        total_requests = self.collector.get_counter("requests_total")

        return {
            "requests_per_second": total_requests / uptime if uptime > 0 else 0,
            "total_requests": total_requests,
            "uptime_seconds": uptime,
        }

    def get_latency_stats(self) -> Dict[str, Any]:
        """Get latency statistics."""
        return self.collector.get_timing_stats("request_latency") or {}


class QualityMetrics:
    """
    Quality-specific metrics collector.

    Tracks:
    - Validation scores
    - Similarity scores
    - Privacy scores
    """

    def __init__(self, collector: MetricsCollector):
        """
        Initialize quality metrics.

        Args:
            collector: Base metrics collector
        """
        self.collector = collector

    def record_validation_score(
        self,
        score: float,
        validation_type: str,
        passed: bool
    ):
        """Record validation score."""
        self.collector.record_metric(
            "validation_score",
            score,
            tags={"type": validation_type},
            unit="score"
        )

        self.collector.increment_counter(
            "validations_total",
            tags={
                "type": validation_type,
                "result": "passed" if passed else "failed"
            }
        )

    def record_similarity_score(self, score: float, metric_name: str):
        """Record similarity score."""
        self.collector.record_metric(
            "similarity_score",
            score,
            tags={"metric": metric_name},
            unit="score"
        )

    def record_privacy_score(self, score: float):
        """Record privacy score."""
        self.collector.record_metric(
            "privacy_score",
            score,
            unit="score"
        )

    def get_quality_summary(self) -> Dict[str, Any]:
        """Get quality metrics summary."""
        validation_summary = self.collector.get_summary("validation_score")
        similarity_summary = self.collector.get_summary("similarity_score")
        privacy_summary = self.collector.get_summary("privacy_score")

        return {
            "validation": {
                "avg_score": validation_summary.avg if validation_summary else 0,
                "total_validations": self.collector.get_counter("validations_total"),
            },
            "similarity": {
                "avg_score": similarity_summary.avg if similarity_summary else 0,
            },
            "privacy": {
                "avg_score": privacy_summary.avg if privacy_summary else 0,
            },
        }


class ResourceMetrics:
    """
    Resource-specific metrics collector.

    Tracks:
    - Memory usage
    - CPU usage
    - Disk usage
    """

    def __init__(self, collector: MetricsCollector):
        """
        Initialize resource metrics.

        Args:
            collector: Base metrics collector
        """
        self.collector = collector
        self.process = psutil.Process()

    def collect_current(self):
        """Collect current resource usage."""
        # Memory
        memory_info = self.process.memory_info()
        memory_mb = memory_info.rss / (1024 * 1024)

        self.collector.record_metric(
            "memory_usage_mb",
            memory_mb,
            unit="MB"
        )

        # CPU
        cpu_percent = self.process.cpu_percent()

        self.collector.record_metric(
            "cpu_usage_percent",
            cpu_percent,
            unit="percent"
        )

        # Disk
        disk = psutil.disk_usage(".")
        disk_free_gb = disk.free / (1024 * 1024 * 1024)

        self.collector.record_metric(
            "disk_free_gb",
            disk_free_gb,
            unit="GB"
        )

    def get_resource_summary(self) -> Dict[str, Any]:
        """Get resource metrics summary."""
        memory_summary = self.collector.get_summary("memory_usage_mb")
        cpu_summary = self.collector.get_summary("cpu_usage_percent")
        disk_summary = self.collector.get_summary("disk_free_gb")

        return {
            "memory": {
                "current_mb": memory_summary.avg if memory_summary else 0,
                "max_mb": memory_summary.max if memory_summary else 0,
            },
            "cpu": {
                "current_percent": cpu_summary.avg if cpu_summary else 0,
                "max_percent": cpu_summary.max if cpu_summary else 0,
            },
            "disk": {
                "free_gb": disk_summary.avg if disk_summary else 0,
            },
        }


# Global collector instance
_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """Get global metrics collector instance."""
    global _collector
    if _collector is None:
        _collector = MetricsCollector()
    return _collector


def record_metric(name: str, value: float, **kwargs):
    """Convenience function to record a metric."""
    get_metrics_collector().record_metric(name, value, **kwargs)


def increment_counter(name: str, delta: float = 1.0, **kwargs):
    """Convenience function to increment a counter."""
    get_metrics_collector().increment_counter(name, delta, **kwargs)


def get_summary(name: str) -> Optional[MetricSummary]:
    """Convenience function to get metric summary."""
    return get_metrics_collector().get_summary(name)


def get_all_summaries() -> Dict[str, MetricSummary]:
    """Convenience function to get all summaries."""
    return get_metrics_collector().get_all_summaries()


def export_metrics() -> Dict[str, Any]:
    """Convenience function to export all metrics."""
    return get_metrics_collector().export_metrics()


def save_metrics(path: Optional[str] = None):
    """Convenience function to save metrics to file."""
    get_metrics_collector().save_metrics(path)


def clear_all_metrics():
    """Convenience function to clear all metrics."""
    get_metrics_collector().clear_all_metrics()


# Context manager for contextlib
from contextlib import contextmanager


@contextmanager
def track_metric(name: str, tags: Optional[Dict[str, str]] = None):
    """
    Context manager for tracking metrics.

    Args:
        name: Metric name
        tags: Optional tags

    Example:
        ```python
        with track_metric("operation"):
            do_operation()
        ```
    """
    collector = get_metrics_collector()
    with collector.timer(name, tags=tags):
        yield
