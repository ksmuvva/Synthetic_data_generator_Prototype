"""
Decision Engine - Unified decision making for strategies, tools, and parameters.

Implements autonomous decision making considering:
- Strategy selection
- Tool selection
- Parameter optimization
- Trade-off analysis
"""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass

from synth.agent.models.core import (
    Context,
    StrategyType,
    RequestType,
)
from synth.agent.tools.registry import ToolRegistry
from synth.agent.cognitive.strategy import StrategySelector
from synth.agent.cognitive.tool_selector import ToolSelector


@dataclass
class Decision:
    """A decision made by the decision engine."""
    decision_type: str  # "strategy", "tool", "parameter"
    selection: Any
    rationale: Dict[str, Any]
    confidence: float
    alternatives: List[Dict[str, Any]]


@dataclass
class Tradeoff:
    """A trade-off analysis."""
    option_a: Dict[str, Any]
    option_b: Dict[str, Any]
    criteria: List[str]
    winner: str
    analysis: Dict[str, Any]


class DecisionEngine:
    """
    Unified decision making for strategies, tools, and parameters.

    Makes autonomous decisions by:
    1. Selecting optimal strategies
    2. Selecting appropriate tools
    3. Optimizing parameters
    4. Analyzing trade-offs
    """

    def __init__(self, tool_registry: ToolRegistry):
        """
        Initialize decision engine.

        Args:
            tool_registry: Tool registry to use for tool selection
        """
        self.tool_registry = tool_registry
        self.strategy_selector = StrategySelector()
        self.tool_selector = ToolSelector(tool_registry)

    def make_decision(
        self,
        decision_type: str,
        context: Context,
        **kwargs,
    ) -> Decision:
        """
        Make a decision.

        Args:
            decision_type: Type of decision ("strategy", "tool", "parameter")
            context: Current execution context
            **kwargs: Additional decision-specific parameters

        Returns:
            Decision object with selection and rationale
        """
        if decision_type == "strategy":
            return self._select_strategy(context, **kwargs)
        elif decision_type == "tool":
            return self._select_tool(context, **kwargs)
        elif decision_type == "parameter":
            return self._optimize_parameters(context, **kwargs)
        else:
            raise ValueError(f"Unknown decision type: {decision_type}")

    def make_comprehensive_decision(
        self,
        context: Context,
    ) -> Dict[str, Decision]:
        """
        Make all necessary decisions for a request.

        Returns dict of decision_type -> Decision
        """
        decisions = {}

        # 1. Select strategy
        strategy_decision = self._select_strategy(context)
        decisions["strategy"] = strategy_decision

        # 2. Select tool (based on strategy)
        task = context.request.original_text
        tool_decision = self._select_tool(context, task=task)
        decisions["tool"] = tool_decision

        # 3. Optimize parameters (based on strategy and tool)
        param_decision = self._optimize_parameters(
            context,
            strategy=strategy_decision.selection,
            tool=tool_decision.selection,
        )
        decisions["parameters"] = param_decision

        return decisions

    def _select_strategy(
        self,
        context: Context,
        available_strategies: Optional[List[StrategyType]] = None,
    ) -> Decision:
        """Select optimal strategy."""
        strategy, rationale = self.strategy_selector.select_strategy(
            context,
            available_strategies,
        )

        # Calculate confidence
        fit_level = rationale.get("fit_level", "acceptable")
        confidence = self._fit_level_to_confidence(fit_level)

        # Extract alternatives
        alternatives = rationale.get("alternatives", [])

        return Decision(
            decision_type="strategy",
            selection=strategy,
            rationale=rationale,
            confidence=confidence,
            alternatives=alternatives,
        )

    def _select_tool(
        self,
        context: Context,
        task: Optional[str] = None,
    ) -> Decision:
        """Select appropriate tool."""
        if task is None:
            task = context.request.original_text

        tool, rationale = self.tool_selector.select_tool(task, context)

        if tool is None:
            # No tool found
            return Decision(
                decision_type="tool",
                selection=None,
                rationale=rationale,
                confidence=0.0,
                alternatives=[],
            )

        # Calculate confidence
        match_score = rationale.get("match_score", 0.5)
        confidence = match_score

        # Extract alternatives
        alternatives = rationale.get("alternatives", [])

        return Decision(
            decision_type="tool",
            selection=tool,
            rationale=rationale,
            confidence=confidence,
            alternatives=alternatives,
        )

    def _optimize_parameters(
        self,
        context: Context,
        strategy: Optional[StrategyType] = None,
        tool: Optional[Any] = None,
    ) -> Decision:
        """Optimize parameters for strategy/tool."""
        # Get base parameters from context
        base_params = context.request.entities.copy()

        # Apply optimizations
        optimized = self._apply_parameter_optimizations(
            base_params,
            context,
            strategy,
            tool,
        )

        rationale = {
            "original_parameters": base_params,
            "optimized_parameters": optimized,
            "optimizations_applied": self._get_applied_optimizations(
                base_params,
                optimized,
            ),
        }

        return Decision(
            decision_type="parameter",
            selection=optimized,
            rationale=rationale,
            confidence=0.8,  # Parameter optimization is reasonably confident
            alternatives=[],
        )

    def analyze_tradeoffs(
        self,
        option_a: Dict[str, Any],
        option_b: Dict[str, Any],
        criteria: List[str],
        weights: Optional[Dict[str, float]] = None,
    ) -> Tradeoff:
        """
        Analyze trade-offs between two options.

        Args:
            option_a: First option with metrics
            option_b: Second option with metrics
            criteria: List of criteria to compare
            weights: Optional weights for each criterion

        Returns:
            Tradeoff analysis
        """
        if weights is None:
            # Equal weights by default
            weights = {c: 1.0 / len(criteria) for c in criteria}

        scores_a = {}
        scores_b = {}
        analysis = {}

        for criterion in criteria:
            val_a = option_a.get(criterion, 0)
            val_b = option_b.get(criterion, 0)

            # Normalize scores (higher is better)
            if val_a > val_b:
                scores_a[criterion] = 1.0
                scores_b[criterion] = val_b / val_a if val_a != 0 else 0.0
            elif val_b > val_a:
                scores_b[criterion] = 1.0
                scores_a[criterion] = val_a / val_b if val_b != 0 else 0.0
            else:
                scores_a[criterion] = 1.0
                scores_b[criterion] = 1.0

            analysis[criterion] = {
                "option_a": val_a,
                "option_b": val_b,
                "winner": "A" if val_a > val_b else ("B" if val_b > val_a else "tie"),
            }

        # Calculate weighted scores
        weighted_score_a = sum(
            scores_a[c] * weights.get(c, 0)
            for c in criteria
        )
        weighted_score_b = sum(
            scores_b[c] * weights.get(c, 0)
            for c in criteria
        )

        # Determine winner
        winner = "A" if weighted_score_a > weighted_score_b else "B"

        return Tradeoff(
            option_a=option_a,
            option_b=option_b,
            criteria=criteria,
            winner=winner,
            analysis={
                "scores": {"A": scores_a, "B": scores_b},
                "weighted_scores": {"A": weighted_score_a, "B": weighted_score_b},
                "weights": weights,
                "detailed": analysis,
            },
        )

    def _apply_parameter_optimizations(
        self,
        params: Dict[str, Any],
        context: Context,
        strategy: Optional[StrategyType],
        tool: Optional[Any],
    ) -> Dict[str, Any]:
        """Apply parameter optimizations."""
        optimized = params.copy()

        # Optimize count based on memory
        if "count" in optimized:
            count = optimized["count"]
            available_memory = context.environment.available_memory_mb

            # Adjust count if memory is limited
            if count > 10000 and available_memory < 1000:
                optimized["count"] = min(count, 5000)
                optimized["memory_adjusted"] = True

        # Add strategy-specific optimizations
        if strategy == StrategyType.COPULA:
            # Copula needs sufficient samples
            if "count" in optimized and optimized["count"] < 100:
                optimized["count"] = max(optimized["count"], 100)
                optimized["strategy_adjusted"] = True

        return optimized

    def _get_applied_optimizations(
        self,
        original: Dict[str, Any],
        optimized: Dict[str, Any],
    ) -> List[str]:
        """Get list of applied optimizations."""
        optimizations = []

        for key in optimized:
            if key in original:
                if original[key] != optimized[key]:
                    optimizations.append(
                        f"{key}: {original[key]} -> {optimized[key]}"
                    )
            else:
                optimizations.append(f"{key}: added = {optimized[key]}")

        return optimizations

    def _fit_level_to_confidence(self, fit_level: str) -> float:
        """Convert fit level to confidence score."""
        mapping = {
            "excellent": 0.95,
            "good": 0.80,
            "acceptable": 0.60,
            "poor": 0.40,
        }
        return mapping.get(fit_level.lower(), 0.50)
