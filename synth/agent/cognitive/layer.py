"""
Cognitive Layer - Unified decision making and progress tracking.

Provides a single interface for all cognitive operations:
- Decision making
- Progress tracking
- Strategy selection
- Tool selection
"""

from typing import Dict, Any, List, Optional

from synth.agent.models.core import (
    Context,
    Plan,
    StrategyType,
    RequestType,
)
from synth.agent.tools.registry import ToolRegistry
from synth.agent.cognitive.decision import DecisionEngine, Decision
from synth.agent.cognitive.progress import ProgressTracker, PlanProgress
from synth.agent.cognitive.strategy import StrategySelector
from synth.agent.cognitive.tool_selector import ToolSelector


class CognitiveLayer:
    """
    Unified cognitive layer for decision making and progress tracking.

    Combines:
    - Decision engine (strategy, tool, parameter selection)
    - Progress tracker (monitoring execution)
    - Strategy selector (autonomous strategy choice)
    - Tool selector (autonomous tool choice)
    """

    def __init__(self, tool_registry: ToolRegistry):
        """
        Initialize cognitive layer.

        Args:
            tool_registry: Tool registry for tool selection
        """
        self.tool_registry = tool_registry
        self.decision_engine = DecisionEngine(tool_registry)
        self.progress_tracker = ProgressTracker()
        self.strategy_selector = StrategySelector()
        self.tool_selector = ToolSelector(tool_registry)

    # ========== Decision Making ==========

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
            Decision object
        """
        return self.decision_engine.make_decision(decision_type, context, **kwargs)

    def make_all_decisions(
        self,
        context: Context,
    ) -> Dict[str, Decision]:
        """
        Make all necessary decisions for a request.

        Returns dict of decision_type -> Decision
        """
        return self.decision_engine.make_comprehensive_decision(context)

    def select_strategy(
        self,
        context: Context,
        available_strategies: Optional[List[StrategyType]] = None,
    ) -> tuple[StrategyType, Dict[str, Any]]:
        """
        Select optimal strategy.

        Returns tuple of (strategy, rationale)
        """
        return self.strategy_selector.select_strategy(context, available_strategies)

    def select_tool(
        self,
        task: str,
        context: Context,
    ) -> tuple[Optional[Any], Dict[str, Any]]:
        """
        Select appropriate tool for a task.

        Returns tuple of (tool, rationale)
        """
        return self.tool_selector.select_tool(task, context)

    def analyze_tradeoffs(
        self,
        option_a: Dict[str, Any],
        option_b: Dict[str, Any],
        criteria: List[str],
        weights: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        """
        Analyze trade-offs between two options.

        Returns trade-off analysis
        """
        tradeoff = self.decision_engine.analyze_tradeoffs(
            option_a, option_b, criteria, weights
        )
        return {
            "option_a": tradeoff.option_a,
            "option_b": tradeoff.option_b,
            "winner": tradeoff.winner,
            "analysis": tradeoff.analysis,
        }

    # ========== Progress Tracking ==========

    def start_tracking(
        self,
        plan: Plan,
    ) -> PlanProgress:
        """
        Start tracking a plan.

        Args:
            plan: Plan to track

        Returns:
            PlanProgress object
        """
        return self.progress_tracker.start_plan(plan)

    def update_step(
        self,
        plan_id: str,
        step,
    ):
        """
        Update progress for a step.

        Args:
            plan_id: Plan ID
            step: Step with updated status
        """
        self.progress_tracker.update_step(plan_id, step)

    def get_progress(
        self,
        plan_id: str,
    ):
        """
        Get progress for a plan.

        Args:
            plan_id: Plan ID

        Returns:
            PlanProgress if found, None otherwise
        """
        return self.progress_tracker.get_progress(plan_id)

    def estimate_completion(
        self,
        plan_id: str,
    ):
        """
        Estimate completion time for a plan.

        Args:
            plan_id: Plan ID

        Returns:
            Estimated completion datetime or None
        """
        return self.progress_tracker.estimate_completion(plan_id)

    def is_stalled(
        self,
        plan_id: str,
    ) -> bool:
        """
        Check if a plan is stalled.

        Args:
            plan_id: Plan ID

        Returns:
            True if stalled, False otherwise
        """
        return self.progress_tracker.detect_stalls(plan_id)

    def set_checkpoint(
        self,
        plan_id: str,
        checkpoint_name: str,
        data: Dict[str, Any],
    ):
        """Set a checkpoint for a plan."""
        self.progress_tracker.set_checkpoint(plan_id, checkpoint_name, data)

    def get_checkpoint(
        self,
        plan_id: str,
        checkpoint_name: str,
    ) -> Optional[Dict[str, Any]]:
        """Get a checkpoint for a plan."""
        return self.progress_tracker.get_checkpoint(plan_id, checkpoint_name)

    def remove_plan(
        self,
        plan_id: str,
    ):
        """Remove a plan from tracking."""
        self.progress_tracker.remove_plan(plan_id)

    # ========== High-Level Planning ==========

    def plan_execution(
        self,
        context: Context,
    ) -> Dict[str, Any]:
        """
        Plan execution for a request.

        Makes all necessary decisions and returns a complete plan.

        Returns:
            Dict containing:
            - decisions: All decisions made
            - plan: Execution plan (if generated)
            - estimated_duration: Estimated time to complete
        """
        # Make all decisions
        decisions = self.make_all_decisions(context)

        result = {
            "decisions": {
                k: {
                    "selection": v.selection.value if hasattr(v.selection, "value") else str(v.selection),
                    "confidence": v.confidence,
                    "rationale": v.rationale,
                }
                for k, v in decisions.items()
            },
            "estimated_duration": None,
        }

        # Estimate duration based on tool cost
        if "tool" in decisions:
            tool_decision = decisions["tool"]
            if tool_decision.selection:
                cost = tool_decision.rationale.get("estimated_cost", {})
                result["estimated_duration"] = cost.get("time_seconds")

        return result

    # ========== Status and Info ==========

    def get_status(self) -> Dict[str, Any]:
        """
        Get cognitive layer status.

        Returns:
            Status information
        """
        active_plans = len(self.progress_tracker.get_all_progress())

        return {
            "active_plans": active_plans,
            "tools_available": len(self.tool_registry.list_tools()),
            "decision_engine_ready": True,
            "progress_tracker_ready": True,
        }
