"""
Core data tools for the AI Agent.

Implements:
- DataGenerationTool
- DataValidationTool
- DataAnalysisTool
"""

import time
import pandas as pd
from typing import Dict, Any
import uuid

from synth.agent.tools.base import Tool, ToolParameter
from synth.agent.models.core import ToolResult
from synth.generation import StatisticalSampler
from synth.patterns import UnivariateAnalyzer
from synth.patterns.schema import SchemaInferrer
from synth.patterns.storage import create_pattern_from_analysis


class DataGenerationTool(Tool):
    """Generate synthetic data from patterns."""

    def __init__(self):
        super().__init__()
        self._name = "DataGenerationTool"
        self._description = "Generate synthetic data from learned patterns"
        self._parameters = {
            "data": ToolParameter(
                name="data",
                type="DataFrame",
                description="Input data to learn from",
                required=True,
            ),
            "count": ToolParameter(
                name="count",
                type="int",
                description="Number of records to generate",
                required=True,
            ),
            "strategy": ToolParameter(
                name="strategy",
                type="str",
                description="Generation strategy",
                required=False,
                default="statistical",
                enum=["statistical", "constrained", "copula"],
            ),
        }
        self._timeout = 600  # 10 minutes for data generation

    def validate_parameters(self, **kwargs) -> bool:
        """Validate parameters."""
        if "data" not in kwargs:
            return False
        if "count" not in kwargs:
            return False
        if not isinstance(kwargs["count"], int) or kwargs["count"] <= 0:
            return False
        if "strategy" in kwargs:
            if kwargs["strategy"] not in ["statistical", "constrained", "copula"]:
                return False
        # Check data is not None
        if kwargs["data"] is None:
            return False
        return True

    async def execute(self, **kwargs) -> ToolResult:
        """Execute data generation."""
        start_time = time.time()

        try:
            import numpy as np
            from synth.patterns.schema import SchemaInferrer

            data = kwargs["data"]
            count = kwargs["count"]
            strategy = kwargs.get("strategy", "statistical")

            # Learn patterns using schema inferrer
            schema_inferrer = SchemaInferrer()
            schema = schema_inferrer.infer(data)

            analyzer = UnivariateAnalyzer()

            # Analyze each field and collect patterns
            numeric_patterns = {}
            categorical_patterns = {}
            string_patterns = {}

            for field in schema.fields:
                series = data[field.name].dropna()
                if len(series) < 10:
                    continue

                if field.type.value in ("integer", "float"):
                    pattern = analyzer.analyze_numeric(series, field.name)
                    numeric_patterns[field.name] = pattern
                elif field.type.value == "string":
                    pattern = analyzer.analyze_string(series, field.name)
                    string_patterns[field.name] = pattern
                elif field.type.value == "boolean":
                    # Convert boolean to numeric for analysis
                    pattern = analyzer.analyze_numeric(series.astype(int), field.name)
                    numeric_patterns[field.name] = pattern

            # Create Pattern object using the storage utility
            pattern_id = f"pattern_{uuid.uuid4().hex[:8]}"
            pattern = create_pattern_from_analysis(
                pattern_id=pattern_id,
                schema=schema,
                numeric_patterns=numeric_patterns,
                categorical_patterns=categorical_patterns,
                string_patterns=string_patterns,
                source_files=["tool_input"],
            )

            # Generate data
            sampler = StatisticalSampler()
            synthetic = sampler.generate(pattern, count)

            # Check if generation succeeded
            if synthetic is None:
                raise ValueError("Data generation failed - no patterns or generation error")

            execution_time = time.time() - start_time

            return ToolResult(
                tool_name=self.name,
                success=True,
                data=synthetic,
                execution_time_seconds=execution_time,
                metadata={
                    "strategy": strategy,
                    "rows_generated": len(synthetic) if synthetic is not None else 0,
                    "columns": len(synthetic.columns) if synthetic is not None else 0,
                }
            )
        except Exception as e:
            return ToolResult(
                tool_name=self.name,
                success=False,
                error=str(e),
                execution_time_seconds=time.time() - start_time
            )

    def get_capabilities(self) -> list[str]:
        """Get tool capabilities."""
        return [
            "data_generation",
            "statistical_generation",
            "pattern_learning",
            "synthetic_data",
        ]

    def estimate_cost(self, **kwargs) -> Dict[str, float]:
        """Estimate execution cost."""
        count = kwargs.get("count", 100)
        return {
            "time_seconds": count * 0.01,  # 10ms per record
            "memory_mb": count * 0.5,  # 0.5MB per record
            "cpu_percent": 50.0,
        }


class DataValidationTool(Tool):
    """Validate synthetic data quality."""

    def __init__(self):
        super().__init__()
        self._name = "DataValidationTool"
        self._description = "Validate synthetic data quality against original"
        self._parameters = {
            "original": ToolParameter(
                name="original",
                type="DataFrame",
                description="Original data",
                required=True,
            ),
            "synthetic": ToolParameter(
                name="synthetic",
                type="DataFrame",
                description="Synthetic data",
                required=True,
            ),
        }
        self._timeout = 300

    def validate_parameters(self, **kwargs) -> bool:
        """Validate parameters."""
        if "original" not in kwargs:
            return False
        if "synthetic" not in kwargs:
            return False
        if kwargs["original"] is None:
            return False
        if kwargs["synthetic"] is None:
            return False
        return True

    async def execute(self, **kwargs) -> ToolResult:
        """Execute validation."""
        start_time = time.time()

        try:
            original = kwargs["original"]
            synthetic = kwargs["synthetic"]

            # Calculate basic statistics
            results = {
                "rows": {
                    "original": len(original),
                    "synthetic": len(synthetic),
                },
                "columns": {
                    "original": len(original.columns),
                    "synthetic": len(synthetic.columns),
                },
                "columns_match": set(original.columns) == set(synthetic.columns),
                "statistical_similarity": {},
            }

            # Compare distributions for numeric columns
            numeric_cols = original.select_dtypes(include=["number"]).columns
            for col in numeric_cols:
                if col in synthetic.columns:
                    orig_mean = original[col].mean()
                    synth_mean = synthetic[col].mean()
                    diff_pct = abs(orig_mean - synth_mean) / orig_mean * 100 if orig_mean != 0 else 0

                    results["statistical_similarity"][col] = {
                        "original_mean": float(orig_mean),
                        "synthetic_mean": float(synth_mean),
                        "difference_percent": float(diff_pct),
                    }

            execution_time = time.time() - start_time

            return ToolResult(
                tool_name=self.name,
                success=True,
                data=results,
                execution_time_seconds=execution_time,
                metadata={
                    "validation_checks": len(results),
                    "columns_checked": len(numeric_cols),
                }
            )
        except Exception as e:
            return ToolResult(
                tool_name=self.name,
                success=False,
                error=str(e),
                execution_time_seconds=time.time() - start_time
            )

    def get_capabilities(self) -> list[str]:
        """Get tool capabilities."""
        return [
            "data_validation",
            "quality_check",
            "statistical_validation",
        ]


class DataAnalysisTool(Tool):
    """Analyze data patterns and statistics."""

    def __init__(self):
        super().__init__()
        self._name = "DataAnalysisTool"
        self._description = "Analyze data patterns and statistics"
        self._parameters = {
            "data": ToolParameter(
                name="data",
                type="DataFrame",
                description="Data to analyze",
                required=True,
            ),
        }
        self._timeout = 300

    def validate_parameters(self, **kwargs) -> bool:
        """Validate parameters."""
        if "data" not in kwargs:
            return False
        if kwargs["data"] is None:
            return False
        return True

    async def execute(self, **kwargs) -> ToolResult:
        """Execute analysis."""
        start_time = time.time()

        try:
            import numpy as np
            from synth.patterns.schema import SchemaInferrer

            data = kwargs["data"]

            # Calculate statistics
            stats = {
                "rows": len(data),
                "columns": len(data.columns),
                "numeric_columns": int(data.select_dtypes(include=[np.number]).shape[1]),
                "categorical_columns": int(data.select_dtypes(include=["object"]).shape[1]),
                "missing_values": data.isnull().sum().to_dict(),
                "memory_usage_mb": float(data.memory_usage(deep=True).sum() / 1024 / 1024),
                "column_types": {col: str(dtype) for col, dtype in data.dtypes.items()},
            }

            # Analyze patterns
            schema_inferrer = SchemaInferrer()
            schema = schema_inferrer.infer(data)

            analyzer = UnivariateAnalyzer()
            patterns = []

            for field in schema.fields:
                series = data[field.name].dropna()
                if len(series) < 10:
                    continue

                if field.type.value in ("integer", "float"):
                    pattern = analyzer.analyze_numeric(series, field.name)
                    patterns.append(pattern)
                elif field.type.value == "string":
                    pattern = analyzer.analyze_string(series, field.name)
                    patterns.append(pattern)

            execution_time = time.time() - start_time

            return ToolResult(
                tool_name=self.name,
                success=True,
                data={
                    "statistics": stats,
                    "patterns_count": len(patterns),
                    "patterns": patterns,
                },
                execution_time_seconds=execution_time
            )
        except Exception as e:
            return ToolResult(
                tool_name=self.name,
                success=False,
                error=str(e),
                execution_time_seconds=time.time() - start_time
            )

    def get_capabilities(self) -> list[str]:
        """Get tool capabilities."""
        return [
            "data_analysis",
            "pattern_detection",
            "statistical_analysis",
        ]


class DataExportTool(Tool):
    """Export data to various formats."""

    def __init__(self):
        super().__init__()
        self._name = "DataExportTool"
        self._description = "Export data to various formats (CSV, JSON, Parquet)"
        self._parameters = {
            "data": ToolParameter(
                name="data",
                type="DataFrame",
                description="Data to export",
                required=True,
            ),
            "format": ToolParameter(
                name="format",
                type="str",
                description="Output format",
                required=False,
                default="csv",
                enum=["csv", "json", "parquet"],
            ),
            "path": ToolParameter(
                name="path",
                type="str",
                description="Output file path",
                required=True,
            ),
        }
        self._timeout = 300

    def validate_parameters(self, **kwargs) -> bool:
        """Validate parameters."""
        if "data" not in kwargs:
            return False
        if "path" not in kwargs:
            return False
        if kwargs["data"] is None:
            return False
        if "format" in kwargs:
            if kwargs["format"] not in ["csv", "json", "parquet"]:
                return False
        return True

    async def execute(self, **kwargs) -> ToolResult:
        """Execute export."""
        start_time = time.time()

        try:
            data = kwargs["data"]
            format_type = kwargs.get("format", "csv")
            path = kwargs["path"]

            if format_type == "csv":
                data.to_csv(path, index=False)
            elif format_type == "json":
                data.to_json(path, orient="records")
            elif format_type == "parquet":
                data.to_parquet(path, index=False)

            execution_time = time.time() - start_time

            return ToolResult(
                tool_name=self.name,
                success=True,
                data={"path": path, "rows": len(data)},
                execution_time_seconds=execution_time,
                metadata={"format": format_type}
            )
        except Exception as e:
            return ToolResult(
                tool_name=self.name,
                success=False,
                error=str(e),
                execution_time_seconds=time.time() - start_time
            )

    def get_capabilities(self) -> list[str]:
        """Get tool capabilities."""
        return [
            "data_export",
            "csv_export",
            "json_export",
            "parquet_export",
        ]
