"""
Parameter Optimizer - Learn and optimize parameters.

Implements:
- Sample size optimization
- Distribution choice optimization
- Validation threshold optimization
- Quality target optimization
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import statistics

from synth.agent.models.core import Context, StrategyType


@dataclass
class ParameterSuggestion:
    """Suggested parameter values."""
    parameter_name: str
    suggested_value: Any
    confidence: float
    reasoning: str
    expected_improvement: str


@dataclass
class OptimizationResult:
    """Result of parameter optimization."""
    optimized_parameters: Dict[str, Any]
    suggestions: List[ParameterSuggestion]
    confidence: float
    estimated_improvement: float


class ParameterOptimizer:
    """
    Optimize parameters based on context and past experience.

    Learns optimal parameter values from historical outcomes
    and suggests improvements.
    """

    def __init__(self):
        """Initialize parameter optimizer."""
        # Learned optimal values from past executions
        self._optimal_values: Dict[str, List[float]] = {}

        # Performance tracking
        self._parameter_performance: Dict[str, List[Dict[str, Any]]] = {}

    def optimize_sample_size(
        self,
        context: Context,
    ) -> ParameterSuggestion:
        """
        Optimize sample size for data generation.

        Args:
            context: Current execution context

        Returns:
            ParameterSuggestion with optimal sample size
        """
        # Get baseline from request
        requested_count = context.request.entities.get("count", 100)

        # Factor 1: Available memory
        available_memory_mb = context.environment.available_memory_mb
        memory_based_count = self._estimate_max_count_from_memory(available_memory_mb)

        # Factor 2: Past performance
        memory_key = self._get_context_key(context)
        optimal_counts = self._optimal_values.get(f"count_{memory_key}", [])

        if optimal_counts:
            # Use median of successful past counts
            past_optimal = statistics.median(optimal_counts)
        else:
            past_optimal = None

        # Factor 3: Data quality requirements
        min_count_for_quality = 100  # Minimum for statistical significance

        # Determine optimal count
        suggestions = [
            ("requested", requested_count),
            ("memory_limited", memory_based_count),
            ("past_optimal", past_optimal) if past_optimal else None,
            ("quality_minimum", min_count_for_quality),
        ]

        # Filter None values
        suggestions = [(k, v) for k, v in suggestions if v is not None]

        # Choose the most conservative count
        optimal_count = min(v for _, v in suggestions)

        # Calculate confidence
        if past_optimal and abs(optimal_count - past_optimal) / past_optimal < 0.1:
            confidence = 0.9
        elif optimal_count == requested_count:
            confidence = 0.7
        else:
            confidence = 0.6

        reasoning_parts = []
        if optimal_count < requested_count:
            reasoning_parts.append(f"Reduced from {requested_count} due to memory constraints")
        if optimal_count == past_optimal:
            reasoning_parts.append(f"Based on {len(optimal_counts)} past successful runs")

        return ParameterSuggestion(
            parameter_name="count",
            suggested_value=optimal_count,
            confidence=confidence,
            reasoning="; ".join(reasoning_parts) if reasoning_parts else "Standard optimization",
            expected_improvement="Better resource utilization",
        )

    def optimize_distribution(
        self,
        context: Context,
    ) -> ParameterSuggestion:
        """
        Optimize distribution choice for generation.

        Args:
            context: Current execution context

        Returns:
            ParameterSuggestion with distribution choice
        """
        # For now, return a basic suggestion
        # In a full implementation, this would analyze data characteristics

        data = context.working_variables.get("data")

        if data is not None:
            # Check if data has specific patterns
            # For now, simple heuristic
            return ParameterSuggestion(
                parameter_name="distribution",
                suggested_value="statistical",
                confidence=0.7,
                reasoning="Based on data characteristics",
                expected_improvement="Better pattern matching",
            )
        else:
            return ParameterSuggestion(
                parameter_name="distribution",
                suggested_value="uniform",
                confidence=0.5,
                reasoning="No data to analyze, using default",
                expected_improvement="Default distribution",
            )

    def optimize_thresholds(
        self,
        context: Context,
    ) -> List[ParameterSuggestion]:
        """
        Optimize validation thresholds.

        Args:
            context: Current execution context

        Returns:
            List of ParameterSuggestions for thresholds
        """
        suggestions = []

        # Sample size threshold
        count = context.request.entities.get("count", 0)
        if count > 1000:
            suggestions.append(ParameterSuggestion(
                parameter_name="validation_sample_size",
                suggested_value=min(1000, count),
                confidence=0.8,
                reasoning=f"Large dataset ({count}), sampling for validation",
                expected_improvement="Faster validation with good coverage",
            ))

        # Quality threshold
        suggestions.append(ParameterSuggestion(
            parameter_name="min_quality_score",
            suggested_value=0.85,
            confidence=0.7,
            reasoning="Balanced quality requirement",
            expected_improvement="Good balance between strictness and flexibility",
        ))

        return suggestions

    def optimize_all_parameters(
        self,
        context: Context,
    ) -> OptimizationResult:
        """
        Optimize all parameters for the current context.

        Args:
            context: Current execution context

        Returns:
            OptimizationResult with all suggestions
        """
        suggestions = []
        optimized = {}

        # Optimize sample size
        count_suggestion = self.optimize_sample_size(context)
        suggestions.append(count_suggestion)
        optimized["count"] = count_suggestion.suggested_value

        # Optimize distribution
        dist_suggestion = self.optimize_distribution(context)
        suggestions.append(dist_suggestion)
        optimized["distribution"] = dist_suggestion.suggested_value

        # Optimize thresholds
        threshold_suggestions = self.optimize_thresholds(context)
        suggestions.extend(threshold_suggestions)
        for suggestion in threshold_suggestions:
            optimized[suggestion.parameter_name] = suggestion.suggested_value

        # Calculate overall confidence
        avg_confidence = sum(s.confidence for s in suggestions) / len(suggestions)

        # Estimate improvement
        improvement = 0.1  # 10% improvement baseline
        if avg_confidence > 0.8:
            improvement = 0.2  # 20% improvement
        elif avg_confidence > 0.6:
            improvement = 0.15  # 15% improvement

        return OptimizationResult(
            optimized_parameters=optimized,
            suggestions=suggestions,
            confidence=avg_confidence,
            estimated_improvement=improvement,
        )

    def record_outcome(
        self,
        context: Context,
        parameters: Dict[str, Any],
        success: bool,
        metrics: Dict[str, float],
    ):
        """
        Record outcome for learning.

        Args:
            context: Execution context
            parameters: Parameters used
            success: Whether execution succeeded
            metrics: Performance metrics
        """
        # Only learn from successful outcomes
        if not success:
            return

        # Record sample size performance
        if "count" in parameters:
            context_key = self._get_context_key(context)
            key = f"count_{context_key}"

            if key not in self._optimal_values:
                self._optimal_values[key] = []

            # Store count weighted by quality
            quality = metrics.get("quality", 0.8)
            count = parameters["count"]

            # Record multiple times based on quality (better quality = more records)
            records = int(quality * 3) + 1
            for _ in range(records):
                self._optimal_values[key].append(count)

        # Record general parameter performance
        for param_name, param_value in parameters.items():
            if param_name not in self._parameter_performance:
                self._parameter_performance[param_name] = []

            self._parameter_performance[param_name].append({
                "value": param_value,
                "success": success,
                "quality": metrics.get("quality", 0.8),
                "duration": metrics.get("duration", 0),
                "context": context.to_dict(),
            })

    def _get_context_key(self, context: Context) -> str:
        """Get a key representing the context type."""
        # Create a simplified context key
        request_type = context.request.request_type.value
        has_data = "data" in context.working_variables

        return f"{request_type}_withData_{has_data}"

    def _estimate_max_count_from_memory(
        self,
        available_memory_mb: float,
    ) -> int:
        """
        Estimate maximum record count based on available memory.

        Args:
            available_memory_mb: Available memory in MB

        Returns:
            Estimated safe count
        """
        # Rough estimate: 1 record = 1KB memory
        # Use 50% of available memory for safety
        safe_memory_mb = available_memory_mb * 0.5
        estimated_count = int(safe_memory_mb * 1024)  # Convert MB to KB

        # Cap at reasonable values
        return min(max(estimated_count, 100), 1000000)

    def get_parameter_stats(
        self,
        parameter_name: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Get statistics for a parameter.

        Args:
            parameter_name: Name of parameter

        Returns:
            Statistics dictionary or None
        """
        if parameter_name not in self._parameter_performance:
            return None

        records = self._parameter_performance[parameter_name]

        if not records:
            return None

        # Calculate statistics
        success_records = [r for r in records if r["success"]]

        if not success_records:
            return {
                "parameter": parameter_name,
                "total_uses": len(records),
                "success_rate": 0.0,
            }

        values = [r["value"] for r in success_records]

        # Try to calculate numeric stats
        try:
            numeric_values = [float(v) for v in values if isinstance(v, (int, float))]
            if numeric_values:
                return {
                    "parameter": parameter_name,
                    "total_uses": len(records),
                    "success_rate": len(success_records) / len(records),
                    "avg_value": statistics.mean(numeric_values),
                    "min_value": min(numeric_values),
                    "max_value": max(numeric_values),
                    "std_value": statistics.stdev(numeric_values) if len(numeric_values) > 1 else 0,
                }
        except (TypeError, ValueError):
            pass

        return {
            "parameter": parameter_name,
            "total_uses": len(records),
            "success_rate": len(success_records) / len(records),
            "common_values": values[:5],  # First 5 values
        }

    def suggest_improvements(
        self,
        current_parameters: Dict[str, Any],
        context: Context,
    ) -> List[ParameterSuggestion]:
        """
        Suggest parameter improvements based on learning.

        Args:
            current_parameters: Current parameter values
            context: Execution context

        Returns:
            List of improvement suggestions
        """
        suggestions = []

        # Check each parameter
        for param_name, param_value in current_parameters.items():
            stats = self.get_parameter_stats(param_name)

            if stats and stats.get("success_rate", 0) < 0.7:
                # Low success rate, suggest change
                if "avg_value" in stats:
                    suggestions.append(ParameterSuggestion(
                        parameter_name=param_name,
                        suggested_value=stats["avg_value"],
                        confidence=0.7,
                        reasoning=f"Current success rate {stats['success_rate']:.1%}, historical average performs better",
                        expected_improvement=f"Improved success rate to ~{stats.get('success_rate', 0.7)*100:.0f}%",
                    ))

        return suggestions
