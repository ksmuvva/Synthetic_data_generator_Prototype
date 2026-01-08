"""
Enhanced Proactive Agent - Intelligent unsolicited suggestions.

Implements autonomous proactive behavior with:
- Pattern-based opportunity detection
- Semantic similarity analysis
- Multi-factor suggestion scoring
- Context-aware recommendations
- Learning from user behavior
"""

from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import asyncio
from collections import defaultdict

from synth.agent.models.core import (
    Context,
    Suggestion,
    RequestType,
)


class SuggestionUrgency(str, Enum):
    """Urgency levels for suggestions."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFORMATIONAL = "informational"


class SuggestionCategory(str, Enum):
    """Categories of proactive suggestions."""
    OPTIMIZATION = "optimization"
    AUTOMATION = "automation"
    QUALITY = "quality"
    WARNING = "warning"
    LEARNING = "learning"
    WORKFLOW = "workflow"
    RESOURCE = "resource"
    DISCOVERY = "discovery"


@dataclass
class ProactiveSuggestion:
    """An enhanced proactive suggestion."""
    suggestion_id: str
    category: SuggestionCategory
    urgency: SuggestionUrgency
    title: str
    description: str
    rationale: str
    suggested_actions: List[str]
    expected_benefit: str
    confidence: float
    effort_required: str  # "low", "medium", "high"
    dependencies: List[str] = field(default_factory=list)
    context_snapshot: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    auto_action: Optional[Callable] = None

    def to_suggestion(self) -> Suggestion:
        """Convert to base Suggestion type."""
        return Suggestion(
            suggestion_id=self.suggestion_id,
            suggestion_type=self.category.value,
            title=self.title,
            description=self.description,
            benefit=self.expected_benefit,
            effort=self.effort_required,
            priority=int(self.urgency.value == "critical") * 10 + int(self.confidence * 5),
            timestamp=self.created_at,
        )


@dataclass
class BehaviorPattern:
    """A learned behavior pattern."""
    pattern_id: str
    pattern_type: str  # "sequential", "repetitive", "conditional"
    description: str
    frequency: int
    last_seen: datetime
    confidence: float
    context_requirements: Dict[str, Any]
    suggested_automation: Optional[Dict[str, Any]] = None


class SmartProactiveAgent:
    """
    Enhanced proactive agent with intelligent suggestion generation.

    Analyzes user behavior, context patterns, and system state to
    generate relevant unsolicited suggestions.
    """

    def __init__(
        self,
        suggestion_queue_size: int = 50,
        pattern_learning_enabled: bool = True,
        min_confidence_threshold: float = 0.5,
    ):
        """
        Initialize smart proactive agent.

        Args:
            suggestion_queue_size: Max suggestions to queue
            pattern_learning_enabled: Enable pattern learning
            min_confidence_threshold: Minimum confidence for suggestions
        """
        self.suggestion_queue_size = suggestion_queue_size
        self.pattern_learning_enabled = pattern_learning_enabled
        self.min_confidence = min_confidence_threshold

        # Suggestion management
        self._suggestions: List[ProactiveSuggestion] = []
        self._dismissed_suggestions: Dict[str, str] = {}  # suggestion_id -> reason

        # Pattern learning
        self._behavior_patterns: Dict[str, BehaviorPattern] = {}
        self._action_history: List[Dict[str, Any]] = []
        self._context_transitions: List[Dict[str, Any]] = []

        # Monitoring state
        self._monitoring_active = False
        self._last_analysis_time: Optional[datetime] = None

    async def analyze_and_suggest(
        self,
        context: Context,
        force_analysis: bool = False,
    ) -> List[ProactiveSuggestion]:
        """
        Analyze context and generate proactive suggestions.

        Args:
            context: Current context
            force_analysis: Force analysis even if recently analyzed

        Returns:
            List of new suggestions
        """
        # Check if analysis is needed
        if not force_analysis and self._last_analysis_time:
            time_since_last = datetime.now() - self._last_analysis_time
            if time_since_last < timedelta(minutes=5):
                return []

        # Update behavior tracking
        if self.pattern_learning_enabled:
            self._track_behavior(context)

        # Generate suggestions from multiple analyzers
        new_suggestions = []

        # Quality and optimization suggestions
        new_suggestions.extend(await self._analyze_quality_opportunities(context))

        # Automation opportunities
        new_suggestions.extend(await self._analyze_automation_opportunities(context))

        # Resource optimization
        new_suggestions.extend(await self._analyze_resource_optimization(context))

        # Pattern-based suggestions
        if self.pattern_learning_enabled:
            new_suggestions.extend(await self._analyze_pattern_opportunities(context))

        # Discovery and learning
        new_suggestions.extend(await self._analyze_discovery_opportunities(context))

        # Workflow improvements
        new_suggestions.extend(await self._analyze_workflow_improvements(context))

        # Filter by confidence and deduplicate
        filtered = self._filter_and_deduplicate(new_suggestions)

        # Add to queue
        for suggestion in filtered:
            self._add_suggestion(suggestion)

        self._last_analysis_time = datetime.now()

        return filtered

    async def _analyze_quality_opportunities(
        self,
        context: Context,
    ) -> List[ProactiveSuggestion]:
        """Analyze quality improvement opportunities."""
        suggestions = []

        request_type = context.request.request_type
        entities = context.request.entities

        # Large dataset without validation
        if request_type == RequestType.DATA_GENERATION:
            count = entities.get("count", 0)
            has_validation = entities.get("validation", False)

            if count > 1000 and not has_validation:
                suggestions.append(ProactiveSuggestion(
                    suggestion_id=f"quality_validation_{int(datetime.now().timestamp())}",
                    category=SuggestionCategory.QUALITY,
                    urgency=SuggestionUrgency.MEDIUM,
                    title="Add Data Validation",
                    description=f"You're generating {count} records. Adding validation ensures quality.",
                    rationale="Large datasets benefit from statistical validation",
                    suggested_actions=[
                        "Enable distribution validation",
                        "Add correlation checks",
                        "Validate privacy/anonymization quality"
                    ],
                    expected_benefit="Higher confidence in synthetic data quality",
                    confidence=0.85,
                    effort_required="low",
                    context_snapshot={"count": count, "request_type": request_type.value},
                ))

        # Missing constraints
        if not entities.get("constraints"):
            suggestions.append(ProactiveSuggestion(
                suggestion_id=f"quality_constraints_{int(datetime.now().timestamp())}",
                category=SuggestionCategory.QUALITY,
                urgency=SuggestionUrgency.LOW,
                title="Add Business Constraints",
                description="Adding business constraints can improve realism.",
                rationale="Business rules make synthetic data more realistic",
                suggested_actions=[
                    "Define value ranges (e.g., age >= 18)",
                    "Add correlation constraints",
                    "Specify categorical distributions"
                ],
                expected_benefit="More realistic and usable synthetic data",
                confidence=0.75,
                effort_required="medium",
                context_snapshot={"entity_type": entities.get("entity_type")},
            ))

        return suggestions

    async def _analyze_automation_opportunities(
        self,
        context: Context,
    ) -> List[ProactiveSuggestion]:
        """Analyze automation opportunities."""
        suggestions = []

        # Check for repetitive patterns
        history = context.conversation_history
        if len(history) >= 3:
            # Count request types
            request_counts = defaultdict(int)
            for turn in history[-10:]:
                request = turn.get("user_message", "").lower()
                if "generate" in request:
                    request_counts["generate"] += 1
                if "validate" in request:
                    request_counts["validate"] += 1
                if "export" in request:
                    request_counts["export"] += 1

            # Suggest automation for repetitive tasks
            for task, count in request_counts.items():
                if count >= 3:
                    suggestions.append(ProactiveSuggestion(
                        suggestion_id=f"automation_{task}_{int(datetime.now().timestamp())}",
                        category=SuggestionCategory.AUTOMATION,
                        urgency=SuggestionUrgency.MEDIUM,
                        title=f"Automate {task.capitalize()} Workflow",
                        description=f"You've performed '{task}' {count} times recently.",
                        rationale=f"Repetitive {task} operations can be automated",
                        suggested_actions=[
                            f"Create {task} workflow template",
                            "Set up automatic execution",
                            "Configure default parameters"
                        ],
                        expected_benefit=f"Save time on repetitive {task} tasks",
                        confidence=min(0.5 + count * 0.1, 0.95),
                        effort_required="low",
                        context_snapshot={"task": task, "frequency": count},
                    ))

        return suggestions

    async def _analyze_resource_optimization(
        self,
        context: Context,
    ) -> List[ProactiveSuggestion]:
        """Analyze resource optimization opportunities."""
        suggestions = []

        env = context.environment
        entities = context.request.entities

        # Memory optimization
        if env and env.available_memory_mb < 2000:
            count = entities.get("count", 0)
            if count > 5000:
                suggestions.append(ProactiveSuggestion(
                    suggestion_id=f"resource_memory_{int(datetime.now().timestamp())}",
                    category=SuggestionCategory.RESOURCE,
                    urgency=SuggestionUrgency.HIGH,
                    title="Use Memory-Constrained Generation",
                    description=f"Low memory ({env.available_memory_mb:.0f}MB) with {count} records.",
                    rationale="Large datasets in low memory can cause failures",
                    suggested_actions=[
                        "Reduce batch size to 100-500 records",
                        "Enable streaming output",
                        "Process in smaller chunks"
                    ],
                    expected_benefit="Avoid out-of-memory errors",
                    confidence=0.95,
                    effort_required="low",
                    context_snapshot={
                        "available_memory_mb": env.available_memory_mb,
                        "count": count
                    },
                ))

        # Parallel processing for large datasets
        count = entities.get("count", 0)
        if count > 10000:
            suggestions.append(ProactiveSuggestion(
                suggestion_id=f"resource_parallel_{int(datetime.now().timestamp())}",
                category=SuggestionCategory.OPTIMIZATION,
                urgency=SuggestionUrgency.MEDIUM,
                title="Enable Parallel Processing",
                description=f"Large dataset ({count} records) - parallel processing can speed up generation.",
                rationale=f"{count} records will take time to generate sequentially",
                suggested_actions=[
                    "Enable multi-threaded generation",
                    "Use chunked processing",
                    "Consider streaming output"
                ],
                expected_benefit="2-5x faster generation",
                confidence=0.9,
                effort_required="low",
                context_snapshot={"count": count},
            ))

        # Format optimization
        output_format = entities.get("format", "csv")
        if output_format == "csv" and count > 100000:
            suggestions.append(ProactiveSuggestion(
                suggestion_id=f"resource_format_{int(datetime.now().timestamp())}",
                category=SuggestionCategory.OPTIMIZATION,
                urgency=SuggestionUrgency.LOW,
                title="Use Parquet for Large Datasets",
                description=f"{count} records as CSV - Parquet format is more efficient.",
                rationale="Parquet provides better compression and faster I/O",
                suggested_actions=[
                    "Export to Parquet format",
                    "Enable compression (snappy or gzip)",
                    "Consider partitioning"
                ],
                expected_benefit="3-5x smaller files, faster read/write",
                confidence=0.8,
                effort_required="low",
                context_snapshot={"count": count, "format": output_format},
            ))

        return suggestions

    async def _analyze_pattern_opportunities(
        self,
        context: Context,
    ) -> List[ProactiveSuggestion]:
        """Analyze patterns for proactive suggestions."""
        suggestions = []

        # Check for sequential patterns (generate -> validate -> export)
        history = context.conversation_history
        if len(history) >= 2:
            recent_requests = [turn.get("user_message", "").lower() for turn in history[-3:]]

            has_generate = any("generate" in r for r in recent_requests)
            has_validate = any("validate" in r for r in recent_requests)
            has_export = any("export" in r for r in recent_requests)

            if has_generate and has_validate and not has_export:
                suggestions.append(ProactiveSuggestion(
                    suggestion_id=f"pattern_workflow_{int(datetime.now().timestamp())}",
                    category=SuggestionCategory.WORKFLOW,
                    urgency=SuggestionUrgency.LOW,
                    title="Complete Your Workflow",
                    description="I notice you generate and validate data. Want to export it?",
                    rationale="Common pattern: generate → validate → export",
                    suggested_actions=[
                        "Export to CSV format",
                        "Export to Parquet format",
                        "Create custom export workflow"
                    ],
                    expected_benefit="Complete data pipeline workflow",
                    confidence=0.7,
                    effort_required="low",
                    context_snapshot={"pattern": "generate_validate"},
                ))

        return suggestions

    async def _analyze_discovery_opportunities(
        self,
        context: Context,
    ) -> List[ProactiveSuggestion]:
        """Analyze discovery and learning opportunities."""
        suggestions = []

        entities = context.request.entities
        entity_type = entities.get("entity_type", "")

        # Suggest related entities
        if entity_type == "customer":
            suggestions.append(ProactiveSuggestion(
                suggestion_id=f"discovery_related_{int(datetime.now().timestamp())}",
                category=SuggestionCategory.DISCOVERY,
                urgency=SuggestionUrgency.INFORMATIONAL,
                title="Explore Related Entities",
                description=f"{entity_type.capitalize()} data typically has related entities.",
                rationale=f"Realistic {entity_type} data includes relationships",
                suggested_actions=[
                    "Generate transaction data",
                    "Add product catalog",
                    "Create order entities"
                ],
                expected_benefit="More complete and realistic test dataset",
                confidence=0.65,
                effort_required="high",
                context_snapshot={"entity_type": entity_type},
            ))

        # Suggest advanced features
        if not entities.get("source_file") and not entities.get("reference_data"):
            suggestions.append(ProactiveSuggestion(
                suggestion_id=f"discovery_learning_{int(datetime.now().timestamp())}",
                category=SuggestionCategory.LEARNING,
                urgency=SuggestionUrgency.INFORMATIONAL,
                title="Learn from Reference Data",
                description="Using reference data can improve synthetic data quality.",
                rationale="Patterns learned from real data produce more realistic results",
                suggested_actions=[
                    "Provide sample data file",
                    "Enable pattern learning",
                    "Match statistical distributions"
                ],
                expected_benefit="More accurate synthetic data matching real patterns",
                confidence=0.7,
                effort_required="medium",
                context_snapshot={"has_reference": False},
            ))

        return suggestions

    async def _analyze_workflow_improvements(
        self,
        context: Context,
    ) -> List[ProactiveSuggestion]:
        """Analyze workflow improvement opportunities."""
        suggestions = []

        # Check for multi-objective opportunity
        request_type = context.request.request_type
        if request_type == RequestType.DATA_GENERATION:
            # Look for sequential requests in history
            history = context.conversation_history
            if len(history) >= 2:
                recent = history[-2:]
                operations = []
                for turn in recent:
                    msg = turn.get("user_message", "").lower()
                    if "generate" in msg:
                        operations.append("generate")
                    if "validate" in msg:
                        operations.append("validate")
                    if "export" in msg:
                        operations.append("export")

                if len(set(operations)) >= 2:
                    suggestions.append(ProactiveSuggestion(
                        suggestion_id=f"workflow_multi_{int(datetime.now().timestamp())}",
                        category=SuggestionCategory.WORKFLOW,
                        urgency=SuggestionUrgency.MEDIUM,
                        title="Use Multi-Objective Workflow",
                        description=f"I see you're doing {', '.join(operations)}. Try combining them!",
                        rationale="Multi-objective workflows are more efficient",
                        suggested_actions=[
                            "Combine operations in single request",
                            "Define workflow with multiple steps",
                            "Use batch processing"
                        ],
                        expected_benefit="Faster processing, better integration",
                        confidence=0.75,
                        effort_required="low",
                        context_snapshot={"operations": operations},
                    ))

        return suggestions

    def _filter_and_deduplicate(
        self,
        suggestions: List[ProactiveSuggestion],
    ) -> List[ProactiveSuggestion]:
        """Filter suggestions by confidence and remove duplicates."""
        # Filter by confidence
        filtered = [s for s in suggestions if s.confidence >= self.min_confidence]

        # Deduplicate by category and title similarity
        seen = set()
        deduplicated = []

        for suggestion in filtered:
            key = (suggestion.category, suggestion.title.lower())
            if key not in seen:
                seen.add(key)
                deduplicated.append(suggestion)

        return deduplicated

    def _add_suggestion(self, suggestion: ProactiveSuggestion):
        """Add suggestion to queue."""
        self._suggestions.append(suggestion)

        # Maintain queue size
        if len(self._suggestions) > self.suggestion_queue_size:
            # Remove oldest low-urgency suggestions
            self._suggestions = [
                s for s in self._suggestions
                if s.urgency != SuggestionUrgency.LOW or
                   len(self._suggestions) <= self.suggestion_queue_size
            ]

        # Sort by urgency and confidence
        self._suggestions.sort(
            key=lambda s: (
                -self._urgency_score(s.urgency),
                -s.confidence
            )
        )

    def _urgency_score(self, urgency: SuggestionUrgency) -> int:
        """Convert urgency to numeric score."""
        scores = {
            SuggestionUrgency.CRITICAL: 5,
            SuggestionUrgency.HIGH: 4,
            SuggestionUrgency.MEDIUM: 3,
            SuggestionUrgency.LOW: 2,
            SuggestionUrgency.INFORMATIONAL: 1,
        }
        return scores.get(urgency, 0)

    def get_suggestions(
        self,
        limit: int = 5,
        min_urgency: Optional[SuggestionUrgency] = None,
    ) -> List[ProactiveSuggestion]:
        """
        Get top proactive suggestions.

        Args:
            limit: Max suggestions to return
            min_urgency: Minimum urgency level

        Returns:
            List of suggestions
        """
        suggestions = self._suggestions

        # Filter by urgency
        if min_urgency:
            min_score = self._urgency_score(min_urgency)
            suggestions = [
                s for s in suggestions
                if self._urgency_score(s.urgency) >= min_score
            ]

        return suggestions[:limit]

    def dismiss_suggestion(
        self,
        suggestion_id: str,
        reason: str = "user_dismissed",
    ):
        """
        Dismiss a suggestion.

        Args:
            suggestion_id: ID of suggestion to dismiss
            reason: Reason for dismissal
        """
        # Remove from active suggestions
        self._suggestions = [s for s in self._suggestions if s.suggestion_id != suggestion_id]

        # Record dismissal
        self._dismissed_suggestions[suggestion_id] = reason

    def clear_suggestions(self):
        """Clear all suggestions."""
        self._suggestions.clear()

    def get_suggestion_stats(self) -> Dict[str, Any]:
        """Get suggestion statistics."""
        by_category = defaultdict(int)
        by_urgency = defaultdict(int)

        for suggestion in self._suggestions:
            by_category[suggestion.category.value] += 1
            by_urgency[suggestion.urgency.value] += 1

        return {
            "total_suggestions": len(self._suggestions),
            "dismissed_count": len(self._dismissed_suggestions),
            "by_category": dict(by_category),
            "by_urgency": dict(by_urgency),
            "last_analysis": self._last_analysis_time.isoformat() if self._last_analysis_time else None,
        }

    def _track_behavior(self, context: Context):
        """Track user behavior for pattern learning."""
        # Record action
        self._action_history.append({
            "timestamp": datetime.now().isoformat(),
            "request_type": context.request.request_type.value,
            "intent": context.request.intent,
            "entities": context.request.entities,
        })

        # Keep history manageable
        if len(self._action_history) > 100:
            self._action_history = self._action_history[-100:]

        # Analyze for patterns
        self._detect_behavior_patterns()

    def _detect_behavior_patterns(self):
        """Detect behavior patterns from history."""
        if len(self._action_history) < 3:
            return

        # Count request types
        type_counts = defaultdict(int)
        for action in self._action_history[-20:]:
            type_counts[action["request_type"]] += 1

        # Detect repetitive patterns
        for req_type, count in type_counts.items():
            if count >= 3:
                pattern_id = f"repetitive_{req_type}"

                if pattern_id not in self._behavior_patterns:
                    self._behavior_patterns[pattern_id] = BehaviorPattern(
                        pattern_id=pattern_id,
                        pattern_type="repetitive",
                        description=f"Repeatedly performs {req_type}",
                        frequency=count,
                        last_seen=datetime.now(),
                        confidence=min(0.5 + count * 0.1, 0.9),
                        context_requirements={"request_type": req_type},
                        suggested_automation={
                            "type": "workflow_automation",
                            "operation": req_type,
                            "frequency": count,
                        },
                    )
                else:
                    # Update existing pattern
                    pattern = self._behavior_patterns[pattern_id]
                    pattern.frequency = count
                    pattern.last_seen = datetime.now()
                    pattern.confidence = min(0.5 + count * 0.1, 0.9)

    def get_learned_patterns(self) -> List[BehaviorPattern]:
        """Get learned behavior patterns."""
        patterns = list(self._behavior_patterns.values())

        # Sort by frequency and confidence
        patterns.sort(
            key=lambda p: (p.frequency, p.confidence),
            reverse=True
        )

        return patterns
