"""
Planning Engine - Create multi-step execution plans.

Implements:
- Plan creation from goals
- Dependency handling
- Checkpoint integration
- Timeline estimation
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field

from synth.agent.models.core import (
    Context,
    Plan,
    Goal,
    SubGoal,
    Step,
    TaskStatus,
)
from synth.agent.planning.goal import GoalDecomposer, GoalComplexity


@dataclass
class PlanOptions:
    """Options for plan creation."""
    include_checkpoints: bool = True
    include_rollback: bool = True
    max_parallel_steps: int = 3
    safety_margin: float = 1.2  # Time estimate multiplier


class PlanningEngine:
    """
    Create multi-step execution plans from goals.

    Transforms high-level goals into concrete execution plans with
    proper dependency handling and validation.
    """

    def __init__(self):
        """Initialize planning engine."""
        self.goal_decomposer = GoalDecomposer()

    def create_plan(
        self,
        context: Context,
        options: Optional[PlanOptions] = None,
    ) -> Plan:
        """
        Create execution plan from context.

        Args:
            context: Current execution context
            options: Optional planning options

        Returns:
            Complete Plan object
        """
        if options is None:
            options = PlanOptions()

        # Create main goal from request
        main_goal = Goal(
            description=context.request.original_text,
            goal_type=context.request.request_type.value,
        )

        # Initialize plan
        plan = Plan()
        plan.goal = main_goal

        # Decompose goal into sub-goals
        decomposition = self.goal_decomposer.decompose_goal(context)

        # Create steps from sub-goals
        steps = self._create_steps_from_sub_goals(
            decomposition["sub_goals"],
            context,
            decomposition["execution_order"],
        )

        # Add checkpoints if requested
        if options.include_checkpoints:
            steps = self._add_checkpoints(steps, context)

        # Build dependency graph
        steps = self._resolve_dependencies(steps)

        # Set steps in plan
        plan.steps = steps

        # Estimate timeline
        duration = decomposition["estimated_duration_seconds"] * options.safety_margin
        plan.estimated_duration_seconds = duration

        return plan

    def _create_steps_from_sub_goals(
        self,
        sub_goals: List[Dict[str, Any]],
        context: Context,
        execution_order: List[str],
    ) -> List[Step]:
        """Create Step objects from sub-goals."""
        steps = []

        # Track execution order
        order_map = {sg_id: i for i, sg_id in enumerate(execution_order)}

        for sg_dict in sub_goals:
            sg_id = sg_dict["id"]
            sg_type = sg_dict["type"]
            sg_deps = sg_dict["dependencies"]

            # Map sub-goal type to tool and action
            tool, action = self._map_goal_to_tool(sg_type, context)

            # Determine parameters
            parameters = self._determine_step_parameters(sg_type, context)

            # Create step
            step = Step(
                step_id=f"step_{sg_id}",
                action=action,
                tool=tool,
                parameters=parameters,
                dependencies=sg_deps,  # Will be resolved later
                estimated_duration=sg_dict["estimated_time"],
                status=TaskStatus.PENDING,
            )

            steps.append(step)

        return steps

    def _map_goal_to_tool(
        self,
        goal_type: str,
        context: Context,
    ) -> tuple[str, str]:
        """Map goal type to tool and action."""
        mapping = {
            "data_generation": ("DataGenerationTool", "generate_data"),
            "data_analysis": ("DataAnalysisTool", "analyze_data"),
            "data_validation": ("DataValidationTool", "validate_data"),
            "data_export": ("DataExportTool", "export_data"),
        }

        return mapping.get(goal_type, (None, goal_type))

    def _determine_step_parameters(
        self,
        goal_type: str,
        context: Context,
    ) -> Dict[str, Any]:
        """Determine parameters for a step."""
        params = {}

        if goal_type == "data_generation":
            params = {
                "data": context.working_variables.get("data"),
                "count": context.request.entities.get("count", 100),
            }
        elif goal_type == "data_analysis":
            params = {
                "data": context.working_variables.get("data"),
            }
        elif goal_type == "data_validation":
            # Need both original and synthetic
            params = {
                "original": context.working_variables.get("data"),
                "synthetic": None,  # Will be resolved from dependencies
            }
        elif goal_type == "data_export":
            params = {
                "data": None,  # Will be resolved from dependencies
                "format": context.request.entities.get("format", "csv"),
                "path": context.request.entities.get("path", "output.csv"),
            }

        return params

    def _add_checkpoints(
        self,
        steps: List[Step],
        context: Context,
    ) -> List[Step]:
        """Add validation checkpoints between steps."""
        with_checkpoints = []

        for i, step in enumerate(steps):
            # Add original step
            with_checkpoints.append(step)

            # Add checkpoint after generation if data is large
            if step.action == "generate_data":
                count = context.request.entities.get("count", 0)
                if count > 1000:
                    checkpoint = Step(
                        step_id=f"checkpoint_post_{step.step_id}",
                        action="checkpoint",
                        tool=None,
                        parameters={
                            "type": "validation",
                            "target": step.step_id,
                        },
                        dependencies=[step.step_id],
                        status=TaskStatus.PENDING,
                    )
                    with_checkpoints.append(checkpoint)

        return with_checkpoints

    def _resolve_dependencies(
        self,
        steps: List[Step],
    ) -> List[Step]:
        """Resolve step dependencies."""
        # Create a mapping of step_id to step
        step_map = {step.step_id: step for step in steps}

        # Resolve dependencies
        for step in steps:
            resolved_deps = []
            for dep_id in step.dependencies:
                if dep_id.startswith("step_"):
                    # Dependency is a step ID
                    resolved_deps.append(dep_id)
                elif dep_id.startswith("sg_"):
                    # Dependency is a sub-goal ID, map to step ID
                    step_id = f"step_{dep_id}"
                    if step_id in step_map:
                        resolved_deps.append(step_id)

            step.dependencies = resolved_deps

        return steps

    def replan_on_failure(
        self,
        original_plan: Plan,
        failed_step: Step,
        error: Exception,
        context: Context,
    ) -> Plan:
        """
        Create a new plan adapting to failure.

        Args:
            original_plan: Original plan that failed
            failed_step: Step that failed
            error: Exception that occurred
            context: Current execution context

        Returns:
            New Plan with adjustments
        """
        # Create new plan
        new_plan = Plan()
        new_plan.goal = original_plan.goal

        # Copy completed steps
        new_steps = []
        for step in original_plan.steps:
            if step.status == TaskStatus.COMPLETED:
                new_steps.append(step)
            elif step.step_id == failed_step.step_id:
                # Stop at failed step
                break
            else:
                # Not reached yet
                break

        # Analyze failure and create alternative
        alternative_step = self._create_alternative_step(
            failed_step,
            error,
            context,
        )

        if alternative_step:
            new_steps.append(alternative_step)

            # Add remaining steps after alternative
            failed_index = next(
                i for i, s in enumerate(original_plan.steps)
                if s.step_id == failed_step.step_id
            )

            for step in original_plan.steps[failed_index + 1:]:
                # Update dependencies to point to alternative
                if failed_step.step_id in step.dependencies:
                    step.dependencies = [
                        alternative_step.step_id if dep == failed_step.step_id else dep
                        for dep in step.dependencies
                    ]
                new_steps.append(step)

        new_plan.steps = new_steps

        # Re-estimate duration
        remaining_duration = sum(
            s.estimated_duration for s in new_steps
            if s.status == TaskStatus.PENDING
        )
        new_plan.estimated_duration_seconds = remaining_duration

        return new_plan

    def _create_alternative_step(
        self,
        failed_step: Step,
        error: Exception,
        context: Context,
    ) -> Optional[Step]:
        """Create alternative step for failed step."""
        error_msg = str(error).lower()

        # Analyze error type
        if "memory" in error_msg or "out of memory" in error_msg:
            # Reduce batch size
            new_params = failed_step.parameters.copy()
            if "count" in new_params:
                new_params["count"] = max(new_params["count"] // 2, 10)

            return Step(
                step_id=f"{failed_step.step_id}_alt_reduced",
                action=failed_step.action,
                tool=failed_step.tool,
                parameters=new_params,
                dependencies=failed_step.dependencies,
                estimated_duration=failed_step.estimated_duration * 0.6,
                status=TaskStatus.PENDING,
            )

        elif "timeout" in error_msg or "timed out" in error_msg:
            # Try simpler approach
            return Step(
                step_id=f"{failed_step.step_id}_alt_timeout",
                action=failed_step.action,
                tool=failed_step.tool,
                parameters=failed_step.parameters,
                dependencies=failed_step.dependencies,
                estimated_duration=failed_step.estimated_duration * 1.5,
                status=TaskStatus.PENDING,
            )

        elif "permission" in error_msg or "access" in error_msg:
            # Try different path
            new_params = failed_step.parameters.copy()
            if "path" in new_params:
                # Try current directory
                new_params["path"] = f"./{new_params['path'].split('/')[-1]}"

            return Step(
                step_id=f"{failed_step.step_id}_alt_path",
                action=failed_step.action,
                tool=failed_step.tool,
                parameters=new_params,
                dependencies=failed_step.dependencies,
                estimated_duration=failed_step.estimated_duration,
                status=TaskStatus.PENDING,
            )

        else:
            # Generic retry
            return Step(
                step_id=f"{failed_step.step_id}_retry",
                action=failed_step.action,
                tool=failed_step.tool,
                parameters=failed_step.parameters,
                dependencies=failed_step.dependencies,
                estimated_duration=failed_step.estimated_duration,
                status=TaskStatus.PENDING,
            )

    def estimate_plan_duration(
        self,
        plan: Plan,
        context: Context,
    ) -> Dict[str, Any]:
        """
        Estimate plan completion duration.

        Args:
            plan: Plan to estimate
            context: Current context

        Returns:
            Duration estimation details
        """
        base_duration = sum(
            s.estimated_duration for s in plan.steps
            if s.status == TaskStatus.PENDING
        )

        # Adjust for resource constraints
        resource_multiplier = 1.0
        if context.environment.available_memory_mb < 1000:
            resource_multiplier += 0.3  # Slower with low memory
        if context.environment.available_cpu_percent < 20:
            resource_multiplier += 0.2  # Slower with low CPU

        estimated_duration = base_duration * resource_multiplier

        # Add buffer for complex plans
        if len(plan.steps) > 5:
            estimated_duration *= 1.2

        return {
            "estimated_seconds": estimated_duration,
            "estimated_minutes": estimated_duration / 60,
            "confidence": 0.7,
            "factors": {
                "base_duration": base_duration,
                "resource_multiplier": resource_multiplier,
                "complexity_buffer": 1.2 if len(plan.steps) > 5 else 1.0,
            },
        }
