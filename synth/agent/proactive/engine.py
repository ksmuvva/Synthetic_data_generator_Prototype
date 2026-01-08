"""
Proactive Engine - Unified proactive behavior.

Implements:
- Improvement suggestions
- Issue warnings
- Opportunity detection
"""

from typing import Dict, Any, List
from dataclasses import dataclass

from synth.agent.models.core import (
    Context,
    Suggestion,
    Warning,
    ErrorSeverity,
)


class ProactiveEngine:
    """
    Unified proactive behavior.

    Generates:
    1. Improvement suggestions
    2. Issue warnings
    3. Opportunity detection
    """

    def __init__(self):
        """Initialize proactive engine."""
        pass

    def generate_suggestions(
        self,
        context: Context,
        result: Dict[str, Any],
    ) -> List[Suggestion]:
        """
        Generate proactive suggestions.

        Args:
            context: Current execution context
            result: Result of current operation

        Returns:
            List of Suggestion objects
        """
        suggestions = []

        # Suggest validation after data generation
        if context.request.request_type.value == "data_generation":
            suggestions.append(Suggestion(
                suggestion_type="validation",
                title="Validate Generated Data",
                description="Would you like me to validate the quality of the generated data?",
                benefit="Ensures data quality meets requirements",
                effort="Low",
                priority=1,
            ))

            # Suggest export
            suggestions.append(Suggestion(
                suggestion_type="export",
                title="Export Data",
                description="Would you like me to export this data to a file?",
                benefit="Save results for later use",
                effort="Low",
                priority=2,
            ))

            # Suggest analysis if data is large
            count = context.request.entities.get("count", 0)
            if count > 1000:
                suggestions.append(Suggestion(
                    suggestion_type="analysis",
                    title="Analyze Patterns",
                    description="Would you like me to analyze the patterns in this data?",
                    benefit="Discover insights and correlations",
                    effort="Medium",
                    priority=3,
                ))

        # Suggest generation after analysis
        elif context.request.request_type.value == "data_analysis":
            suggestions.append(Suggestion(
                suggestion_type="generation",
                title="Generate More Data",
                description="Would you like me to generate more data based on these patterns?",
                benefit="Expand your dataset with similar quality",
                effort="Medium",
                priority=1,
            ))

        return suggestions

    def generate_warnings(
        self,
        context: Context,
        plan: Any,
    ) -> List[Warning]:
        """
        Generate proactive warnings.

        Args:
            context: Current execution context
            plan: Execution plan

        Returns:
            List of Warning objects
        """
        warnings = []

        # Warn about large data generation
        if context.request.request_type.value == "data_generation":
            count = context.request.entities.get("count", 0)
            if count > 10000:
                warnings.append(Warning(
                    warning_type="resource",
                    message=f"Generating {count} records may require significant memory and time",
                    severity=ErrorSeverity.MEDIUM,
                    mitigation="Consider generating in smaller batches",
                ))

            # Warn about memory constraints
            if context.environment.available_memory_mb < 1000:
                warnings.append(Warning(
                    warning_type="resource",
                    message=f"Low memory available ({context.environment.available_memory_mb:.0f}MB)",
                    severity=ErrorSeverity.HIGH,
                    mitigation="Reduce data size or free up memory",
                ))

        # Warn about validation without original data
        if context.request.request_type.value == "data_validation":
            if "original" not in context.request.entities:
                warnings.append(Warning(
                    warning_type="validation",
                    message="No original data provided for comparison",
                    severity=ErrorSeverity.MEDIUM,
                    mitigation="Provide original data for meaningful validation",
                ))

        return warnings

    def detect_opportunities(
        self,
        context: Context,
        result: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Detect optimization opportunities.

        Args:
            context: Current execution context
            result: Result of current operation

        Returns:
            List of opportunity dicts
        """
        opportunities = []

        # Detect large dataset opportunity
        data = context.working_variables.get("data")
        if data is not None:
            try:
                data_size = len(data)
                if data_size > 5000:
                    opportunities.append({
                        "type": "optimization",
                        "description": "Consider using sampling for faster analysis",
                        "benefit": "Reduce processing time significantly",
                        "effort": "Low",
                    })
            except:
                pass

        # Detect multi-format export opportunity
        if context.request.request_type.value == "data_generation":
            opportunities.append({
                "type": "export",
                "description": "Export in multiple formats (CSV, JSON, Parquet)",
                "benefit": "Maximum compatibility and performance",
                "effort": "Low",
            })

        return opportunities
