"""
Adaptive Planning - Dynamic plan adjustment and monitoring.

Implements:
- Adaptive plan creation
- Progress monitoring
- Replanning on failure
- Progress preservation
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

from synth.agent.models.core import (
    Context,
    Plan,
    Step,
    TaskStatus,
)
from synth.agent.planning.planner import PlanningEngine


class PlanHealth(str, Enum):
    """Plan health status."""
    HEALTHY = "healthy"
    STALLED = "stalled"
    FAILING = "failing"
    COMPLETE = "complete"
    FAILED = "failed"


@dataclass
class ProgressSnapshot:
    """Snapshot of plan progress."""
    plan_id: str
    timestamp: datetime
    steps_completed: int
    steps_failed: int
    steps_remaining: int
    elapsed_time_seconds: float
    estimated_remaining_seconds: float
    health: PlanHealth


class AdaptivePlanner:
    """
    Adaptive planning with monitoring and replanning.

    Monitors plan execution and adapts to changes, failures,
    and new information.
    """

    def __init__(self):
        """Initialize adaptive planner."""
        self.planning_engine = PlanningEngine()
        self._snapshots: Dict[str, List[ProgressSnapshot]] = {}

    def create_adaptive_plan(
        self,
        context: Context,
    ) -> Plan:
        """
        Create an adaptive plan that can adjust during execution.

        Args:
            context: Current execution context

        Returns:
            Plan with adaptive capabilities
        """
        plan = self.planning_engine.create_plan(context)

        # Mark plan as adaptive
        plan.metadata["adaptive"] = True
        plan.metadata["replan_threshold"] = 0.5  # Replan if 50% steps fail

        return plan

    def monitor_progress(
        self,
        plan: Plan,
    ) -> ProgressSnapshot:
        """
        Monitor plan progress and health.

        Args:
            plan: Plan to monitor

        Returns:
            ProgressSnapshot with current status
        """
        completed = sum(1 for s in plan.steps if s.status == TaskStatus.COMPLETED)
        failed = sum(1 for s in plan.steps if s.status == TaskStatus.FAILED)
        remaining = sum(1 for s in plan.steps if s.status == TaskStatus.PENDING)
        total = len(plan.steps)

        # Calculate elapsed time
        elapsed = 0.0
        now = datetime.now()
        for step in plan.steps:
            if step.completed_at and step.started_at:
                elapsed += (step.completed_at - step.started_at).total_seconds()

        # Estimate remaining time
        if completed > 0:
            avg_time_per_step = elapsed / completed
            estimated_remaining = avg_time_per_step * remaining
        else:
            estimated_remaining = plan.estimated_duration_seconds - elapsed

        # Determine health
        if completed == total:
            health = PlanHealth.COMPLETE
        elif failed > 0 and failed / total > 0.3:
            health = PlanHealth.FAILING
        elif failed > 0:
            health = PlanHealth.STALLED
        else:
            health = PlanHealth.HEALTHY

        snapshot = ProgressSnapshot(
            plan_id=plan.plan_id,
            timestamp=now,
            steps_completed=completed,
            steps_failed=failed,
            steps_remaining=remaining,
            elapsed_time_seconds=elapsed,
            estimated_remaining_seconds=estimated_remaining,
            health=health,
        )

        # Store snapshot
        if plan.plan_id not in self._snapshots:
            self._snapshots[plan.plan_id] = []
        self._snapshots[plan.plan_id].append(snapshot)

        return snapshot

    def trigger_replan(
        self,
        plan: Plan,
        failed_step: Step,
        error: Exception,
        context: Context,
    ) -> Plan:
        """
        Trigger replanning when a step fails.

        Args:
            plan: Current plan
            failed_step: Step that failed
            error: Exception that occurred
            context: Current execution context

        Returns:
            New adapted plan
        """
        # Save progress before replanning
        snapshot = self.monitor_progress(plan)

        # Create new plan using replanning
        new_plan = self.planning_engine.replan_on_failure(
            plan,
            failed_step,
            error,
            context,
        )

        # Preserve progress metadata
        new_plan.metadata["previous_plan_id"] = plan.plan_id
        new_plan.metadata["replan_count"] = plan.metadata.get("replan_count", 0) + 1
        new_plan.metadata["preserved_progress"] = {
            "steps_completed": snapshot.steps_completed,
            "elapsed_time": snapshot.elapsed_time_seconds,
        }

        # Copy completed steps' results to new plan
        self._preserve_completed_results(plan, new_plan)

        return new_plan

    def _preserve_completed_results(
        self,
        old_plan: Plan,
        new_plan: Plan,
    ):
        """
        Preserve results from completed steps.

        Args:
            old_plan: Original plan
            new_plan: New plan to populate
        """
        # Create mapping of actions to their completed results
        completed_results = {}
        for step in old_plan.steps:
            if step.status == TaskStatus.COMPLETED and step.result is not None:
                completed_results[step.action] = step.result

        # Populate new plan with preserved results
        for step in new_plan.steps:
            if step.action in completed_results:
                step.result = completed_results[step.action]
                step.status = TaskStatus.COMPLETED
                step.completed_at = datetime.now()
                step.started_at = datetime.now()

    def should_replan(
        self,
        plan: Plan,
        context: Context,
    ) -> bool:
        """
        Determine if plan should be replanned.

        Args:
            plan: Current plan
            context: Current execution context

        Returns:
            True if replanning is recommended
        """
        # Get progress snapshot
        snapshot = self.monitor_progress(plan)

        # Check failure threshold
        total_steps = len(plan.steps)
        if total_steps > 0:
            failure_rate = snapshot.steps_failed / total_steps
            threshold = plan.metadata.get("replan_threshold", 0.5)
            if failure_rate > threshold:
                return True

        # Check for stalls
        if self._is_stalled(plan):
            return True

        # Check for resource constraints
        if self._has_resource_constraints(plan, context):
            return True

        return False

    def _is_stalled(
        self,
        plan: Plan,
    ) -> bool:
        """Check if plan is stalled."""
        # Look for steps that are IN_PROGRESS for too long
        now = datetime.now()

        for step in plan.steps:
            if step.status == TaskStatus.IN_PROGRESS:
                if step.started_at:
                    duration = (now - step.started_at).total_seconds()
                    # If step has been running 3x longer than estimated
                    if duration > step.estimated_duration * 3:
                        return True

        return False

    def _has_resource_constraints(
        self,
        plan: Plan,
        context: Context,
    ) -> bool:
        """Check if resource constraints prevent plan continuation."""
        # Low memory
        if context.environment.available_memory_mb < 500:
            return True

        # Low disk space
        if context.environment.available_disk_gb < 1:
            return True

        # No significant resource constraints
        return False

    def adapt_to_changes(
        self,
        plan: Plan,
        context: Context,
        changes: List[str],
    ) -> Plan:
        """
        Adapt plan to environmental changes.

        Args:
            plan: Current plan
            context: Current execution context
            changes: List of detected changes

        Returns:
            Adapted plan
        """
        # For now, return the same plan
        # In a full implementation, this would adjust the plan based on changes

        # If memory is low, reduce batch sizes
        if "memory" in " ".join(changes).lower():
            if context.environment.available_memory_mb < 1000:
                # Reduce counts in generation steps
                for step in plan.steps:
                    if step.action == "generate_data" and "count" in step.parameters:
                        step.parameters["count"] = max(
                            step.parameters["count"] // 2,
                            10
                        )
                        step.estimated_duration *= 0.7

        plan.metadata["adapted_to_changes"] = True
        plan.metadata["changes_detected"] = changes

        return plan

    def get_progress_history(
        self,
        plan_id: str,
    ) -> List[ProgressSnapshot]:
        """
        Get progress history for a plan.

        Args:
            plan_id: Plan ID

        Returns:
            List of progress snapshots
        """
        return self._snapshots.get(plan_id, [])

    def analyze_progress_trend(
        self,
        plan_id: str,
    ) -> Dict[str, Any]:
        """
        Analyze progress trend over time.

        Args:
            plan_id: Plan ID

        Returns:
            Trend analysis
        """
        snapshots = self.get_progress_history(plan_id)

        if len(snapshots) < 2:
            return {
                "trend": "insufficient_data",
                "velocity": 0,
                "eta_accuracy": 0,
            }

        # Calculate velocity (steps per second)
        first = snapshots[0]
        last = snapshots[-1]

        time_diff = (last.timestamp - first.timestamp).total_seconds()
        steps_diff = last.steps_completed - first.steps_completed

        velocity = steps_diff / time_diff if time_diff > 0 else 0

        # Calculate ETA accuracy
        if first.estimated_remaining_seconds > 0:
            eta_accuracy = 1.0 - abs(
                last.estimated_remaining_seconds /
                (first.estimated_remaining_seconds + 1)
            )
        else:
            eta_accuracy = 0

        # Determine trend
        if velocity > 0.1:  # More than 0.1 steps per second
            trend = "on_track"
        elif velocity > 0:
            trend = "slow"
        elif velocity == 0 and last.steps_failed > 0:
            trend = "stalled"
        else:
            trend = "unknown"

        return {
            "trend": trend,
            "velocity": velocity,
            "eta_accuracy": eta_accuracy,
            "health_improvement": self._compare_health(snapshots),
        }

    def _compare_health(
        self,
        snapshots: List[ProgressSnapshot],
    ) -> str:
        """Compare health between first and last snapshot."""
        if len(snapshots) < 2:
            return "unknown"

        first_health = snapshots[0].health
        last_health = snapshots[-1].health

        health_order = [
            PlanHealth.HEALTHY,
            PlanHealth.STALLED,
            PlanHealth.FAILING,
            PlanHealth.FAILED,
        ]

        first_index = health_order.index(first_health) if first_health in health_order else 0
        last_index = health_order.index(last_health) if last_health in health_order else 0

        if last_index < first_index:
            return "improving"
        elif last_index > first_index:
            return "degrading"
        else:
            return "stable"

    def cleanup_history(
        self,
        plan_id: str,
    ):
        """
        Clean up progress history for a plan.

        Args:
            plan_id: Plan ID to clean up
        """
        if plan_id in self._snapshots:
            del self._snapshots[plan_id]
