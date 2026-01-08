"""
Proactive Agent - Autonomous initiative without prompts.

Implements:
- Proactive monitoring
- Autonomous goal generation
- Unsolicited suggestions
- Background tasks
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
import asyncio

from synth.agent.models.core import Context, Suggestion


@dataclass
class ProactiveTask:
    """A proactive task."""
    task_id: str
    description: str
    priority: float  # 0-1
    created_at: datetime
    context: Dict[str, Any]
    action: Optional[callable] = None


class ProactiveAgent:
    """
    Proactive autonomous agent.

    Monitors environment and user behavior to:
    - Suggest improvements without being asked
    - Detect problems before users notice
    - Propose optimizations
    - Learn patterns and suggest automations
    """

    def __init__(self):
        """Initialize proactive agent."""
        self._active_tasks: List[ProactiveTask] = []
        self._completed_tasks: List[ProactiveTask] = []
        self._suggestions_queue: List[Suggestion] = []
        self._monitoring_enabled = True

    async def start_monitoring(self, context: Context):
        """Start proactive monitoring in background."""
        if self._monitoring_enabled:
            asyncio.create_task(self._monitor_loop(context))

    async def _monitor_loop(self, context: Context):
        """Background monitoring loop."""
        while self._monitoring_enabled:
            # Check for proactive opportunities
            suggestions = await self._detect_opportunities(context)
            self._suggestions_queue.extend(suggestions)

            # Sleep for a bit
            await asyncio.sleep(10)

    async def _detect_opportunities(self, context: Context) -> List[Suggestion]:
        """Detect proactive opportunities."""
        suggestions = []

        # Check for common patterns
        suggestions.extend(await self._check_repetitive_tasks(context))
        suggestions.extend(await self._check_optimization_opportunities(context))
        suggestions.extend(await self._check_potential_issues(context))

        return suggestions

    async def _check_repetitive_tasks(self, context: Context) -> List[Suggestion]:
        """Check for repetitive tasks that could be automated."""
        suggestions = []

        # Check conversation history for patterns
        history = context.get("conversation_history", [])

        # Count request types
        request_counts = {}
        for turn in history[-20:]:  # Last 20 turns
            request_type = turn.get("request_type", "unknown")
            request_counts[request_type] = request_counts.get(request_type, 0) + 1

        # Suggest automation for repetitive tasks
        for req_type, count in request_counts.items():
            if count >= 3:
                suggestions.append(Suggestion(
                    title=f"Automate {req_type}",
                    description=f"You've performed '{req_type}' {count} times recently. Would you like me to create a workflow for this?",
                    suggestion_type=SuggestionType.AUTOMATION,
                    confidence=min(count / 10, 0.9),
                    action_suggested="create_automation",
                ))

        return suggestions

    async def _check_optimization_opportunities(self, context: Context) -> List[Suggestion]:
        """Check for optimization opportunities."""
        suggestions = []

        # Check data size patterns
        data_size = len(context.working_variables.get("data", []))
        if data_size > 10000:
            suggestions.append(Suggestion(
                title="Optimize for large dataset",
                description=f"Your dataset has {data_size} records. Consider using batched processing for better performance.",
                suggestion_type=SuggestionType.OPTIMIZATION,
                confidence=0.8,
                action_suggested="use_batch_mode",
                parameters={"batch_size": 1000},
            ))

        # Check export patterns
        history = context.get("conversation_history", [])
        export_count = sum(1 for turn in history if "export" in turn.get("request", "").lower())
        if export_count > 0:
            suggestions.append(Suggestion(
                title="Automate exports",
                description=f"You've exported data {export_count} times. Want me to set up automatic export?",
                suggestion_type=SuggestionType.OPTIMIZATION,
                confidence=0.7,
                action_suggested="setup_auto_export",
            ))

        return suggestions

    async def _check_potential_issues(self, context: Context) -> List[Suggestion]:
        """Check for potential issues before they occur."""
        suggestions = []

        # Check memory pressure
        memory_mb = context.environment.available_memory_mb
        if memory_mb < 500:
            suggestions.append(Suggestion(
                title="Low memory warning",
                description=f"Only {memory_mb:.0f}MB memory available. Consider clearing old data or using smaller batches.",
                suggestion_type=SuggestionType.WARNING,
                confidence=0.9,
                action_suggested="free_memory",
            ))

        # Check for missing validations
        last_requests = [turn.get("request", "") for turn in context.get("conversation_history", [])[-5:]]
        has_generation = any("generate" in r.lower() for r in last_requests)
        has_validation = any("validate" in r.lower() for r in last_requests)

        if has_generation and not has_validation:
            suggestions.append(Suggestion(
                title="Consider validation",
                description="You've been generating synthetic data. Would you like me to validate the quality?",
                suggestion_type=SuggestionType.VALIDATION,
                confidence=0.6,
                action_suggested="validate_data",
            ))

        return suggestions

    def get_proactive_suggestions(self, limit: int = 5) -> List[Suggestion]:
        """Get queued proactive suggestions."""
        # Sort by confidence
        self._suggestions_queue.sort(key=lambda s: s.confidence, reverse=True)

        suggestions = self._suggestions_queue[:limit]
        self._suggestions_queue = self._suggestions_queue[limit:]

        return suggestions

    def generate_autonomous_goals(self, context: Context) -> List[Dict[str, Any]]:
        """Generate autonomous goals based on context."""
        goals = []

        # Analyze patterns
        history = context.get("conversation_history", [])

        # Goal 1: Learn from recent interactions
        if len(history) > 5:
            goals.append({
                "goal": "Improve understanding of user preferences",
                "priority": 0.7,
                "actions": ["analyze conversation patterns", "identify preferred strategies"],
            })

        # Goal 2: Optimize performance
        data_sizes = [len(turn.get("data", [])) for turn in history if "data" in turn]
        if data_sizes and max(data_sizes) > 5000:
            goals.append({
                "goal": "Optimize for large-scale processing",
                "priority": 0.8,
                "actions": ["implement batch processing", "add progress monitoring"],
            })

        # Goal 3: Expand capabilities
        unique_operations = set(turn.get("request_type", "") for turn in history)
        if len(unique_operations) < 4:
            goals.append({
                "goal": "Explore additional capabilities",
                "priority": 0.5,
                "actions": ["try new operations", "experiment with parameters"],
            })

        return goals

    async def execute_background_task(self, task: ProactiveTask) -> Dict[str, Any]:
        """Execute a proactive background task."""
        try:
            if task.action:
                result = await task.action()
                return {
                    "success": True,
                    "result": result,
                    "task_id": task.task_id,
                }
            else:
                return {
                    "success": False,
                    "error": "No action defined for task",
                    "task_id": task.task_id,
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "task_id": task.task_id,
            }
