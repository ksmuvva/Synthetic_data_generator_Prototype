"""
Progress Tracking - Track progress toward goals.

Implements progress monitoring for:
- Step completion
- Time estimation
- Stall detection
- Resource tracking
"""

import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from synth.agent.models.core import (
    Plan,
    Step,
    TaskStatus,
)


@dataclass
class StepProgress:
    """Progress information for a single step."""
    step_id: str
    status: TaskStatus
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: float = 0.0
    error: Optional[str] = None
    progress_percent: float = 0.0


@dataclass
class PlanProgress:
    """Progress information for a plan."""
    plan_id: str
    total_steps: int
    completed_steps: int = 0
    failed_steps: int = 0
    in_progress_steps: int = 0
    pending_steps: int = 0
    start_time: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None
    actual_completion: Optional[datetime] = None
    step_progress: Dict[str, StepProgress] = field(default_factory=dict)

    @property
    def completion_percent(self) -> float:
        """Calculate completion percentage."""
        if self.total_steps == 0:
            return 100.0
        return (self.completed_steps / self.total_steps) * 100

    @property
    def is_stalled(self) -> bool:
        """Check if plan is stalled."""
        # Consider stalled if:
        # 1. Has been running for > 5 minutes
        # 2. No steps completed in last 2 minutes
        # 3. Still has pending/in-progress steps

        if self.start_time is None:
            return False

        running_time = (datetime.now() - self.start_time).total_seconds()

        if running_time < 300:  # Less than 5 minutes
            return False

        if self.pending_steps + self.in_progress_steps == 0:
            return False  # All done or failed

        # Check if any step completed recently
        recent_completions = 0
        for sp in self.step_progress.values():
            if sp.completed_at is not None:
                time_since = (datetime.now() - sp.completed_at).total_seconds()
                if time_since < 120:  # Completed in last 2 minutes
                    recent_completions += 1

        return recent_completions == 0

    @property
    def estimated_time_remaining(self) -> Optional[float]:
        """Estimate time remaining in seconds."""
        if self.completed_steps == 0:
            return None

        # Calculate average time per completed step
        total_time = 0.0
        for sp in self.step_progress.values():
            if sp.status == TaskStatus.COMPLETED:
                total_time += sp.duration_seconds

        avg_time_per_step = total_time / self.completed_steps

        # Estimate remaining time
        remaining_steps = self.pending_steps + self.in_progress_steps
        return avg_time_per_step * remaining_steps


class ProgressTracker:
    """
    Track progress toward goals.

    Monitors:
    1. Step completion
    2. Time estimation
    3. Stall detection
    4. Resource usage
    """

    def __init__(self):
        """Initialize progress tracker."""
        self._plans: Dict[str, PlanProgress] = {}
        self._checkpoints: Dict[str, Dict[str, Any]] = {}

    def start_plan(self, plan: Plan) -> PlanProgress:
        """
        Start tracking a plan.

        Args:
            plan: Plan to track

        Returns:
            PlanProgress object
        """
        progress = PlanProgress(
            plan_id=plan.plan_id,
            total_steps=len(plan.steps),
            start_time=datetime.now(),
        )

        # Initialize step progress
        for step in plan.steps:
            progress.step_progress[step.step_id] = StepProgress(
                step_id=step.step_id,
                status=step.status,
            )

        self._plans[plan.plan_id] = progress
        return progress

    def update_step(
        self,
        plan_id: str,
        step: Step,
    ) -> StepProgress:
        """
        Update progress for a step.

        Args:
            plan_id: Plan ID
            step: Step with updated status

        Returns:
            Updated StepProgress
        """
        if plan_id not in self._plans:
            raise ValueError(f"Plan {plan_id} not being tracked")

        plan_progress = self._plans[plan_id]

        # Get or create step progress
        if step.step_id not in plan_progress.step_progress:
            step_progress = StepProgress(
                step_id=step.step_id,
                status=step.status,
            )
            plan_progress.step_progress[step.step_id] = step_progress
        else:
            step_progress = plan_progress.step_progress[step.step_id]

        # Update based on status
        old_status = step_progress.status
        step_progress.status = step.status

        if old_status != TaskStatus.IN_PROGRESS and step.status == TaskStatus.IN_PROGRESS:
            # Step started
            step_progress.started_at = datetime.now()
            plan_progress.in_progress_steps += 1
            plan_progress.pending_steps -= 1

        elif old_status != TaskStatus.COMPLETED and step.status == TaskStatus.COMPLETED:
            # Step completed
            step_progress.completed_at = datetime.now()
            if step_progress.started_at:
                step_progress.duration_seconds = (
                    step_progress.completed_at - step_progress.started_at
                ).total_seconds()
            step_progress.progress_percent = 100.0

            plan_progress.completed_steps += 1
            plan_progress.in_progress_steps -= 1

            # Update plan completion estimate
            if plan_progress.completed_steps == plan_progress.total_steps:
                plan_progress.actual_completion = datetime.now()
                plan_progress.estimated_completion = datetime.now()

        elif old_status != TaskStatus.FAILED and step.status == TaskStatus.FAILED:
            # Step failed
            step_progress.completed_at = datetime.now()
            if step_progress.started_at:
                step_progress.duration_seconds = (
                    step_progress.completed_at - step_progress.started_at
                ).total_seconds()

            plan_progress.failed_steps += 1
            plan_progress.in_progress_steps -= 1

        # Store error if present
        if step.error:
            step_progress.error = step.error

        return step_progress

    def update_progress(
        self,
        plan_id: str,
        step_id: str,
        progress_percent: float,
    ):
        """
        Update progress percentage for a step.

        Args:
            plan_id: Plan ID
            step_id: Step ID
            progress_percent: Progress percentage (0-100)
        """
        if plan_id not in self._plans:
            return

        plan_progress = self._plans[plan_id]

        if step_id in plan_progress.step_progress:
            step_progress = plan_progress.step_progress[step_id]
            step_progress.progress_percent = max(0.0, min(100.0, progress_percent))

    def get_progress(self, plan_id: str) -> Optional[PlanProgress]:
        """
        Get progress for a plan.

        Args:
            plan_id: Plan ID

        Returns:
            PlanProgress if found, None otherwise
        """
        return self._plans.get(plan_id)

    def estimate_completion(self, plan_id: str) -> Optional[datetime]:
        """
        Estimate completion time for a plan.

        Args:
            plan_id: Plan ID

        Returns:
            Estimated completion datetime or None
        """
        progress = self._plans.get(plan_id)
        if progress is None:
            return None

        # If already complete, return actual completion
        if progress.actual_completion:
            return progress.actual_completion

        # If no completed steps, can't estimate
        if progress.completed_steps == 0:
            return None

        # Estimate based on average time per step
        remaining_seconds = progress.estimated_time_remaining
        if remaining_seconds is None:
            return None

        return datetime.now() + timedelta(seconds=remaining_seconds)

    def detect_stalls(self, plan_id: str) -> bool:
        """
        Detect if a plan is stalled.

        Args:
            plan_id: Plan ID

        Returns:
            True if stalled, False otherwise
        """
        progress = self._plans.get(plan_id)
        if progress is None:
            return False

        return progress.is_stalled

    def set_checkpoint(
        self,
        plan_id: str,
        checkpoint_name: str,
        data: Dict[str, Any],
    ):
        """
        Set a checkpoint for a plan.

        Args:
            plan_id: Plan ID
            checkpoint_name: Checkpoint name
            data: Checkpoint data
        """
        if plan_id not in self._checkpoints:
            self._checkpoints[plan_id] = {}

        self._checkpoints[plan_id][checkpoint_name] = {
            "timestamp": datetime.now().isoformat(),
            "data": data,
        }

    def get_checkpoint(
        self,
        plan_id: str,
        checkpoint_name: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Get a checkpoint for a plan.

        Args:
            plan_id: Plan ID
            checkpoint_name: Checkpoint name

        Returns:
            Checkpoint data if found, None otherwise
        """
        if plan_id not in self._checkpoints:
            return None

        return self._checkpoints[plan_id].get(checkpoint_name)

    def remove_plan(self, plan_id: str):
        """
        Remove a plan from tracking.

        Args:
            plan_id: Plan ID
        """
        self._plans.pop(plan_id, None)
        self._checkpoints.pop(plan_id, None)

    def get_all_progress(self) -> Dict[str, PlanProgress]:
        """
        Get progress for all tracked plans.

        Returns:
            Dict of plan_id -> PlanProgress
        """
        return self._plans.copy()
