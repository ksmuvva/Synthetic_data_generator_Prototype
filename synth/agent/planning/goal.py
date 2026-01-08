"""
Goal Decomposition - Break complex goals into sub-goals.

Implements:
- Goal complexity analysis
- Sub-goal identification
- Dependency establishment
- Effort estimation
"""

from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, field
from enum import Enum

from synth.agent.models.core import (
    Context,
    Goal,
    SubGoal,
    RequestType,
)


class GoalComplexity(str, Enum):
    """Goal complexity levels."""
    TRIVIAL = "trivial"
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    VERY_COMPLEX = "very_complex"


@dataclass
class ComplexityAssessment:
    """Assessment of goal complexity."""
    complexity: GoalComplexity
    score: float  # 0.0 to 1.0
    reasoning: str
    estimated_sub_goals: int
    estimated_depth: int
    confidence: float


class GoalDecomposer:
    """
    Decompose complex goals into manageable sub-goals.

    Analyzes goals and breaks them down into hierarchical sub-goals
    with explicit dependencies.
    """

    def __init__(self):
        """Initialize goal decomposer."""
        # Complexity thresholds
        self.simple_threshold = 0.3
        self.moderate_threshold = 0.5
        self.complex_threshold = 0.7
        self.very_complex_threshold = 0.85

    def analyze_goal_complexity(
        self,
        context: Context,
    ) -> ComplexityAssessment:
        """
        Analyze the complexity of a goal.

        Args:
            context: Current execution context

        Returns:
            ComplexityAssessment with detailed analysis
        """
        score = 0.0
        factors = []

        # Factor 1: Request type
        request_type = context.request.request_type
        if request_type == RequestType.MULTI_OBJECTIVE:
            score += 0.4
            factors.append("Multiple objectives")
        elif request_type in [RequestType.DATA_GENERATION, RequestType.DATA_ANALYSIS]:
            score += 0.2
            factors.append("Single objective")
        else:
            score += 0.1
            factors.append("Simple request")

        # Factor 2: Data size
        count = context.request.entities.get("count", 0)
        if count > 50000:
            score += 0.3
            factors.append(f"Large data size ({count})")
        elif count > 10000:
            score += 0.2
            factors.append(f"Medium data size ({count})")
        elif count > 1000:
            score += 0.1
            factors.append(f"Small data size ({count})")

        # Factor 3: Constraint complexity
        constraints = context.request.constraints
        if len(constraints) > 5:
            score += 0.2
            factors.append(f"Many constraints ({len(constraints)})")
        elif len(constraints) > 2:
            score += 0.1
            factors.append(f"Some constraints ({len(constraints)})")

        # Factor 4: Parameter complexity
        params = context.request.parameters
        if len(params) > 5:
            score += 0.15
            factors.append(f"Many parameters ({len(params)})")

        # Factor 5: Working variables (existing data)
        working_vars = context.working_variables
        if "data" in working_vars:
            score += 0.1
            factors.append("Working with existing data")

        # Normalize score to 0-1
        score = min(score, 1.0)

        # Determine complexity level
        if score < self.simple_threshold:
            complexity = GoalComplexity.TRIVIAL
            estimated_sub_goals = 1
            estimated_depth = 1
        elif score < self.moderate_threshold:
            complexity = GoalComplexity.SIMPLE
            estimated_sub_goals = 2
            estimated_depth = 1
        elif score < self.complex_threshold:
            complexity = GoalComplexity.MODERATE
            estimated_sub_goals = 3
            estimated_depth = 2
        elif score < self.very_complex_threshold:
            complexity = GoalComplexity.COMPLEX
            estimated_sub_goals = 5
            estimated_depth = 3
        else:
            complexity = GoalComplexity.VERY_COMPLEX
            estimated_sub_goals = 7
            estimated_depth = 4

        return ComplexityAssessment(
            complexity=complexity,
            score=score,
            reasoning=f"Complexity factors: {', '.join(factors)}",
            estimated_sub_goals=estimated_sub_goals,
            estimated_depth=estimated_depth,
            confidence=0.8,
        )

    def identify_sub_goals(
        self,
        context: Context,
        complexity_assessment: Optional[ComplexityAssessment] = None,
    ) -> List[SubGoal]:
        """
        Identify necessary sub-goals to achieve the main goal.

        Args:
            context: Current execution context
            complexity_assessment: Optional pre-computed assessment

        Returns:
            List of SubGoal objects in execution order
        """
        if complexity_assessment is None:
            complexity_assessment = self.analyze_goal_complexity(context)

        sub_goals = []
        request_type = context.request.request_type

        # Handle multi-objective requests
        if request_type == RequestType.MULTI_OBJECTIVE:
            detected_types = context.request.entities.get("detected_types", [])

            # Sub-goal 1: Data generation (if needed)
            if RequestType.DATA_GENERATION in detected_types:
                sub_goals.append(SubGoal(
                    sub_goal_id="sg_generate",
                    description="Generate synthetic data",
                    goal_type="data_generation",
                    dependencies=[],
                    estimated_effort=0.6,
                    status="pending",
                ))

            # Sub-goal 2: Data analysis (if needed)
            if RequestType.DATA_ANALYSIS in detected_types:
                deps = ["sg_generate"] if RequestType.DATA_GENERATION in detected_types else []
                sub_goals.append(SubGoal(
                    sub_goal_id="sg_analyze",
                    description="Analyze data patterns and statistics",
                    goal_type="data_analysis",
                    dependencies=deps,
                    estimated_effort=0.3,
                    status="pending",
                ))

            # Sub-goal 3: Data validation (if needed)
            if RequestType.DATA_VALIDATION in detected_types:
                deps = ["sg_generate"] if RequestType.DATA_GENERATION in detected_types else []
                sub_goals.append(SubGoal(
                    sub_goal_id="sg_validate",
                    description="Validate data quality and consistency",
                    goal_type="data_validation",
                    dependencies=deps,
                    estimated_effort=0.4,
                    status="pending",
                ))

            # Sub-goal 4: Data export (if needed)
            if RequestType.DATA_EXPORT in detected_types:
                deps = ["sg_generate"] if RequestType.DATA_GENERATION in detected_types else []
                sub_goals.append(SubGoal(
                    sub_goal_id="sg_export",
                    description="Export data to file",
                    goal_type="data_export",
                    dependencies=deps,
                    estimated_effort=0.2,
                    status="pending",
                ))

        # Handle single-objective requests
        elif request_type == RequestType.DATA_GENERATION:
            sub_goals.append(SubGoal(
                sub_goal_id="sg_generate",
                description="Generate synthetic data",
                goal_type="data_generation",
                dependencies=[],
                estimated_effort=0.6,
                status="pending",
            ))

            # Add validation as sub-goal if data is large
            count = context.request.entities.get("count", 0)
            if count > 1000:
                sub_goals.append(SubGoal(
                    sub_goal_id="sg_validate",
                    description="Validate generated data quality",
                    goal_type="data_validation",
                    dependencies=["sg_generate"],
                    estimated_effort=0.3,
                    status="pending",
                ))

            # Add export as sub-goal if path specified
            if "path" in context.request.entities:
                deps = ["sg_generate", "sg_validate"] if count > 1000 else ["sg_generate"]
                sub_goals.append(SubGoal(
                    sub_goal_id="sg_export",
                    description="Export data to file",
                    goal_type="data_export",
                    dependencies=deps,
                    estimated_effort=0.2,
                    status="pending",
                ))

        elif request_type == RequestType.DATA_ANALYSIS:
            sub_goals.append(SubGoal(
                sub_goal_id="sg_analyze",
                description="Analyze data patterns and statistics",
                goal_type="data_analysis",
                dependencies=[],
                estimated_effort=0.4,
                status="pending",
            ))

        elif request_type == RequestType.DATA_VALIDATION:
            sub_goals.append(SubGoal(
                sub_goal_id="sg_validate",
                description="Validate data quality and consistency",
                goal_type="data_validation",
                dependencies=[],
                estimated_effort=0.5,
                status="pending",
            ))

        elif request_type == RequestType.DATA_EXPORT:
            sub_goals.append(SubGoal(
                sub_goal_id="sg_export",
                description="Export data to file",
                goal_type="data_export",
                dependencies=[],
                estimated_effort=0.3,
                status="pending",
            ))

        return sub_goals

    def establish_dependencies(
        self,
        sub_goals: List[SubGoal],
        context: Context,
    ) -> List[SubGoal]:
        """
        Establish dependencies between sub-goals.

        Args:
            sub_goals: List of sub-goals
            context: Current execution context

        Returns:
            Sub-goals with updated dependencies
        """
        # Dependencies are already set in identify_sub_goals
        # This method can enhance them based on context

        request_type = context.request.request_type

        # For multi-objective, ensure export depends on all other steps
        if request_type == RequestType.MULTI_OBJECTIVE:
            export_goal = next((sg for sg in sub_goals if sg.goal_type == "data_export"), None)
            if export_goal and len(sub_goals) > 1:
                # Export depends on all non-export sub-goals
                export_goal.dependencies = [sg.sub_goal_id for sg in sub_goals if sg.sub_goal_id != export_goal.sub_goal_id]

        return sub_goals

    def estimate_effort(
        self,
        sub_goal: SubGoal,
        context: Context,
    ) -> Dict[str, Any]:
        """
        Estimate effort required for a sub-goal.

        Args:
            sub_goal: Sub-goal to estimate
            context: Current execution context

        Returns:
            Dictionary with effort estimates
        """
        # Base effort by goal type
        base_effort = {
            "data_generation": 0.6,
            "data_analysis": 0.3,
            "data_validation": 0.4,
            "data_export": 0.2,
        }.get(sub_goal.goal_type, 0.3)

        # Adjust for data size
        count = context.request.entities.get("count", 0)
        if count > 0:
            # Logarithmic scaling
            size_multiplier = 1.0 + (min(count, 100000) / 100000) * 0.5
            base_effort *= size_multiplier

        # Adjust for complexity
        num_constraints = len(context.request.constraints)
        if num_constraints > 0:
            base_effort *= (1.0 + num_constraints * 0.1)

        return {
            "effort_score": base_effort,
            "estimated_time_seconds": base_effort * 10,
            "resource_intensity": "high" if base_effort > 0.5 else "medium" if base_effort > 0.3 else "low",
            "confidence": 0.7,
        }

    def decompose_goal(
        self,
        context: Context,
    ) -> Dict[str, Any]:
        """
        Full goal decomposition pipeline.

        Args:
            context: Current execution context

        Returns:
            Dictionary with decomposition results
        """
        # Step 1: Analyze complexity
        complexity = self.analyze_goal_complexity(context)

        # Step 2: Identify sub-goals
        sub_goals = self.identify_sub_goals(context, complexity)

        # Step 3: Establish dependencies
        sub_goals = self.establish_dependencies(sub_goals, context)

        # Step 4: Estimate effort for each sub-goal
        efforts = {
            sg.sub_goal_id: self.estimate_effort(sg, context)
            for sg in sub_goals
        }

        # Calculate total effort
        total_effort = sum(e["effort_score"] for e in efforts.values())
        total_time = sum(e["estimated_time_seconds"] for e in efforts.values())

        return {
            "complexity_assessment": {
                "level": complexity.complexity.value,
                "score": complexity.score,
                "reasoning": complexity.reasoning,
            },
            "sub_goals": [
                {
                    "id": sg.sub_goal_id,
                    "description": sg.description,
                    "type": sg.goal_type,
                    "dependencies": sg.dependencies,
                    "effort": efforts[sg.sub_goal_id]["effort_score"],
                    "estimated_time": efforts[sg.sub_goal_id]["estimated_time_seconds"],
                }
                for sg in sub_goals
            ],
            "total_effort": total_effort,
            "estimated_duration_seconds": total_time,
            "execution_order": [sg.sub_goal_id for sg in sub_goals],
        }
