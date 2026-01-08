"""
Multi-Objective Optimization Engine.

Handles requests with multiple competing objectives by:
- Identifying conflicting objectives
- Calculating trade-offs
- Finding Pareto-optimal solutions
- Recommending balanced approaches
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import math


class ObjectiveType(str, Enum):
    """Types of optimization objectives."""
    QUALITY = "quality"  # Data quality, realism
    SPEED = "speed"  # Generation speed, time to complete
    PRIVACY = "privacy"  # Privacy preservation, anonymization
    SIZE = "size"  # Dataset size
    DIVERSITY = "diversity"  # Variance, coverage
    COST = "cost"  # Computational cost, API usage


@dataclass
class Objective:
    """An optimization objective."""
    name: str
    objective_type: ObjectiveType
    weight: float = 1.0  # Importance (0-1)
    target: Optional[float] = None  # Target value if any
    constraint: Optional[Tuple[float, float]] = None  # (min, max) bounds

    def normalize_value(self, value: float) -> float:
        """Normalize a value to 0-1 range."""
        if self.constraint:
            min_val, max_val = self.constraint
            if max_val > min_val:
                return (value - min_val) / (max_val - min_val)
        return value


@dataclass
class Solution:
    """A potential solution with objective scores."""
    name: str
    description: str
    objective_scores: Dict[ObjectiveType, float] = field(default_factory=dict)
    overall_score: float = 0.0
    trade_offs: List[str] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)

    def dominates(self, other: 'Solution') -> bool:
        """
        Check if this solution dominates another (Pareto dominance).

        A solution dominates another if it is better or equal in all objectives
        and strictly better in at least one.
        """
        at_least_one_better = False

        for obj_type in set(self.objective_scores.keys()) | set(other.objective_scores.keys()):
            self_score = self.objective_scores.get(obj_type, 0)
            other_score = other.objective_scores.get(obj_type, 0)

            if self_score < other_score:
                return False
            elif self_score > other_score:
                at_least_one_better = True

        return at_least_one_better


@dataclass
class OptimizationResult:
    """Result of multi-objective optimization."""
    recommended_solution: Solution
    pareto_front: List[Solution]
    analysis: str
    trade_off_explanation: str
    objectives: List[Objective]
    confidence: float


class MultiObjectiveOptimizer:
    """
    Multi-objective optimization engine.

    Handles requests with multiple competing objectives and finds
    balanced solutions that optimize across all goals.
    """

    def __init__(self):
        """Initialize multi-objective optimizer."""
        self.solution_strategies = self._init_solution_strategies()

    def optimize(
        self,
        context: 'Context',
        detected_objectives: List[ObjectiveType],
    ) -> OptimizationResult:
        """
        Optimize across multiple objectives.

        Args:
            context: Current execution context
            detected_objectives: List of objective types to optimize

        Returns:
            OptimizationResult with recommended solution
        """
        # Build objectives with default weights
        objectives = self._build_objectives(detected_objectives, context)

        # Generate candidate solutions
        candidates = self._generate_candidates(objectives, context)

        # Calculate Pareto front (non-dominated solutions)
        pareto_front = self._find_pareto_front(candidates)

        # Select recommended solution (balanced or preference-based)
        recommended = self._select_recommended(pareto_front, objectives)

        # Generate analysis and explanation
        analysis = self._generate_analysis(objectives, pareto_front, recommended)
        trade_off_explanation = self._explain_trade_offs(objectives, recommended)

        return OptimizationResult(
            recommended_solution=recommended,
            pareto_front=pareto_front,
            analysis=analysis,
            trade_off_explanation=trade_off_explanation,
            objectives=objectives,
            confidence=self._calculate_confidence(objectives, pareto_front),
        )

    def _init_solution_strategies(self) -> Dict[str, Dict[str, Any]]:
        """Initialize predefined solution strategies."""
        return {
            "quality_focused": {
                "name": "Quality-Focused",
                "description": "Maximize data quality and realism",
                "parameters": {
                    "validation_enabled": True,
                    "statistical_sampling": True,
                    "correlation_preservation": True,
                    "privacy_validation": True,
                },
                "objective_impact": {
                    ObjectiveType.QUALITY: 1.0,
                    ObjectiveType.PRIVACY: 0.9,
                    ObjectiveType.DIVERSITY: 0.85,
                    ObjectiveType.SPEED: 0.4,
                    ObjectiveType.COST: 0.5,
                }
            },
            "speed_focused": {
                "name": "Speed-Focused",
                "description": "Fast generation with acceptable quality",
                "parameters": {
                    "validation_enabled": False,
                    "statistical_sampling": True,
                    "correlation_preservation": False,
                    "batch_size": 1000,
                },
                "objective_impact": {
                    ObjectiveType.QUALITY: 0.6,
                    ObjectiveType.PRIVACY: 0.5,
                    ObjectiveType.DIVERSITY: 0.6,
                    ObjectiveType.SPEED: 1.0,
                    ObjectiveType.COST: 0.9,
                }
            },
            "privacy_focused": {
                "name": "Privacy-Focused",
                "description": "Maximum privacy preservation",
                "parameters": {
                    "privacy_validation": True,
                    "privacy_threshold": 0.98,
                    "anonymization": True,
                    "k_anonymity": True,
                },
                "objective_impact": {
                    ObjectiveType.QUALITY: 0.5,
                    ObjectiveType.PRIVACY: 1.0,
                    ObjectiveType.DIVERSITY: 0.4,
                    ObjectiveType.SPEED: 0.5,
                    ObjectiveType.COST: 0.6,
                }
            },
            "balanced": {
                "name": "Balanced",
                "description": "Balance all objectives equally",
                "parameters": {
                    "validation_enabled": True,
                    "statistical_sampling": True,
                    "correlation_preservation": True,
                    "batch_size": 500,
                },
                "objective_impact": {
                    ObjectiveType.QUALITY: 0.8,
                    ObjectiveType.PRIVACY: 0.8,
                    ObjectiveType.DIVERSITY: 0.75,
                    ObjectiveType.SPEED: 0.7,
                    ObjectiveType.COST: 0.75,
                }
            },
            "resource_efficient": {
                "name": "Resource-Efficient",
                "description": "Minimize computational cost",
                "parameters": {
                    "batch_size": 100,
                    "parallel_workers": 1,
                    "validation_sample_rate": 0.1,
                },
                "objective_impact": {
                    ObjectiveType.QUALITY: 0.6,
                    ObjectiveType.PRIVACY: 0.6,
                    ObjectiveType.DIVERSITY: 0.65,
                    ObjectiveType.SPEED: 0.7,
                    ObjectiveType.COST: 1.0,
                }
            }
        }

    def _build_objectives(
        self,
        detected_objectives: List[ObjectiveType],
        context: 'Context',
    ) -> List[Objective]:
        """Build objective list from detected types."""
        objectives = []

        # Default objectives based on request
        if not detected_objectives:
            detected_objectives = [ObjectiveType.QUALITY, ObjectiveType.SPEED]

        for obj_type in detected_objectives:
            # Set default weights based on context
            weight = 1.0
            if obj_type == ObjectiveType.QUALITY:
                weight = 0.9
            elif obj_type == ObjectiveType.SPEED:
                weight = 0.7
            elif obj_type == ObjectiveType.PRIVACY:
                weight = 0.8

            objectives.append(Objective(
                name=obj_type.value,
                objective_type=obj_type,
                weight=weight,
            ))

        return objectives

    def _generate_candidates(
        self,
        objectives: List[Objective],
        context: 'Context',
    ) -> List[Solution]:
        """Generate candidate solutions."""
        candidates = []

        # Use predefined strategies
        for strategy_key, strategy_data in self.solution_strategies.items():
            # Calculate score for each objective
            objective_scores = {}
            overall_score = 0.0
            total_weight = 0.0

            for obj in objectives:
                impact = strategy_data["objective_impact"].get(obj.objective_type, 0.5)
                objective_scores[obj.objective_type] = impact
                overall_score += impact * obj.weight
                total_weight += obj.weight

            # Normalize overall score
            if total_weight > 0:
                overall_score /= total_weight

            # Identify trade-offs
            trade_offs = self._identify_trade_offs(objective_scores, objectives)

            solution = Solution(
                name=strategy_data["name"],
                description=strategy_data["description"],
                objective_scores=objective_scores,
                overall_score=overall_score,
                trade_offs=trade_offs,
                parameters=strategy_data["parameters"],
            )

            candidates.append(solution)

        return candidates

    def _identify_trade_offs(
        self,
        scores: Dict[ObjectiveType, float],
        objectives: List[Objective],
    ) -> List[str]:
        """Identify trade-offs in a solution."""
        trade_offs = []

        # Find pairs where one objective is sacrificed for another
        for i, obj1 in enumerate(objectives):
            for obj2 in objectives[i+1:]:
                score1 = scores.get(obj1.objective_type, 0.5)
                score2 = scores.get(obj2.objective_type, 0.5)

                # If scores differ significantly, there's a trade-off
                if abs(score1 - score2) > 0.3:
                    if score1 > score2:
                        trade_offs.append(
                            f"Prioritizes {obj1.objective_type.value} over {obj2.objective_type.value}"
                        )
                    else:
                        trade_offs.append(
                            f"Prioritizes {obj2.objective_type.value} over {obj1.objective_type.value}"
                        )

        return trade_offs

    def _find_pareto_front(self, candidates: List[Solution]) -> List[Solution]:
        """Find Pareto-optimal solutions (non-dominated)."""
        pareto_front = []

        for candidate in candidates:
            is_dominated = False
            for other in candidates:
                if other.dominates(candidate):
                    is_dominated = True
                    break

            if not is_dominated:
                pareto_front.append(candidate)

        return pareto_front

    def _select_recommended(
        self,
        pareto_front: List[Solution],
        objectives: List[Objective],
    ) -> Solution:
        """Select recommended solution from Pareto front."""
        if not pareto_front:
            return self.solution_strategies["balanced"]

        # Prefer balanced solution if available
        for solution in pareto_front:
            if "balanced" in solution.name.lower():
                return solution

        # Otherwise, select by weighted score
        best = max(pareto_front, key=lambda s: s.overall_score)
        return best

    def _generate_analysis(
        self,
        objectives: List[Objective],
        pareto_front: List[Solution],
        recommended: Solution,
    ) -> str:
        """Generate analysis text."""
        lines = [
            "Multi-Objective Optimization Analysis",
            "=" * 50,
            "",
            f"Objectives: {', '.join([obj.objective_type.value for obj in objectives])}",
            f"Pareto-optimal solutions found: {len(pareto_front)}",
            "",
            f"Recommended: {recommended.name}",
            f"Overall Score: {recommended.overall_score:.2f}",
            "",
        ]

        # Add objective scores
        lines.append("Objective Scores:")
        for obj_type, score in recommended.objective_scores.items():
            lines.append(f"  - {obj_type.value}: {score:.2f}")

        return "\n".join(lines)

    def _explain_trade_offs(
        self,
        objectives: List[Objective],
        recommended: Solution,
    ) -> str:
        """Generate trade-off explanation."""
        if not recommended.trade_offs:
            return "No significant trade-offs detected."

        lines = [
            "Trade-offs Identified:",
            "",
        ]

        for trade_off in recommended.trade_offs:
            lines.append(f"  - {trade_off}")

        return "\n".join(lines)

    def _calculate_confidence(
        self,
        objectives: List[Objective],
        pareto_front: List[Solution],
    ) -> float:
        """Calculate confidence in the recommendation."""
        # More objectives and more Pareto-optimal solutions = higher complexity
        # which might indicate lower confidence

        base_confidence = 0.8

        # Reduce confidence for many conflicting objectives
        if len(objectives) > 3:
            base_confidence -= 0.1

        # Increase confidence for clear Pareto front
        if len(pareto_front) <= 2:
            base_confidence += 0.1

        return min(1.0, max(0.0, base_confidence))
