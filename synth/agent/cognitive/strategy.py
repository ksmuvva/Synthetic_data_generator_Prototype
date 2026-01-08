"""
Strategy Selection - Autonomous strategy selection based on context.

Implements intelligent strategy selection considering:
- Data characteristics
- User preferences
- Past success rates
- Resource constraints
"""

from typing import Optional, Dict, Any, List
from enum import Enum

from synth.agent.models.core import (
    Context,
    RequestType,
    StrategyType,
)


class StrategyFit(str, Enum):
    """Strategy fit level."""
    EXCELLENT = "excellent"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    POOR = "poior"


class StrategySelector:
    """
    Autonomous strategy selection based on context.

    Selects optimal generation/analysis strategies by evaluating:
    1. Data characteristics (size, types, distributions)
    2. User preferences (from memory)
    3. Past success rates (learned from history)
    4. Resource constraints (memory, CPU, time)
    """

    def __init__(self):
        """Initialize strategy selector."""
        # Strategy effectiveness weights
        self._weights = {
            "past_success": 0.4,
            "data_fit": 0.3,
            "resource_efficiency": 0.2,
            "user_preference": 0.1,
        }

    def select_strategy(
        self,
        context: Context,
        available_strategies: Optional[List[StrategyType]] = None,
    ) -> tuple[StrategyType, Dict[str, Any]]:
        """
        Select optimal strategy for the current context.

        Args:
            context: Current execution context
            available_strategies: Optional list of strategies to consider

        Returns:
            Tuple of (selected_strategy, rationale)
        """
        # Default strategies for each request type
        if available_strategies is None:
            available_strategies = self._get_default_strategies(context.request.request_type)

        # Evaluate each strategy
        evaluations = []
        for strategy in available_strategies:
            fit_score, rationale = self._evaluate_strategy_fit(strategy, context)
            evaluations.append((strategy, fit_score, rationale))

        # Sort by fit score
        evaluations.sort(key=lambda x: x[1].value, reverse=True)

        # Select best strategy
        best_strategy, best_fit, best_rationale = evaluations[0]

        # Combine rationales
        combined_rationale = {
            "selected_strategy": best_strategy.value,
            "fit_level": best_fit.value,
            "reasoning": best_rationale,
            "considered": len(evaluations),
            "alternatives": [
                {
                    "strategy": s.value,
                    "fit": f.value,
                }
                for s, f, _ in evaluations[1:]
            ],
        }

        return best_strategy, combined_rationale

    def _evaluate_strategy_fit(
        self,
        strategy: StrategyType,
        context: Context,
    ) -> tuple[StrategyFit, Dict[str, Any]]:
        """
        Evaluate how well a strategy fits the current context.

        Returns tuple of (fit_level, rationale)
        """
        scores = {}
        rationale_parts = []

        # 1. Check data characteristics fit
        data_fit, data_reasoning = self._evaluate_data_fit(strategy, context)
        scores["data_fit"] = self._fit_to_score(data_fit)
        rationale_parts.append(data_reasoning)

        # 2. Check past success rates
        past_success, success_reasoning = self._evaluate_past_success(strategy, context)
        scores["past_success"] = past_success
        rationale_parts.append(success_reasoning)

        # 3. Check resource efficiency
        resource_fit, resource_reasoning = self._evaluate_resource_fit(strategy, context)
        scores["resource_efficiency"] = self._fit_to_score(resource_fit)
        rationale_parts.append(resource_reasoning)

        # 4. Check user preferences
        user_preference, user_reasoning = self._evaluate_user_preference(strategy, context)
        scores["user_preference"] = user_preference
        rationale_parts.append(user_reasoning)

        # Calculate weighted score
        weighted_score = sum(
            scores[k] * self._weights[k]
            for k in self._weights
        )

        # Determine fit level
        if weighted_score >= 0.8:
            fit = StrategyFit.EXCELLENT
        elif weighted_score >= 0.6:
            fit = StrategyFit.GOOD
        elif weighted_score >= 0.4:
            fit = StrategyFit.ACCEPTABLE
        else:
            fit = StrategyFit.POOR

        rationale = {
            "weighted_score": weighted_score,
            "component_scores": scores,
            "reasoning": rationale_parts,
        }

        return fit, rationale

    def _evaluate_data_fit(
        self,
        strategy: StrategyType,
        context: Context,
    ) -> tuple[StrategyFit, str]:
        """Evaluate how well strategy fits data characteristics."""
        # Get data size from context
        data = context.working_variables.get("data")
        if data is None:
            return StrategyFit.ACCEPTABLE, "No data available for analysis"

        # Estimate data size
        try:
            data_size = len(data)
        except:
            return StrategyFit.ACCEPTABLE, "Could not determine data size"

        # Different strategies for different data sizes
        if strategy == StrategyType.STATISTICAL:
            if data_size < 1000:
                return StrategyFit.EXCELLENT, f"Statistical strategy ideal for {data_size} records"
            elif data_size < 10000:
                return StrategyFit.GOOD, f"Statistical strategy suitable for {data_size} records"
            else:
                return StrategyFit.ACCEPTABLE, f"Statistical strategy may be slow for {data_size} records"

        elif strategy == StrategyType.CONSTRAINED:
            if data_size < 5000:
                return StrategyFit.GOOD, f"Constrained strategy good for {data_size} records with complex constraints"
            else:
                return StrategyFit.ACCEPTABLE, f"Constrained strategy acceptable for {data_size} records"

        elif strategy == StrategyType.COPULA:
            if data_size >= 1000:
                return StrategyFit.EXCELLENT, f"Copula strategy excellent for {data_size} records (correlations preserved)"
            else:
                return StrategyFit.ACCEPTABLE, f"Copula strategy acceptable but may be overkill for {data_size} records"

        return StrategyFit.ACCEPTABLE, "Strategy compatible with data characteristics"

    def _evaluate_past_success(
        self,
        strategy: StrategyType,
        context: Context,
    ) -> tuple[float, str]:
        """
        Evaluate past success rate of strategy.

        Returns tuple of (success_rate_0_to_1, reasoning)
        """
        # Check if we have past data about this strategy
        strategy_key = strategy.value

        # Look in similar past situations
        similar_situations = context.similar_past_situations or []
        success_count = 0
        total_count = 0

        for situation in similar_situations:
            if situation.get("strategy") == strategy_key:
                total_count += 1
                if situation.get("success", False):
                    success_count += 1

        if total_count == 0:
            # No past experience - neutral rating
            return 0.5, f"No past experience with {strategy_key} strategy"

        success_rate = success_count / total_count

        if success_rate >= 0.9:
            return success_rate, f"Excellent past success rate ({success_count}/{total_count}) for {strategy_key}"
        elif success_rate >= 0.7:
            return success_rate, f"Good past success rate ({success_count}/{total_count}) for {strategy_key}"
        elif success_rate >= 0.5:
            return success_rate, f"Moderate past success rate ({success_count}/{total_count}) for {strategy_key}"
        else:
            return success_rate, f"Poor past success rate ({success_count}/{total_count}) for {strategy_key}"

    def _evaluate_resource_fit(
        self,
        strategy: StrategyType,
        context: Context,
    ) -> tuple[StrategyFit, str]:
        """Evaluate resource efficiency of strategy."""
        env = context.environment

        # Check memory availability
        available_memory_gb = env.available_memory_mb / 1024

        if available_memory_gb < 1.0:
            # Low memory - prefer simpler strategies
            if strategy == StrategyType.STATISTICAL:
                return StrategyFit.EXCELLENT, "Statistical strategy is memory-efficient"
            elif strategy == StrategyType.COPULA:
                return StrategyFit.POOR, "Copula strategy requires significant memory"
        elif available_memory_gb >= 4.0:
            # Plenty of memory - all strategies fine
            return StrategyFit.GOOD, f"Good memory availability ({available_memory_gb:.1f} GB)"

        # Check CPU availability
        if env.available_cpu_percent < 20:
            # Low CPU - prefer faster strategies
            if strategy == StrategyType.STATISTICAL:
                return StrategyFit.EXCELLENT, "Statistical strategy is CPU-efficient"
            else:
                return StrategyFit.ACCEPTABLE, "Strategy acceptable with limited CPU"

        return StrategyFit.GOOD, "Resource availability sufficient for this strategy"

    def _evaluate_user_preference(
        self,
        strategy: StrategyType,
        context: Context,
    ) -> tuple[float, str]:
        """
        Evaluate user preference for strategy.

        Returns tuple of (preference_score_0_to_1, reasoning)
        """
        user_prefs = context.user_preferences or {}

        # Check if user has a preferred strategy
        preferred_strategy = user_prefs.get("preferred_strategy")

        if preferred_strategy is None:
            return 0.5, "No user preference specified"

        if preferred_strategy == strategy.value:
            return 1.0, f"Strategy matches user preference ({preferred_strategy})"
        else:
            return 0.3, f"Strategy differs from user preference ({preferred_strategy})"

    def _get_default_strategies(self, request_type: RequestType) -> List[StrategyType]:
        """Get default strategies for a request type."""
        if request_type == RequestType.DATA_GENERATION:
            return [
                StrategyType.STATISTICAL,
                StrategyType.CONSTRAINED,
                StrategyType.COPULA,
            ]
        elif request_type == RequestType.DATA_VALIDATION:
            return [
                StrategyType.STATISTICAL,
            ]
        elif request_type == RequestType.DATA_ANALYSIS:
            return [
                StrategyType.STATISTICAL,
            ]
        else:
            return [
                StrategyType.STATISTICAL,
            ]

    def _fit_to_score(self, fit: StrategyFit) -> float:
        """Convert StrategyFit to numeric score."""
        mapping = {
            StrategyFit.EXCELLENT: 1.0,
            StrategyFit.GOOD: 0.75,
            StrategyFit.ACCEPTABLE: 0.5,
            StrategyFit.POOR: 0.25,
        }
        return mapping.get(fit, 0.5)
