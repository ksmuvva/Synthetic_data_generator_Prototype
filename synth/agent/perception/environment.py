"""
Environment Awareness - Monitor system and data environment.

Implements:
- Resource monitoring
- Data environment monitoring
- Environment context building
"""

import psutil
import os
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from synth.agent.models.core import (
    EnvironmentContext,
)


@dataclass
class ResourceStatus:
    """System resource status."""
    memory_used_mb: float
    memory_available_mb: float
    memory_percent: float
    cpu_percent: float
    disk_used_gb: float
    disk_available_gb: float
    disk_percent: float
    status: str  # "ok", "warning", "critical"


class ResourceMonitor:
    """Monitor system resources."""

    def __init__(self):
        """Initialize resource monitor."""
        # Thresholds
        self.memory_warning_threshold = 80  # percent
        self.memory_critical_threshold = 90  # percent
        self.cpu_warning_threshold = 85  # percent
        self.disk_warning_threshold = 85  # percent

    def get_memory_usage(self) -> Dict[str, float]:
        """Get current memory usage."""
        mem = psutil.virtual_memory()
        return {
            "total_mb": mem.total / 1024 / 1024,
            "available_mb": mem.available / 1024 / 1024,
            "used_mb": mem.used / 1024 / 1024,
            "percent": mem.percent,
        }

    def get_cpu_usage(self) -> float:
        """Get current CPU usage percent."""
        return psutil.cpu_percent(interval=0.1)

    def get_disk_usage(self, path: str = ".") -> Dict[str, float]:
        """Get disk usage for path."""
        # Default values in case all attempts fail
        default_usage = {
            "total_gb": 500.0,
            "used_gb": 250.0,
            "free_gb": 250.0,
            "percent": 50.0,
        }

        try:
            # Try current directory first with normalized path
            norm_path = os.path.normpath(os.path.abspath(path))
            disk = psutil.disk_usage(norm_path)
            return {
                "total_gb": disk.total / (1024**3),
                "used_gb": disk.used / (1024**3),
                "free_gb": disk.free / (1024**3),
                "percent": disk.percent,
            }
        except Exception:
            try:
                # Try root of current drive
                if os.name == 'nt':  # Windows
                    drive = os.path.splitdrive(os.path.abspath(path))[0]  # e.g., 'C:'
                    if drive:
                        disk = psutil.disk_usage(drive)
                    else:
                        return default_usage
                else:
                    disk = psutil.disk_usage('/')
                return {
                    "total_gb": disk.total / (1024**3),
                    "used_gb": disk.used / (1024**3),
                    "free_gb": disk.free / (1024**3),
                    "percent": disk.percent,
                }
            except Exception:
                # Return defaults if all attempts fail
                return default_usage

    def check_thresholds(self) -> ResourceStatus:
        """Check resource thresholds and return status."""
        mem = self.get_memory_usage()
        cpu = self.get_cpu_usage()
        disk = self.get_disk_usage()

        # Determine overall status
        status = "ok"
        if (mem["percent"] >= self.memory_critical_threshold or
            cpu >= self.cpu_warning_threshold or
            disk["percent"] >= self.disk_warning_threshold):
            status = "critical"
        elif (mem["percent"] >= self.memory_warning_threshold or
              disk["percent"] >= self.disk_warning_threshold):
            status = "warning"

        return ResourceStatus(
            memory_used_mb=mem["used_mb"],
            memory_available_mb=mem["available_mb"],
            memory_percent=mem["percent"],
            cpu_percent=cpu,
            disk_used_gb=disk["used_gb"],
            disk_available_gb=disk["free_gb"],
            disk_percent=disk["percent"],
            status=status,
        )


class DataEnvironmentMonitor:
    """Monitor data environment."""

    def __init__(self):
        """Initialize data environment monitor."""
        pass

    def scan_data_sources(self, path: str = ".") -> List[Dict[str, Any]]:
        """Scan for available data sources."""
        sources = []

        # Look for CSV files
        try:
            import glob
            csv_files = glob.glob(os.path.join(path, "**/*.csv"), recursive=True)
            for csv_file in csv_files[:10]:  # Limit to 10
                sources.append({
                    "type": "csv",
                    "path": csv_file,
                    "size_mb": os.path.getsize(csv_file) / 1024 / 1024,
                })
        except:
            pass

        return sources

    def analyze_schema(self, data) -> Dict[str, Any]:
        """Analyze data schema."""
        try:
            import pandas as pd

            if not isinstance(data, pd.DataFrame):
                return {"error": "Not a DataFrame"}

            return {
                "rows": len(data),
                "columns": len(data.columns),
                "column_types": {col: str(dtype) for col, dtype in data.dtypes.items()},
                "memory_mb": data.memory_usage(deep=True).sum() / 1024 / 1024,
            }
        except Exception as e:
            return {"error": str(e)}

    def check_permissions(self, path: str) -> Dict[str, bool]:
        """Check file permissions."""
        return {
            "readable": os.access(path, os.R_OK),
            "writable": os.access(path, os.W_OK),
            "executable": os.access(path, os.X_OK),
        }

    def estimate_quality(self, data) -> Dict[str, Any]:
        """Estimate data quality."""
        try:
            import pandas as pd

            if not isinstance(data, pd.DataFrame):
                return {"error": "Not a DataFrame"}

            # Calculate quality metrics
            total_cells = len(data) * len(data.columns)
            missing_cells = data.isnull().sum().sum()

            return {
                "completeness": 1.0 - (missing_cells / total_cells) if total_cells > 0 else 1.0,
                "missing_values": int(missing_cells),
                "duplicate_rows": int(data.duplicated().sum()),
                "total_rows": len(data),
            }
        except Exception as e:
            return {"error": str(e)}


class EnvironmentContextBuilder:
    """Build environment context."""

    def __init__(self):
        """Initialize environment context builder."""
        self.resource_monitor = ResourceMonitor()
        self.data_monitor = DataEnvironmentMonitor()

    def build_context(self) -> EnvironmentContext:
        """Build complete environment context."""
        resources = self.resource_monitor.check_thresholds()

        return EnvironmentContext(
            available_memory_mb=resources.memory_available_mb,
            available_cpu_percent=100 - resources.cpu_percent,
            available_disk_gb=resources.disk_available_gb,
            active_sessions=1,  # Simplified
        )

    def detect_changes(self, previous: EnvironmentContext) -> List[str]:
        """Detect changes in environment."""
        changes = []
        current = self.build_context()

        # Check memory change
        mem_diff = current.available_memory_mb - previous.available_memory_mb
        if abs(mem_diff) > 500:  # More than 500MB difference
            changes.append(f"Memory changed by {mem_diff:.0f}MB")

        # Check CPU change
        cpu_diff = current.available_cpu_percent - previous.available_cpu_percent
        if abs(cpu_diff) > 20:  # More than 20% difference
            changes.append(f"Available CPU changed by {cpu_diff:.0f}%")

        # Check disk change
        disk_diff = current.available_disk_gb - previous.available_disk_gb
        if abs(disk_diff) > 5:  # More than 5GB difference
            changes.append(f"Disk space changed by {disk_diff:.1f}GB")

        return changes

    def get_full_status(self) -> Dict[str, Any]:
        """Get full environment status."""
        resources = self.resource_monitor.check_thresholds()
        data_sources = self.data_monitor.scan_data_sources()

        return {
            "resources": {
                "memory": {
                    "used_mb": resources.memory_used_mb,
                    "available_mb": resources.memory_available_mb,
                    "percent": resources.memory_percent,
                },
                "cpu": {
                    "available_percent": 100 - resources.cpu_percent,
                    "percent": resources.cpu_percent,
                },
                "disk": {
                    "used_gb": resources.disk_used_gb,
                    "available_gb": resources.disk_available_gb,
                    "percent": resources.disk_percent,
                },
            },
            "status": resources.status,
            "data_sources": data_sources,
        }
