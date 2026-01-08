"""
Reasoning Engine - Unified reasoning engine.

Implements:
- Problem analysis
- Alternative generation
- Evaluation
- Consistency checking
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from synth.agent.models.core import Context
from synth.agent.reasoning.analyzer import (
    ProblemAnalyzer,
    ProblemAnalysis,
    ProblemType,
    ProblemComplexity,
)


@dataclass
class ReasoningResult:
    """Result of reasoning process."""
    problem_analysis: ProblemAnalysis
    alternatives: List[Dict[str, Any]]
    evaluation: Dict[str, Any]
    consistency_checks: List[Dict[str, Any]]
    recommendation: Dict[str, Any]
    confidence: float


class ReasoningEngine:
    """
    Unified reasoning engine.

    Coordinates:
    1. Problem analysis
    2. Alternative generation
    3. Evaluation
    4. Consistency checking
    """

    def __init__(self):
        """Initialize reasoning engine."""
        self.problem_analyzer = ProblemAnalyzer()

    def analyze(
        self,
        context: Context,
    ) -> ProblemAnalysis:
        """
        Analyze the problem.

        Args:
            context: Current execution context

        Returns:
            ProblemAnalysis object
        """
        return self.problem_analyzer.analyze(context)

    def generate_alternatives(
        self,
        context: Context,
        problem_analysis: Optional[ProblemAnalysis] = None,
        count: int = 3,
    ) -> List[Dict[str, Any]]:
        """
        Generate solution alternatives.

        Args:
            context: Current execution context
            problem_analysis: Optional pre-computed problem analysis
            count: Number of alternatives to generate

        Returns:
            List of alternative dicts
        """
        if problem_analysis is None:
            problem_analysis = self.analyze(context)

        alternatives = []

        # Generate alternatives based on problem type
        if problem_analysis.problem_type == ProblemType.DATA_GENERATION:
            alternatives = self._generate_generation_alternatives(
                context,
                count,
            )
        elif problem_analysis.problem_type == ProblemType.MULTI_STEP:
            alternatives = self._generate_multistep_alternatives(
                context,
                count,
            )
        else:
            alternatives = self._generate_generic_alternatives(
                context,
                count,
            )

        return alternatives

    def evaluate(
        self,
        context: Context,
        alternatives: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Evaluate alternatives.

        Args:
            context: Current execution context
            alternatives: List of alternatives to evaluate

        Returns:
            Evaluation results
        """
        evaluations = []

        for i, alt in enumerate(alternatives):
            # Calculate score
            score = self._calculate_alternative_score(alt, context)

            # Identify pros and cons
            pros, cons = self._identify_pros_cons(alt, context)

            evaluations.append({
                "index": i,
                "alternative": alt,
                "score": score,
                "pros": pros,
                "cons": cons,
            })

        # Sort by score
        evaluations.sort(key=lambda x: x["score"], reverse=True)

        return {
            "evaluations": evaluations,
            "best": evaluations[0] if evaluations else None,
            "worst": evaluations[-1] if evaluations else None,
        }

    def check_consistency(
        self,
        context: Context,
        plan: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Check for logical conflicts.

        Args:
            context: Current execution context
            plan: Optional plan to check

        Returns:
            List of consistency issues
        """
        issues = []

        # Check for conflicting constraints
        constraint_conflicts = self._check_conflicting_constraints(context)
        if constraint_conflicts:
            issues.append({
                "type": "conflicting_constraints",
                "description": "Conflicting constraints detected",
                "details": constraint_conflicts,
            })

        # Check for impossible requirements
        impossible_reqs = self._check_impossible_requirements(context)
        if impossible_reqs:
            issues.append({
                "type": "impossible_requirements",
                "description": "Impossible requirements detected",
                "details": impossible_reqs,
            })

        # Check for resource conflicts
        resource_conflicts = self._check_resource_conflicts(context)
        if resource_conflicts:
            issues.append({
                "type": "resource_conflict",
                "description": "Resource conflicts detected",
                "details": resource_conflicts,
            })

        return issues

    def reason_comprehensive(
        self,
        context: Context,
    ) -> ReasoningResult:
        """
        Perform comprehensive reasoning.

        Args:
            context: Current execution context

        Returns:
            Complete reasoning result
        """
        # 1. Analyze problem
        problem_analysis = self.analyze(context)

        # 2. Generate alternatives
        alternatives = self.generate_alternatives(context, problem_analysis)

        # 3. Evaluate alternatives
        evaluation = self.evaluate(context, alternatives)

        # 4. Check consistency
        consistency_checks = self.check_consistency(context)

        # 5. Make recommendation
        recommendation = self._make_recommendation(
            problem_analysis,
            alternatives,
            evaluation,
            consistency_checks,
        )

        # 6. Calculate overall confidence
        confidence = self._calculate_overall_confidence(
            problem_analysis,
            evaluation,
            consistency_checks,
        )

        return ReasoningResult(
            problem_analysis=problem_analysis,
            alternatives=alternatives,
            evaluation=evaluation,
            consistency_checks=consistency_checks,
            recommendation=recommendation,
            confidence=confidence,
        )

    def _generate_generation_alternatives(
        self,
        context: Context,
        count: int,
    ) -> List[Dict[str, Any]]:
        """Generate alternatives for data generation."""
        alternatives = []

        strategies = ["statistical", "constrained", "copula"]

        for i, strategy in enumerate(strategies[:count]):
            alternatives.append({
                "strategy": strategy,
                "description": f"Use {strategy} generation strategy",
                "estimated_time": self._estimate_time_for_strategy(strategy, context),
                "estimated_quality": self._estimate_quality_for_strategy(strategy, context),
            })

        return alternatives

    def _generate_multistep_alternatives(
        self,
        context: Context,
        count: int,
    ) -> List[Dict[str, Any]]:
        """Generate alternatives for multi-step problems."""
        alternatives = []

        # Alternative 1: Sequential execution
        alternatives.append({
            "approach": "sequential",
            "description": "Execute steps sequentially",
            "parallelism": False,
            "estimated_time": "medium",
        })

        # Alternative 2: Parallel where possible
        alternatives.append({
            "approach": "selective_parallel",
            "description": "Execute independent steps in parallel",
            "parallelism": True,
            "estimated_time": "fast",
        })

        # Alternative 3: Optimized ordering
        alternatives.append({
            "approach": "optimized_order",
            "description": "Reorder steps for efficiency",
            "parallelism": False,
            "estimated_time": "medium-fast",
        })

        return alternatives[:count]

    def _generate_generic_alternatives(
        self,
        context: Context,
        count: int,
    ) -> List[Dict[str, Any]]:
        """Generate generic alternatives."""
        alternatives = []

        for i in range(count):
            alternatives.append({
                "option": f"option_{i+1}",
                "description": f"Alternative approach {i+1}",
                "estimated_effort": "medium",
            })

        return alternatives

    def _calculate_alternative_score(
        self,
        alternative: Dict[str, Any],
        context: Context,
    ) -> float:
        """Calculate score for an alternative."""
        score = 0.5  # Base score

        # Bonus for having strategy
        if "strategy" in alternative:
            score += 0.2

        # Bonus for having description
        if "description" in alternative:
            score += 0.1

        # Bonus for quality estimate
        if alternative.get("estimated_quality") == "high":
            score += 0.2
        elif alternative.get("estimated_quality") == "medium":
            score += 0.1

        # Bonus for parallelism
        if alternative.get("parallelism"):
            score += 0.1

        return min(score, 1.0)

    def _identify_pros_cons(
        self,
        alternative: Dict[str, Any],
        context: Context,
    ) -> tuple[List[str], List[str]]:
        """Identify pros and cons of an alternative."""
        pros = []
        cons = []

        strategy = alternative.get("strategy", "")

        if strategy == "statistical":
            pros.append("Fast generation")
            pros.append("Memory efficient")
            cons.append("May not capture complex correlations")
        elif strategy == "copula":
            pros.append("Preserves correlations")
            cons.append("Slower generation")
            cons.append("Higher memory usage")
        elif strategy == "constrained":
            pros.append("Honors constraints")
            cons.append("May be slower")

        if alternative.get("parallelism"):
            pros.append("Can run in parallel")
            cons.append("More complex coordination")

        return pros, cons

    def _check_conflicting_constraints(
        self,
        context: Context,
    ) -> List[str]:
        """Check for conflicting constraints."""
        conflicts = []

        # Example: count conflicts
        count = context.request.entities.get("count")
        if count and count > 100000:
            if context.environment.available_memory_mb < 2000:
                conflicts.append(
                    f"Cannot generate {count} records with {context.environment.available_memory_mb:.0f}MB memory"
                )

        return conflicts

    def _check_impossible_requirements(
        self,
        context: Context,
    ) -> List[str]:
        """Check for impossible requirements."""
        impossible = []

        # Check for negative counts
        count = context.request.entities.get("count")
        if count is not None and count < 0:
            impossible.append("Count cannot be negative")

        return impossible

    def _check_resource_conflicts(
        self,
        context: Context,
    ) -> List[str]:
        """Check for resource conflicts."""
        conflicts = []

        # Check if memory is too low
        if context.environment.available_memory_mb < 100:
            conflicts.append("Very low memory available")

        return conflicts

    def _make_recommendation(
        self,
        problem_analysis: ProblemAnalysis,
        alternatives: List[Dict[str, Any]],
        evaluation: Dict[str, Any],
        consistency_checks: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Make recommendation based on all reasoning."""
        recommendation = {
            "problem_type": problem_analysis.problem_type.value,
            "complexity": problem_analysis.complexity.value,
            "suggested_approach": None,
            "reasoning": [],
        }

        # Get best alternative
        if evaluation.get("best"):
            best = evaluation["best"]
            recommendation["suggested_approach"] = best["alternative"]
            recommendation["reasoning"].append(
                f"Selected best alternative with score {best['score']:.2f}"
            )

        # Add warnings if consistency issues found
        if consistency_checks:
            recommendation["warnings"] = [
                issue["description"]
                for issue in consistency_checks
            ]
            recommendation["reasoning"].append(
                f"Found {len(consistency_checks)} consistency issues"
            )

        return recommendation

    def _calculate_overall_confidence(
        self,
        problem_analysis: ProblemAnalysis,
        evaluation: Dict[str, Any],
        consistency_checks: List[Dict[str, Any]],
    ) -> float:
        """Calculate overall confidence in reasoning."""
        confidence = problem_analysis.confidence

        # Reduce confidence if there are consistency issues
        if consistency_checks:
            confidence *= 0.8

        return confidence

    def _estimate_time_for_strategy(
        self,
        strategy: str,
        context: Context,
    ) -> str:
        """Estimate time for a strategy."""
        if strategy == "statistical":
            return "fast"
        elif strategy == "copula":
            return "slow"
        else:
            return "medium"

    def _estimate_quality_for_strategy(
        self,
        strategy: str,
        context: Context,
    ) -> str:
        """Estimate quality for a strategy."""
        if strategy == "copula":
            return "high"
        elif strategy == "statistical":
            return "medium"
        else:
            return "medium"
