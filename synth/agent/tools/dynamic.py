"""
Dynamic Tool Creation - Create and compose tools on-demand.

Implements:
- Dynamic tool creation
- Tool composition (combining tools)
- Tool discovery
- Tool optimization
"""

from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
import inspect
import asyncio

from synth.agent.tools.registry import ToolRegistry, Tool, ToolResult, ToolParameter
from synth.agent.models.core import Context


class CompositeTool(Tool):
    """A composite tool that executes multiple tools in sequence."""

    def __init__(self, name: str, description: str, workflow: List[Dict[str, Any]], tool_registry: ToolRegistry):
        """Initialize composite tool."""
        super().__init__()
        self._name = name
        self._description = description
        self._workflow = workflow
        self._tool_registry = tool_registry
        self._parameters = {
            "context": ToolParameter(
                name="context",
                type="object",
                description="Execution context",
                required=False,
            )
        }

    async def execute(self, **kwargs) -> ToolResult:
        """Execute the composite workflow."""
        context = kwargs.get("context")
        results = {}
        last_result = None

        for step in self._workflow:
            tool_name = step.get("tool")
            step_params = step.get("parameters", {})

            # Resolve parameter references
            resolved_params = self._resolve_parameters(step_params, results, kwargs)

            # Execute tool
            tool_result = await self._tool_registry.execute_tool(
                tool_name,
                context=context,
                **resolved_params
            )

            # Store result for next steps
            step_name = step.get("name", tool_name)
            results[step_name] = tool_result.data
            last_result = tool_result

            if not tool_result.success and step.get("required", True):
                return ToolResult(
                    success=False,
                    data=None,
                    error=tool_result.error,
                    message=f"Composite workflow failed at step: {step_name}",
                )

        return ToolResult(
            success=True,
            data=last_result.data if last_result else results,
            message=f"Composite tool {self._name} completed successfully",
        )

    def validate_parameters(self, **kwargs) -> bool:
        """Validate tool parameters."""
        # For composite tools, just check if context is provided when needed
        return True

    def _resolve_parameters(
        self,
        params: Dict[str, Any],
        step_results: Dict[str, Any],
        original_kwargs: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Resolve parameter references."""
        resolved = {}

        for key, value in params.items():
            if isinstance(value, str) and value.startswith("$"):
                # Reference to previous step result
                ref = value[1:]
                if ref in step_results:
                    resolved[key] = step_results[ref]
                elif ref in original_kwargs:
                    resolved[key] = original_kwargs[ref]
            else:
                resolved[key] = value

        return resolved


@dataclass
class ToolComposition:
    """A composition of multiple tools."""
    composition_id: str
    name: str
    description: str
    tools: List[str]  # Tool names
    workflow: List[Dict[str, Any]]  # Workflow steps
    parameters: Dict[str, Any]
    created_at: str


@dataclass
class DiscoveredTool:
    """A dynamically discovered tool."""
    tool_id: str
    name: str
    description: str
    endpoint: Optional[str]
    method: Optional[str]
    parameters: Dict[str, Any]
    confidence: float


class DynamicToolCreator:
    """
    Dynamic tool creation and composition system.

    Capabilities:
    - Create new tools on demand
    - Compose existing tools into workflows
    - Discover external tools/APIs
    - Optimize tool usage
    """

    def __init__(self, tool_registry: ToolRegistry):
        """
        Initialize dynamic tool creator.

        Args:
            tool_registry: Existing tool registry
        """
        self.tool_registry = tool_registry
        self._composed_tools: Dict[str, ToolComposition] = {}
        self._discovered_tools: Dict[str, DiscoveredTool] = {}
        self._tool_usage_stats: Dict[str, Dict[str, Any]] = {}

    def create_tool_from_template(
        self,
        name: str,
        description: str,
        function: Callable,
        parameters: Dict[str, Any],
    ) -> Tool:
        """
        Create a new tool from a function template.

        Args:
            name: Tool name
            description: Tool description
            function: The function to wrap
            parameters: Parameter schema

        Returns:
            Created tool
        """
        # Create tool wrapper
        async def tool_wrapper(**kwargs):
            try:
                result = function(**kwargs)
                if asyncio.iscoroutine(result):
                    result = await result

                return ToolResult(
                    success=True,
                    data=result,
                    message=f"Tool {name} executed successfully",
                )
            except Exception as e:
                return ToolResult(
                    success=False,
                    data=None,
                    error=str(e),
                    message=f"Tool {name} failed: {str(e)}",
                )

        # Create tool
        tool = Tool(
            name=name,
            description=description,
            parameters=parameters,
            function=tool_wrapper,
        )

        return tool

    def compose_tools(
        self,
        composition_name: str,
        description: str,
        tool_names: List[str],
        workflow: List[Dict[str, Any]],
    ) -> ToolComposition:
        """
        Compose multiple tools into a workflow.

        Args:
            composition_name: Name for the composition
            description: Description of what it does
            tool_names: Names of tools to compose
            workflow: Workflow definition

        Returns:
            Tool composition
        """
        composition_id = f"comp_{len(self._composed_tools) + 1}"

        composition = ToolComposition(
            composition_id=composition_id,
            name=composition_name,
            description=description,
            tools=tool_names,
            workflow=workflow,
            parameters={
                "tools": tool_names,
                "workflow": workflow,
            },
            created_at=str(asyncio.get_event_loop().time()),
        )

        self._composed_tools[composition_id] = composition

        # Create composite tool
        self._create_composite_tool(composition)

        return composition

    def _create_composite_tool(self, composition: ToolComposition) -> Tool:
        """Create a tool from composition."""
        # Create composite tool
        tool = CompositeTool(
            name=composition.name,
            description=composition.description,
            workflow=composition.workflow,
            tool_registry=self.tool_registry,
        )

        # Register tool
        self.tool_registry.register_tool(tool)

        return tool

    def discover_common_patterns(self) -> List[Dict[str, Any]]:
        """
        Discover common tool usage patterns.

        Returns:
            List of discovered patterns
        """
        patterns = []

        # Analyze tool usage sequences
        if self._tool_usage_stats:
            # Find common sequences
            sequences = self._find_common_sequences(list(self._tool_usage_stats.keys()))

            for seq in sequences:
                patterns.append({
                    "pattern": seq,
                    "suggestion": f"Consider creating a composite tool for: {' → '.join(seq)}",
                    "frequency": sequences[seq],
                    "confidence": min(sequences[seq] / 10, 1.0),
                })

        return patterns

    def _find_common_sequences(self, tool_names: List[str]) -> Dict[str, int]:
        """Find common sequences of tool usage."""
        sequences = {}

        # This is a simplified version
        # In production, would use more sophisticated pattern mining

        # Look for pairs
        for i in range(len(tool_names) - 1):
            seq = f"{tool_names[i]} → {tool_names[i+1]}"
            sequences[seq] = sequences.get(seq, 0) + 1

        return sequences

    def suggest_tool_improvements(self, tool_name: str) -> List[str]:
        """
        Suggest improvements for a tool.

        Args:
            tool_name: Name of the tool

        Returns:
            List of improvement suggestions
        """
        suggestions = []

        if tool_name in self._tool_usage_stats:
            stats = self._tool_usage_stats[tool_name]

            # Check failure rate
            if stats.get("failure_count", 0) / max(stats.get("usage_count", 1), 1) > 0.3:
                suggestions.append("High failure rate - consider adding input validation")

            # Check average duration
            avg_duration = stats.get("avg_duration", 0)
            if avg_duration > 30:
                suggestions.append("Slow execution - consider optimization or batching")

            # Check parameter patterns
            params = stats.get("parameters", {})
            if params:
                most_common = max(params.items(), key=lambda x: x[1])[0]
                suggestions.append(f"Most common parameter: {most_common} - consider making it default")

        return suggestions

    def create_workflow_automation(
        self,
        workflow_name: str,
        steps: List[Dict[str, Any]],
    ) -> ToolComposition:
        """
        Create an automated workflow from steps.

        Args:
            workflow_name: Name of the workflow
            steps: Workflow steps

        Returns:
            Tool composition
        """
        # Extract tool names from steps
        tool_names = [step.get("tool") for step in steps if step.get("tool")]

        # Create composition
        return self.compose_tools(
            composition_name=workflow_name,
            description=f"Automated workflow: {workflow_name}",
            tool_names=tool_names,
            workflow=steps,
        )

    def optimize_tool_usage(
        self,
        context: Context,
        required_tools: List[str],
    ) -> Dict[str, Any]:
        """
        Optimize tool usage for a given context.

        Args:
            context: Current context
            required_tools: Tools that need to be used

        Returns:
            Optimization recommendations
        """
        recommendations = []

        # Check if tools can be parallelized
        independent_tools = self._find_independent_tools(required_tools)
        if len(independent_tools) > 1:
            recommendations.append({
                "type": "parallelization",
                "description": f"Can run {len(independent_tools)} tools in parallel",
                "tools": independent_tools,
                "potential_speedup": len(independent_tools),
            })

        # Check for batching opportunities
        for tool_name in required_tools:
            if tool_name in self._tool_usage_stats:
                stats = self._tool_usage_stats[tool_name]
                if stats.get("avg_duration", 0) > 10:
                    recommendations.append({
                        "type": "batching",
                        "description": f"Consider batching for {tool_name}",
                        "tool": tool_name,
                        "suggested_batch_size": 100,
                    })

        return {
            "recommendations": recommendations,
            "estimated_time_saved": sum(r.get("potential_speedup", 0) for r in recommendations),
        }

    def _find_independent_tools(self, tool_names: List[str]) -> List[str]:
        """Find tools that can run independently."""
        # Simplified version - assumes tools are independent if they don't share data
        # In production, would analyze tool dependencies

        return tool_names  # Simplified

    def register_external_tool(
        self,
        name: str,
        endpoint: str,
        method: str = "GET",
        parameters: Optional[Dict[str, Any]] = None,
    ) -> DiscoveredTool:
        """
        Register an external tool/API.

        Args:
            name: Tool name
            endpoint: API endpoint
            method: HTTP method
            parameters: Parameter schema

        Returns:
            Discovered tool
        """
        tool_id = f"ext_{len(self._discovered_tools) + 1}"

        discovered = DiscoveredTool(
            tool_id=tool_id,
            name=name,
            description=f"External tool: {name}",
            endpoint=endpoint,
            method=method,
            parameters=parameters or {},
            confidence=0.7,
        )

        self._discovered_tools[tool_id] = discovered

        # Create wrapper tool
        self._create_external_tool_wrapper(discovered)

        return discovered

    def _create_external_tool_wrapper(self, discovered: DiscoveredTool):
        """Create a wrapper for external tool."""

        async def external_wrapper(**kwargs):
            """Call external API."""
            # This would make actual HTTP requests
            # For now, just return a placeholder
            return ToolResult(
                success=True,
                data={"external_result": "placeholder"},
                message=f"External tool {discovered.name} called",
            )

        tool = Tool(
            name=discovered.name,
            description=discovered.description,
            parameters=discovered.parameters,
            function=external_wrapper,
        )

        self.tool_registry.register_tool(tool)

    def get_tool_usage_stats(self) -> Dict[str, Any]:
        """Get statistics on tool usage."""
        return {
            "total_tools": len(self._tool_registry._tools),
            "composed_tools": len(self._composed_tools),
            "discovered_tools": len(self._discovered_tools),
            "usage_stats": self._tool_usage_stats,
        }

    def track_tool_usage(self, tool_name: str, duration: float, success: bool):
        """Track tool usage for optimization."""
        if tool_name not in self._tool_usage_stats:
            self._tool_usage_stats[tool_name] = {
                "usage_count": 0,
                "success_count": 0,
                "failure_count": 0,
                "total_duration": 0.0,
                "avg_duration": 0.0,
                "parameters": {},
            }

        stats = self._tool_usage_stats[tool_name]
        stats["usage_count"] += 1
        stats["total_duration"] += duration
        stats["avg_duration"] = stats["total_duration"] / stats["usage_count"]

        if success:
            stats["success_count"] += 1
        else:
            stats["failure_count"] += 1
