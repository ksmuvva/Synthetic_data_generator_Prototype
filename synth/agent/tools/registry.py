"""
Tool registry for managing and executing tools.
"""

import asyncio
from typing import Dict, List, Optional, Type, Any

from synth.agent.tools.base import Tool, ToolParameter
from synth.agent.models.core import ToolResult


class ToolRegistry:
    """
    Registry for all available tools.

    Manages tool registration, discovery, and execution.
    """

    def __init__(self):
        """Initialize tool registry."""
        self._tools: Dict[str, Tool] = {}
        self._capability_index: Dict[str, List[str]] = {}

    def register_tool(self, tool: Tool) -> None:
        """
        Register a tool.

        Args:
            tool: Tool instance to register
        """
        name = tool.name
        self._tools[name] = tool

        # Index by capabilities
        for capability in tool.get_capabilities():
            if capability not in self._capability_index:
                self._capability_index[capability] = []
            self._capability_index[capability].append(name)

    def register_tool_class(self, tool_class: Type[Tool]) -> Tool:
        """
        Register a tool class (instantiates it).

        Args:
            tool_class: Tool class to register

        Returns:
            Tool instance
        """
        tool = tool_class()
        self.register_tool(tool)
        return tool

    def get_tool(self, name: str) -> Optional[Tool]:
        """
        Get tool by name.

        Args:
            name: Tool name

        Returns:
            Tool if found, None otherwise
        """
        return self._tools.get(name)

    def list_tools(self) -> List[str]:
        """
        List all registered tool names.

        Returns:
            List of tool names
        """
        return list(self._tools.keys())

    def get_tools_info(self) -> Dict[str, Dict[str, Any]]:
        """
        Get information about all tools.

        Returns:
            Dictionary of tool information
        """
        return {
            name: {
                "description": tool.description,
                "parameters": tool.get_parameter_info(),
                "capabilities": tool.get_capabilities(),
                "timeout": tool.timeout,
            }
            for name, tool in self._tools.items()
        }

    def get_tools_by_capability(self, capability: str) -> List[Tool]:
        """
        Get tools that have a specific capability.

        Args:
            capability: Capability string

        Returns:
            List of tools with the capability
        """
        tool_names = self._capability_index.get(capability, [])
        return [self._tools[name] for name in tool_names if name in self._tools]

    async def execute_tool(
        self, tool_name: str, **kwargs
    ) -> ToolResult:
        """
        Execute a tool.

        Args:
            tool_name: Name of tool to execute
            **kwargs: Tool parameters

        Returns:
            ToolResult with execution results
        """
        tool = self.get_tool(tool_name)
        if tool is None:
            return ToolResult(
                tool_name=tool_name,
                success=False,
                error=f"Tool not found: {tool_name}"
            )

        # Validate parameters
        if not tool.validate_parameters(**kwargs):
            return ToolResult(
                tool_name=tool_name,
                success=False,
                error=f"Invalid parameters for tool: {tool_name}"
            )

        # Execute with timeout
        try:
            result = await asyncio.wait_for(
                tool.execute(**kwargs),
                timeout=tool.timeout
            )
            return result
        except asyncio.TimeoutError:
            return ToolResult(
                tool_name=tool_name,
                success=False,
                error=f"Tool execution timeout: {tool_name}"
            )
        except Exception as e:
            return ToolResult(
                tool_name=tool_name,
                success=False,
                error=f"Tool execution error: {str(e)}"
            )

    async def execute_tool_chain(
        self, chain: List[tuple[str, Dict[str, Any]]]
    ) -> List[ToolResult]:
        """
        Execute a chain of tools.

        Args:
            chain: List of (tool_name, parameters) tuples

        Returns:
            List of ToolResults
        """
        results = []
        context = {}

        for tool_name, params in chain:
            # Replace context references in params
            processed_params = self._process_params(params, context)

            result = await self.execute_tool(tool_name, **processed_params)
            results.append(result)

            # Update context with result
            if result.success and result.data is not None:
                context[f"{tool_name}_result"] = result.data

            # Stop on failure
            if not result.success:
                break

        return results

    def _process_params(
        self, params: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process parameters, replacing context references.

        Args:
            params: Original parameters
            context: Context from previous tool executions

        Returns:
            Processed parameters
        """
        processed = {}

        for key, value in params.items():
            if isinstance(value, str) and value.startswith("$"):
                # Context reference
                ref = value[1:]  # Remove $ prefix
                processed[key] = context.get(ref)
            else:
                processed[key] = value

        return processed

    def find_tool_for_task(self, task_description: str) -> Optional[Tool]:
        """
        Find a suitable tool for a task.

        Args:
            task_description: Description of the task

        Returns:
            Suitable tool if found, None otherwise
        """
        # Simple keyword matching (can be improved with embeddings)
        task_lower = task_description.lower()

        for tool_name, tool in self._tools.items():
            # Check description
            if task_lower in tool.description.lower():
                return tool

            # Check capabilities
            for capability in tool.get_capabilities():
                if capability.lower() in task_lower:
                    return tool

        return None
