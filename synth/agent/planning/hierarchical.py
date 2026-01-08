"""
Hierarchical Goal Planning - Long-term planning with milestones.

Implements:
- Hierarchical goal decomposition
- Goal progress tracking
- Goal revision based on progress
- Milestone tracking
- Long-term planning
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import time
from datetime import datetime, timedelta

from synth.agent.models.core import Context, Goal, SubGoal, Plan, Step, TaskStatus


class GoalStatus(str, Enum):
    """Status of a goal."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    PARTIALLY_COMPLETE = "partially_complete"
    COMPLETED = "completed"
    FAILED = "failed"
    REVISED = "revised"
    CANCELLED = "cancelled"


class MilestoneStatus(str, Enum):
    """Status of a milestone."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    ACHIEVED = "achieved"
    MISSED = "missed"
    CANCELLED = "cancelled"


@dataclass
class Milestone:
    """A milestone in goal achievement."""
    milestone_id: str
    name: str
    description: str
    target_value: float
    current_value: float
    status: MilestoneStatus
    deadline: Optional[datetime]
    dependencies: List[str]
    created_at: datetime


@dataclass
class HierarchicalGoal:
    """A hierarchical goal with sub-goals."""
    goal_id: str
    name: str
    description: str
    priority: float  # 0-1
    status: GoalStatus
    progress: float  # 0-1
    sub_goals: List[SubGoal]
    milestones: List[Milestone]
    parent_goal_id: Optional[str]
    created_at: datetime
    updated_at: datetime
    deadline: Optional[datetime]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GoalRevision:
    """A revision to a goal."""
    revision_id: str
    goal_id: str
    old_description: str
    new_description: str
    reason: str
    timestamp: datetime
    progress_at_revision: float


class HierarchicalGoalManager:
    """
    Hierarchical goal management system.

    Features:
    - Decompose high-level goals into sub-goals
    - Track progress towards goals
    - Revise goals based on progress
    - Monitor milestones
    - Support long-term planning
    """

    def __init__(self, max_hierarchy_depth: int = 3):
        """
        Initialize hierarchical goal manager.

        Args:
            max_hierarchy_depth: Maximum depth of goal hierarchy
        """
        self.max_hierarchy_depth = max_hierarchy_depth
        self._goals: Dict[str, HierarchicalGoal] = {}
        self._goal_hierarchy: Dict[str, List[str]] = {}  # parent -> children
        self._revisions: List[GoalRevision] = []
        self._progress_history: Dict[str, List[Tuple[float, float]]] = {}

    def create_hierarchical_goal(
        self,
        name: str,
        description: str,
        priority: float,
        deadline: Optional[datetime] = None,
        parent_goal_id: Optional[str] = None,
    ) -> HierarchicalGoal:
        """
        Create a new hierarchical goal.

        Args:
            name: Goal name
            description: Goal description
            priority: Priority (0-1)
            deadline: Optional deadline
            parent_goal_id: Optional parent goal

        Returns:
            Created hierarchical goal
        """
        goal_id = f"goal_{len(self._goals) + 1}_{int(time.time())}"

        # Decompose into sub-goals
        sub_goals = self._decompose_goal(description)

        # Create milestones
        milestones = self._create_milestones(description, deadline)

        goal = HierarchicalGoal(
            goal_id=goal_id,
            name=name,
            description=description,
            priority=priority,
            status=GoalStatus.PENDING,
            progress=0.0,
            sub_goals=sub_goals,
            milestones=milestones,
            parent_goal_id=parent_goal_id,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            deadline=deadline,
        )

        self._goals[goal_id] = goal

        # Update hierarchy
        if parent_goal_id:
            if parent_goal_id not in self._goal_hierarchy:
                self._goal_hierarchy[parent_goal_id] = []
            self._goal_hierarchy[parent_goal_id].append(goal_id)

        # Initialize progress tracking
        self._progress_history[goal_id] = []

        return goal

    def _decompose_goal(self, description: str) -> List[SubGoal]:
        """Decompose high-level goal into sub-goals."""
        sub_goals = []

        desc_lower = description.lower()

        # Multi-objective goals
        if any(word in desc_lower for word in ["and", "then", "followed by"]):
            # Split into components
            if "generate" in desc_lower:
                sub_goals.append(SubGoal(
                    goal_id=f"sub_{len(sub_goals) + 1}",
                    description="Generate synthetic data",
                    priority=0.8,
                    dependencies=[],
                ))

            if "validate" in desc_lower:
                sub_goals.append(SubGoal(
                    goal_id=f"sub_{len(sub_goals) + 1}",
                    description="Validate data quality",
                    priority=0.7,
                    dependencies=["sub_1"] if len(sub_goals) > 0 else [],
                ))

            if "export" in desc_lower:
                sub_goals.append(SubGoal(
                    goal_id=f"sub_{len(sub_goals) + 1}",
                    description="Export data to file",
                    priority=0.6,
                    dependencies=[f"sub_{len(sub_goals)}"],
                ))

        else:
            # Single objective - create phases
            sub_goals.append(SubGoal(
                goal_id="sub_1",
                description="Preparation phase",
                priority=0.9,
                dependencies=[],
            ))

            sub_goals.append(SubGoal(
                goal_id="sub_2",
                description="Execution phase",
                priority=0.8,
                dependencies=["sub_1"],
            ))

            sub_goals.append(SubGoal(
                goal_id="sub_3",
                description="Completion phase",
                priority=0.7,
                dependencies=["sub_2"],
            ))

        return sub_goals

    def _create_milestones(
        self,
        description: str,
        deadline: Optional[datetime],
    ) -> List[Milestone]:
        """Create milestones for tracking progress."""
        milestones = []

        # Common milestones
        milestones.append(Milestone(
            milestone_id="milestone_1",
            name="Start",
            description="Goal initiated",
            target_value=0.0,
            current_value=0.0,
            status=MilestoneStatus.NOT_STARTED,
            deadline=None,
            dependencies=[],
            created_at=datetime.now(),
        ))

        milestones.append(Milestone(
            milestone_id="milestone_2",
            name="25% Complete",
            description="Quarter progress",
            target_value=0.25,
            current_value=0.0,
            status=MilestoneStatus.NOT_STARTED,
            deadline=None,
            dependencies=["milestone_1"],
            created_at=datetime.now(),
        ))

        milestones.append(Milestone(
            milestone_id="milestone_3",
            name="50% Complete",
            description="Halfway point",
            target_value=0.5,
            current_value=0.0,
            status=MilestoneStatus.NOT_STARTED,
            deadline=None,
            dependencies=["milestone_2"],
            created_at=datetime.now(),
        ))

        milestones.append(Milestone(
            milestone_id="milestone_4",
            name="75% Complete",
            description="Three-quarters progress",
            target_value=0.75,
            current_value=0.0,
            status=MilestoneStatus.NOT_STARTED,
            deadline=None,
            dependencies=["milestone_3"],
            created_at=datetime.now(),
        ))

        milestones.append(Milestone(
            milestone_id="milestone_5",
            name="Complete",
            description="Goal achieved",
            target_value=1.0,
            current_value=0.0,
            status=MilestoneStatus.NOT_STARTED,
            deadline=deadline,
            dependencies=["milestone_4"],
            created_at=datetime.now(),
        ))

        return milestones

    def update_progress(
        self,
        goal_id: str,
        progress: float,
        step_results: Optional[Dict[str, Any]] = None,
    ):
        """
        Update progress towards a goal.

        Args:
            goal_id: Goal ID
            progress: Progress value (0-1)
            step_results: Optional step execution results
        """
        if goal_id not in self._goals:
            return

        goal = self._goals[goal_id]

        # Record progress in history
        self._progress_history[goal_id].append((time.time(), progress))

        # Update goal progress
        old_progress = goal.progress
        goal.progress = min(max(progress, 0.0), 1.0)
        goal.updated_at = datetime.now()

        # Update status
        if goal.progress >= 1.0:
            goal.status = GoalStatus.COMPLETED
        elif goal.progress > old_progress:
            if goal.status == GoalStatus.PENDING:
                goal.status = GoalStatus.IN_PROGRESS

        # Update milestones
        self._update_milestones(goal)

        # Check if goal revision is needed
        if self._should_revise_goal(goal, step_results):
            self._revise_goal(goal, step_results)

        # Update parent goals
        if goal.parent_goal_id:
            self._update_parent_progress(goal.parent_goal_id)

    def _update_milestones(self, goal: HierarchicalGoal):
        """Update milestone statuses based on progress."""
        for milestone in goal.milestones:
            milestone.current_value = goal.progress

            if milestone.current_value >= milestone.target_value:
                if milestone.status != MilestoneStatus.ACHIEVED:
                    milestone.status = MilestoneStatus.ACHIEVED
            elif milestone.current_value > 0:
                if milestone.status == MilestoneStatus.NOT_STARTED:
                    milestone.status = MilestoneStatus.IN_PROGRESS

        # Check for missed deadlines
        if goal.deadline:
            for milestone in goal.milestones:
                if milestone.deadline and milestone.status != MilestoneStatus.ACHIEVED:
                    if datetime.now() > milestone.deadline:
                        milestone.status = MilestoneStatus.MISSED

    def _should_revise_goal(
        self,
        goal: HierarchicalGoal,
        step_results: Optional[Dict[str, Any]],
    ) -> bool:
        """Check if goal should be revised based on progress."""
        # Check if progress is too slow
        if len(self._progress_history[goal.goal_id]) > 2:
            recent_progress = self._progress_history[goal.goal_id][-5:]
            if len(recent_progress) >= 2:
                time_diff = recent_progress[-1][0] - recent_progress[0][0]
                progress_diff = recent_progress[-1][1] - recent_progress[0][1]

                # If very slow progress
                if time_diff > 60 and progress_diff < 0.1:
                    return True

        # Check if there were failures
        if step_results and not step_results.get("success", True):
            return True

        # Check deadline proximity
        if goal.deadline:
            time_remaining = (goal.deadline - datetime.now()).total_seconds()
            if time_remaining < 3600 and goal.progress < 0.5:  # < 1 hour left and < 50% done
                return True

        return False

    def _revise_goal(
        self,
        goal: HierarchicalGoal,
        step_results: Optional[Dict[str, Any]],
    ):
        """Revise goal based on progress/issues."""
        old_status = goal.status

        # Create revision record
        revision = GoalRevision(
            revision_id=f"rev_{len(self._revisions) + 1}",
            goal_id=goal.goal_id,
            old_description=goal.description,
            new_description=goal.description,  # Could be modified
            reason="Progress slower than expected",
            timestamp=datetime.now(),
            progress_at_revision=goal.progress,
        )

        self._revisions.append(revision)

        # Update goal status
        goal.status = GoalStatus.REVISED
        goal.updated_at = datetime.now()

        # Extend deadline if possible
        if goal.deadline and goal.progress < 0.5:
            # Extend by 50% of remaining time
            old_deadline = goal.deadline
            time_remaining = (goal.deadline - datetime.now()).total_seconds()
            if time_remaining > 0:
                goal.deadline = datetime.now() + timedelta(seconds=time_remaining * 1.5)

                # Update milestone deadlines
                for milestone in goal.milestones:
                    if milestone.deadline:
                        milestone_time_remaining = (milestone.deadline - datetime.now()).total_seconds()
                        if milestone_time_remaining > 0:
                            milestone.deadline = datetime.now() + timedelta(seconds=milestone_time_remaining * 1.5)

    def _update_parent_progress(self, parent_goal_id: str):
        """Update progress of parent goal based on children."""
        if parent_goal_id not in self._goals:
            return

        parent = self._goals[parent_goal_id]
        child_ids = self._goal_hierarchy.get(parent_goal_id, [])

        if not child_ids:
            return

        # Calculate average progress of children
        child_progress = []
        for child_id in child_ids:
            if child_id in self._goals:
                child_progress.append(self._goals[child_id].progress)

        if child_progress:
            parent.progress = sum(child_progress) / len(child_progress)
            parent.updated_at = datetime.now()

    def get_goal_status(self, goal_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed status of a goal."""
        if goal_id not in self._goals:
            return None

        goal = self._goals[goal_id]

        return {
            "goal_id": goal.goal_id,
            "name": goal.name,
            "description": goal.description,
            "status": goal.status.value,
            "progress": goal.progress,
            "priority": goal.priority,
            "sub_goals": [
                {
                    "id": sg.sub_goal_id,
                    "description": sg.description,
                    "status": sg.status.value,
                    "priority": sg.priority,
                }
                for sg in goal.sub_goals
            ],
            "milestones": [
                {
                    "id": m.milestone_id,
                    "name": m.name,
                    "target": m.target_value,
                    "current": m.current_value,
                    "status": m.status.value,
                }
                for m in goal.milestones
            ],
            "created_at": goal.created_at.isoformat(),
            "updated_at": goal.updated_at.isoformat(),
            "deadline": goal.deadline.isoformat() if goal.deadline else None,
        }

    def get_all_goals(self) -> List[Dict[str, Any]]:
        """Get status of all goals."""
        return [
            self.get_goal_status(goal_id)
            for goal_id in self._goals.keys()
        ]

    def get_next_milestone(self, goal_id: str) -> Optional[Milestone]:
        """Get next milestone to achieve."""
        if goal_id not in self._goals:
            return None

        goal = self._goals[goal_id]

        for milestone in goal.milestones:
            if milestone.status != MilestoneStatus.ACHIEVED:
                return milestone

        return None

    def estimate_completion_time(self, goal_id: str) -> Optional[datetime]:
        """Estimate completion time based on progress rate."""
        if goal_id not in self._goals:
            return None

        history = self._progress_history.get(goal_id, [])
        if len(history) < 2:
            return None

        goal = self._goals[goal_id]

        # Calculate rate of progress
        recent_history = history[-5:]  # Last 5 data points
        if len(recent_history) < 2:
            return None

        time_diff = recent_history[-1][0] - recent_history[0][0]
        progress_diff = recent_history[-1][1] - recent_history[0][1]

        if progress_diff <= 0:
            return None

        # Rate: progress per second
        rate = progress_diff / time_diff

        # Estimate remaining time
        remaining_progress = 1.0 - goal.progress
        estimated_seconds = remaining_progress / rate

        return datetime.now() + timedelta(seconds=estimated_seconds)

    def get_goal_hierarchy(self) -> Dict[str, Any]:
        """Get full goal hierarchy."""
        hierarchy = {}

        for goal_id, goal in self._goals.items():
            if goal.parent_goal_id is None:  # Root goals
                hierarchy[goal_id] = self._build_hierarchy_tree(goal_id)

        return hierarchy

    def _build_hierarchy_tree(self, goal_id: str) -> Dict[str, Any]:
        """Build hierarchy tree for a goal."""
        if goal_id not in self._goals:
            return {}

        goal = self._goals[goal_id]
        tree = {
            "goal_id": goal.goal_id,
            "name": goal.name,
            "status": goal.status.value,
            "progress": goal.progress,
            "children": [],
        }

        # Add children
        for child_id in self._goal_hierarchy.get(goal_id, []):
            tree["children"].append(self._build_hierarchy_tree(child_id))

        return tree
