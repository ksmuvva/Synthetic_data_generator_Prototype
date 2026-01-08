"""
Enhanced Proactive Behavior Engine.

Detects opportunities and provides intelligent suggestions for:
- Data quality improvements
- Workflow optimizations
- Pattern discoveries
- Resource efficiencies
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

from synth.agent.models.core import Context, RequestType, Suggestion


class OpportunityType(str, Enum):
    """Types of opportunities the agent can detect."""
    QUALITY_IMPROVEMENT = "quality_improvement"
    PERFORMANCE_OPTIMIZATION = "performance_optimization"
    PATTERN_DISCOVERY = "pattern_discovery"
    RESOURCE_EFFICIENCY = "resource_efficiency"
    WORKFLOW_AUTOMATION = "workflow_automation"
    VALIDATION_ENHANCEMENT = "validation_enhancement"


@dataclass
class Opportunity:
    """An detected opportunity for improvement."""
    opportunity_type: OpportunityType
    title: str
    description: str
    impact: str  # "high", "medium", "low"
    effort: str  # "high", "medium", "low"
    rationale: str
    suggested_actions: List[str]
    expected_benefit: str
    confidence: float


class EnhancedProactiveEngine:
    """
    Enhanced proactive behavior engine with opportunity detection.

    Goes beyond basic suggestions to actively detect opportunities
    for improvement and optimization.
    """

    def __init__(self, enable_opportunity_detection: bool = True):
        """
        Initialize proactive engine.

        Args:
            enable_opportunity_detection: Enable advanced opportunity detection
        """
        self.enable_opportunity_detection = enable_opportunity_detection

    def detect_opportunities(
        self,
        context: Context,
        execution_result: Optional[Dict[str, Any]] = None,
    ) -> List[Opportunity]:
        """
        Detect opportunities for improvement.

        Args:
            context: Current execution context
            execution_result: Optional execution results

        Returns:
            List of detected opportunities
        """
        opportunities = []

        if not self.enable_opportunity_detection:
            return opportunities

        # Analyze context for opportunities
        opportunities.extend(self._detect_quality_opportunities(context))
        opportunities.extend(self._detect_performance_opportunities(context))
        opportunities.extend(self._detect_pattern_opportunities(context))
        opportunities.extend(self._detect_resource_opportunities(context))

        # Sort by impact and confidence
        opportunities.sort(key=lambda o: (self._impact_score(o.impact), o.confidence), reverse=True)

        return opportunities

    def _detect_quality_opportunities(self, context: Context) -> List[Opportunity]:
        """Detect data quality improvement opportunities."""
        opportunities = []

        request = context.request
        entities = request.entities

        # Check for validation opportunities
        if request.request_type == RequestType.DATA_GENERATION:
            count = entities.get("count", 0)

            if count > 1000:
                opportunities.append(Opportunity(
                    opportunity_type=OpportunityType.QUALITY_IMPROVEMENT,
                    title="Add Statistical Validation",
                    description=f"Generating {count} records - consider adding statistical validation to ensure quality.",
                    impact="high",
                    effort="low",
                    rationale="Large datasets benefit from statistical quality checks",
                    suggested_actions=[
                        "Enable distribution validation against reference data",
                        "Add correlation checks for related fields",
                        "Validate privacy/anonymization quality"
                    ],
                    expected_benefit="Higher confidence in synthetic data quality",
                    confidence=0.85
                ))

        # Check for constraints opportunities
        if not entities.get("constraints"):
            opportunities.append(Opportunity(
                opportunity_type=OpportunityType.QUALITY_IMPROVEMENT,
                title="Add Business Constraints",
                description="No business constraints specified - adding constraints can improve realism.",
                impact="medium",
                effort="medium",
                rationale="Business rules and constraints make synthetic data more realistic",
                suggested_actions=[
                    "Define value ranges (e.g., age >= 18)",
                    "Add correlation constraints between related fields",
                    "Specify categorical distributions"
                ],
                expected_benefit="More realistic and usable synthetic data",
                confidence=0.75
            ))

        return opportunities

    def _detect_performance_opportunities(self, context: Context) -> List[Opportunity]:
        """Detect performance optimization opportunities."""
        opportunities = []

        request = context.request
        entities = request.entities
        env = context.environment

        # Check for batch size optimization
        count = entities.get("count", 0)
        if count > 10000:
            opportunities.append(Opportunity(
                opportunity_type=OpportunityType.PERFORMANCE_OPTIMIZATION,
                title="Enable Parallel Processing",
                description=f"Large dataset ({count} records) - parallel processing can significantly speed up generation.",
                impact="high",
                effort="low",
                rationale=f"{count} records will take time to generate sequentially",
                suggested_actions=[
                    "Enable multi-threaded generation",
                    "Use chunked processing for memory efficiency",
                    "Consider streaming output for large datasets"
                ],
                expected_benefit="2-5x faster generation for large datasets",
                confidence=0.9
            ))

        # Check memory constraints
        if env and env.available_memory_mb < 2000:
            if count > 5000:
                opportunities.append(Opportunity(
                    opportunity_type=OpportunityType.RESOURCE_EFFICIENCY,
                    title="Memory-Constrained Generation",
                    description=f"Low memory ({env.available_memory_mb:.0f}MB) with {count} records - use chunked generation.",
                    impact="high",
                    effort="low",
                    rationale="Generating large datasets in low memory can cause failures",
                    suggested_actions=[
                        "Reduce batch size to 100-500 records",
                        "Enable streaming output to file",
                        "Process in multiple smaller chunks"
                    ],
                    expected_benefit="Avoid out-of-memory errors",
                    confidence=0.95
                ))

        return opportunities

    def _detect_pattern_opportunities(self, context: Context) -> List[Opportunity]:
        """Detect pattern discovery opportunities."""
        opportunities = []

        request = context.request
        entities = request.entities

        # Check for learning opportunities
        if "source_file" in entities or "reference_data" in entities:
            opportunities.append(Opportunity(
                opportunity_type=OpportunityType.PATTERN_DISCOVERY,
                title="Learn Patterns from Reference Data",
                description="Reference data available - learning patterns improves quality.",
                impact="high",
                effort="medium",
                rationale="Patterns learned from real data produce more realistic synthetic data",
                suggested_actions=[
                    "Analyze statistical distributions",
                    "Learn correlation patterns",
                    "Discover categorical value frequencies"
                ],
                expected_benefit="More accurate synthetic data matching real-world patterns",
                confidence=0.85
            ))

        # Check for multi-table opportunities
        entity_type = entities.get("entity_type", "")
        if entity_type in ["transaction", "order", "sales"]:
            opportunities.append(Opportunity(
                opportunity_type=OpportunityType.PATTERN_DISCOVERY,
                title="Add Related Entities",
                description=f"{entity_type.capitalize()} data typically has related entities - consider multi-table generation.",
                impact="medium",
                effort="high",
                rationale=f"Realistic {entity_type} data includes relationships to customers, products, etc.",
                suggested_actions=[
                    "Generate customer entities",
                    "Generate product/entities catalog",
                    "Add foreign key relationships"
                ],
                expected_benefit="More complete and realistic test dataset",
                confidence=0.7
            ))

        return opportunities

    def _detect_resource_opportunities(self, context: Context) -> List[Opportunity]:
        """Detect resource efficiency opportunities."""
        opportunities = []

        # Check for export format optimization
        entities = context.request.entities
        output_format = entities.get("format", "csv")

        if output_format == "csv":
            count = entities.get("count", 0)
            if count > 100000:
                opportunities.append(Opportunity(
                    opportunity_type=OpportunityType.RESOURCE_EFFICIENCY,
                    title="Use Parquet for Large Datasets",
                    description=f"{count} records as CSV - Parquet format is more efficient.",
                    impact="medium",
                    effort="low",
                    rationale="Parquet provides better compression and faster I/O for large datasets",
                    suggested_actions=[
                        "Export to Parquet format",
                        "Enable compression (snappy or gzip)",
                        "Consider partitioning for very large datasets"
                    ],
                    expected_benefit="3-5x smaller files, faster read/write",
                    confidence=0.8
                ))

        return opportunities

    def _impact_score(self, impact: str) -> int:
        """Convert impact string to numeric score."""
        scores = {"high": 3, "medium": 2, "low": 1}
        return scores.get(impact, 0)

    def opportunities_to_suggestions(
        self,
        opportunities: List[Opportunity],
    ) -> List[Suggestion]:
        """
        Convert opportunities to suggestions.

        Args:
            opportunities: List of detected opportunities

        Returns:
            List of suggestions compatible with Response format
        """
        suggestions = []

        for opp in opportunities[:5]:  # Top 5 opportunities
            suggestion = Suggestion(
                suggestion_type="improvement",  # Use string instead of enum
                title=opp.title,
                description=opp.description,
                impact=opp.impact,
                actions=opp.suggested_actions,
                rationale=opp.rationale,
                benefit=opp.expected_benefit,  # Use 'benefit' instead of 'expected_benefit'
            )

            suggestions.append(suggestion)

        return suggestions


# Backward compatibility alias
ProactiveEngine = EnhancedProactiveEngine
