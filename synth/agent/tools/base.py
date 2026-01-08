"""
Tool base class and interfaces.

All tools must inherit from the Tool base class and implement
the required methods.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from synth.agent.models.core import ToolResult


@dataclass
class ToolParameter:
    """Tool parameter definition."""
    name: str
    type: str
    description: str
    required: bool = False
    default: Any = None
    enum: Optional[List[Any]] = None


class Tool(ABC):
    """
    Base class for all tools.

    All tools must inherit from this class and implement
    the required methods.
    """

    def __init__(self):
        self._name = self.__class__.__name__
        self._description = ""
        self._parameters: Dict[str, ToolParameter] = {}
        self._timeout = 300  # seconds

    @property
    def name(self) -> str:
        """Tool name."""
        return self._name

    @property
    def description(self) -> str:
        """Tool description."""
        return self._description

    @property
    def parameters(self) -> Dict[str, ToolParameter]:
        """Tool parameter schema."""
        return self._parameters

    @property
    def timeout(self) -> int:
        """Tool timeout in seconds."""
        return self._timeout

    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """
        Execute the tool.

        Args:
            **kwargs: Tool parameters

        Returns:
            ToolResult with execution results
        """
        pass

    @abstractmethod
    def validate_parameters(self, **kwargs) -> bool:
        """
        Validate tool parameters.

        Args:
            **kwargs: Parameters to validate

        Returns:
            True if valid, False otherwise
        """
        pass

    def get_capabilities(self) -> List[str]:
        """
        Get tool capabilities.

        Returns:
            List of capability strings
        """
        return []

    def estimate_cost(self, **kwargs) -> Dict[str, float]:
        """
        Estimate execution cost.

        Returns:
            Dict with cost estimates (time, memory, etc.)
        """
        return {
            "time_seconds": 1.0,
            "memory_mb": 100.0,
            "cpu_percent": 10.0,
        }

    def get_parameter_info(self) -> Dict[str, Dict[str, Any]]:
        """
        Get parameter information for documentation.

        Returns:
            Dictionary of parameter info
        """
        return {
            name: {
                "type": param.type,
                "description": param.description,
                "required": param.required,
                "default": param.default,
                "enum": param.enum,
            }
            for name, param in self._parameters.items()
        }
