"""
Tool Selection - Select appropriate tools for tasks.

Implements intelligent tool selection considering:
- Task requirements
- Tool capabilities
- Past success rates
- Performance metrics
"""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass

from synth.agent.tools.registry import ToolRegistry
from synth.agent.tools.base import Tool
from synth.agent.models.core import Context


@dataclass
class ToolMatch:
    """Tool match result."""
    tool: Tool
    match_score: float
    rationale: str
    past_success_rate: float
    estimated_cost: Dict[str, float]


class ToolSelector:
    """
    Select appropriate tools for tasks.

    Selects tools by evaluating:
    1. Task-tool capability match
    2. Past success rates
    3. Resource requirements
    4. Performance metrics
    """

    def __init__(self, tool_registry: ToolRegistry):
        """
        Initialize tool selector.

        Args:
            tool_registry: Tool registry to select from
        """
        self.tools = tool_registry

    def select_tool(
        self,
        task_description: str,
        context: Context,
    ) -> tuple[Optional[Tool], Dict[str, Any]]:
        """
        Select best tool for a task.

        Args:
            task_description: Description of the task
            context: Current execution context

        Returns:
            Tuple of (selected_tool, rationale)
        """
        # Find matching tools
        matches = self._find_tools_for_task(task_description, context)

        if not matches:
            return None, {
                "error": "No suitable tool found",
                "task": task_description,
            }

        # Rank tools
        ranked_matches = self._rank_tools(matches, context)

        # Select best tool
        best_match = ranked_matches[0]

        rationale = {
            "selected_tool": best_match.tool.name,
            "match_score": best_match.match_score,
            "rationale": best_match.rationale,
            "past_success_rate": best_match.past_success_rate,
            "estimated_cost": best_match.estimated_cost,
            "alternatives": [
                {
                    "tool": m.tool.name,
                    "score": m.match_score,
                }
                for m in ranked_matches[1:]
            ],
        }

        return best_match.tool, rationale

    def select_tools_for_plan(
        self,
        plan_steps: List[str],
        context: Context,
    ) -> List[tuple[str, Optional[Tool]]]:
        """
        Select tools for multiple plan steps.

        Args:
            plan_steps: List of step descriptions
            context: Current execution context

        Returns:
            List of (step, tool) tuples
        """
        results = []

        for step in plan_steps:
            tool, _ = self.select_tool(step, context)
            results.append((step, tool))

        return results

    def _find_tools_for_task(
        self,
        task_description: str,
        context: Context,
    ) -> List[Tool]:
        """Find tools that can handle a task."""
        matches = []

        # Try finding by capability
        task_lower = task_description.lower()

        # Get all tools
        all_tools = self.tools.list_tools()

        for tool_name in all_tools:
            tool = self.tools.get_tool(tool_name)
            if tool is None:
                continue

            # Check capabilities
            capabilities = tool.get_capabilities()

            # Check if any capability matches the task
            for capability in capabilities:
                if capability.lower() in task_lower:
                    matches.append(tool)
                    break

            # Also check description
            if tool.description and any(
                word in tool.description.lower()
                for word in task_lower.split()
            ):
                if tool not in matches:
                    matches.append(tool)

        return matches

    def _rank_tools(
        self,
        tools: List[Tool],
        context: Context,
    ) -> List[ToolMatch]:
        """
        Rank tools by suitability.

        Returns list of ToolMatch objects sorted by match_score.
        """
        matches = []

        for tool in tools:
            # Calculate match score
            match_score = self._calculate_match_score(tool, context)

            # Get past success rate
            past_success = self._get_past_success_rate(tool, context)

            # Estimate cost
            estimated_cost = self._estimate_tool_cost(tool, context)

            # Generate rationale
            rationale = self._generate_tool_rationale(tool, match_score, past_success)

            matches.append(ToolMatch(
                tool=tool,
                match_score=match_score,
                rationale=rationale,
                past_success_rate=past_success,
                estimated_cost=estimated_cost,
            ))

        # Sort by match score
        matches.sort(key=lambda m: m.match_score, reverse=True)

        return matches

    def _calculate_match_score(
        self,
        tool: Tool,
        context: Context,
    ) -> float:
        """Calculate tool match score (0-1)."""
        score = 0.5  # Base score

        # Bonus for matching capabilities
        capabilities = tool.get_capabilities()
        request_lower = context.request.original_text.lower()

        matching_caps = sum(
            1 for cap in capabilities
            if cap.lower() in request_lower
        )

        if matching_caps > 0:
            score += min(0.3, matching_caps * 0.1)

        # Bonus for past success
        past_success = self._get_past_success_rate(tool, context)
        score += past_success * 0.2

        # Clamp to 0-1
        return max(0.0, min(1.0, score))

    def _get_past_success_rate(
        self,
        tool: Tool,
        context: Context,
    ) -> float:
        """Get past success rate for a tool."""
        # Look in similar past situations
        similar_situations = context.similar_past_situations or []
        success_count = 0
        total_count = 0

        for situation in similar_situations:
            if situation.get("tool") == tool.name:
                total_count += 1
                if situation.get("success", False):
                    success_count += 1

        if total_count == 0:
            return 0.5  # No past experience

        return success_count / total_count

    def _estimate_tool_cost(
        self,
        tool: Tool,
        context: Context,
    ) -> Dict[str, float]:
        """Estimate tool execution cost."""
        # Get basic cost estimation
        # This is a simplified version - in production would analyze parameters

        base_cost = {
            "time_seconds": tool.timeout / 2,  # Rough estimate
            "memory_mb": 100.0,
            "cpu_percent": 50.0,
        }

        # Adjust based on data size if available
        data = context.working_variables.get("data")
        if data is not None:
            try:
                data_size = len(data)
                base_cost["time_seconds"] = max(1.0, data_size * 0.01)
                base_cost["memory_mb"] = max(50.0, data_size * 0.5)
            except:
                pass

        return base_cost

    def _generate_tool_rationale(
        self,
        tool: Tool,
        match_score: float,
        past_success: float,
    ) -> str:
        """Generate rationale for tool selection."""
        parts = []

        parts.append(f"Tool '{tool.name}' selected with match score {match_score:.2f}")

        if tool.description:
            parts.append(f"Description: {tool.description}")

        if past_success > 0.5:
            parts.append(f"Past success rate: {past_success:.1%}")

        return ". ".join(parts)

    def match_tools_to_task(
        self,
        task: str,
        context: Context,
        max_results: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Find and rank tools for a task.

        Args:
            task: Task description
            context: Current context
            max_results: Maximum results to return

        Returns:
            List of tool info dicts
        """
        matches = self._find_tools_for_task(task, context)
        ranked = self._rank_tools(matches, context)

        results = []
        for match in ranked[:max_results]:
            results.append({
                "name": match.tool.name,
                "description": match.tool.description,
                "match_score": match.match_score,
                "capabilities": match.tool.get_capabilities(),
                "estimated_cost": match.estimated_cost,
            })

        return results
