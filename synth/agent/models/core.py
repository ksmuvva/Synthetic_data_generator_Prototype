"""
Core data models for the AI Agent.

Defines all data structures, enumerations, and types used throughout
the agent system.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional, List, Dict, Union
from enum import Enum
import uuid


class RequestType(str, Enum):
    """Types of user requests."""
    DATA_GENERATION = "data_generation"
    DATA_ANALYSIS = "data_analysis"
    DATA_VALIDATION = "data_validation"
    DATA_EXPORT = "data_export"
    CLARIFICATION = "clarification"
    MULTI_OBJECTIVE = "multi_objective"
    UNKNOWN = "unknown"


class StrategyType(str, Enum):
    """Generation strategies."""
    STATISTICAL = "statistical"
    CONSTRAINED = "constrained"
    COPULA = "copula"
    TIME_SERIES = "time_series"
    HYBRID = "hybrid"


class TaskStatus(str, Enum):
    """Task execution status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ErrorSeverity(str, Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ParsedRequest:
    """Parsed user request."""
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    original_text: str = ""
    intent: str = ""
    request_type: RequestType = RequestType.UNKNOWN
    entities: Dict[str, Any] = field(default_factory=dict)
    constraints: List[Any] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)
    complexity: float = 0.0
    confidence: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "request_id": self.request_id,
            "original_text": self.original_text,
            "intent": self.intent,
            "request_type": self.request_type.value,
            "entities": self.entities,
            "constraints": [str(c) for c in self.constraints],
            "parameters": self.parameters,
            "complexity": self.complexity,
            "confidence": self.confidence,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class EnvironmentContext:
    """System environment context."""
    available_data_sources: List[str] = field(default_factory=list)
    available_memory_mb: float = 0.0
    available_cpu_percent: float = 0.0
    available_disk_gb: float = 0.0
    active_sessions: int = 0
    recent_history: List[Dict] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "available_data_sources": self.available_data_sources,
            "available_memory_mb": self.available_memory_mb,
            "available_cpu_percent": self.available_cpu_percent,
            "available_disk_gb": self.available_disk_gb,
            "active_sessions": self.active_sessions,
            "recent_history": self.recent_history,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class Context:
    """Rich context for decision making."""
    request: ParsedRequest
    environment: EnvironmentContext
    conversation_history: List[Dict] = field(default_factory=list)
    user_preferences: Dict[str, Any] = field(default_factory=dict)
    similar_past_situations: List[Dict] = field(default_factory=list)
    working_variables: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "request": self.request.to_dict(),
            "environment": self.environment.to_dict(),
            "conversation_history": self.conversation_history,
            "user_preferences": self.user_preferences,
            "similar_past_situations": self.similar_past_situations,
            "working_variables": self.working_variables,
        }


@dataclass
class Goal:
    """High-level goal."""
    goal_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    description: str = ""
    priority: int = 0
    success_criteria: List[str] = field(default_factory=list)
    constraints: List[Any] = field(default_factory=list)
    deadline: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "goal_id": self.goal_id,
            "description": self.description,
            "priority": self.priority,
            "success_criteria": self.success_criteria,
            "constraints": [str(c) for c in self.constraints],
            "deadline": self.deadline.isoformat() if self.deadline else None,
        }


@dataclass
class SubGoal(Goal):
    """Sub-goal with dependencies."""
    parent_goal_id: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    estimated_effort: float = 0.0
    progress: float = 0.0


@dataclass
class Step:
    """Execution step."""
    step_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    action: str = ""
    tool: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[Any] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "step_id": self.step_id,
            "action": self.action,
            "tool": self.tool,
            "parameters": self.parameters,
            "dependencies": self.dependencies,
            "status": self.status.value,
            "result": str(self.result) if self.result is not None else None,
            "error": self.error,
            "started_at": self.started_at.isoformat() if self.started_at is not None else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at is not None else None,
        }

    def is_ready(self, completed_steps: List[str]) -> bool:
        """Check if step is ready to execute."""
        return all(dep in completed_steps for dep in self.dependencies)


@dataclass
class Plan:
    """Execution plan."""
    plan_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    goal: Optional[Goal] = None
    sub_goals: List[SubGoal] = field(default_factory=list)
    steps: List[Step] = field(default_factory=list)
    estimated_duration_seconds: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)
    status: TaskStatus = TaskStatus.PENDING

    def get_ready_steps(self) -> List[Step]:
        """Get steps that are ready to execute."""
        completed = [s.step_id for s in self.steps if s.status == TaskStatus.COMPLETED]
        return [s for s in self.steps if s.status == TaskStatus.PENDING and s.is_ready(completed)]

    def get_progress(self) -> float:
        """Get plan progress (0-1)."""
        if not self.steps:
            return 0.0
        completed = sum(1 for s in self.steps if s.status == TaskStatus.COMPLETED)
        return completed / len(self.steps)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "plan_id": self.plan_id,
            "goal": self.goal.to_dict() if self.goal else None,
            "sub_goals": [sg.to_dict() for sg in self.sub_goals],
            "steps": [s.to_dict() for s in self.steps],
            "estimated_duration_seconds": self.estimated_duration_seconds,
            "created_at": self.created_at.isoformat(),
            "status": self.status.value,
            "progress": self.get_progress(),
        }


@dataclass
class Alternative:
    """Solution alternative."""
    alternative_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    description: str = ""
    strategy: StrategyType = StrategyType.STATISTICAL
    tools: List[str] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)
    expected_success_probability: float = 0.0
    expected_duration_seconds: float = 0.0
    resource_requirements: Dict[str, float] = field(default_factory=dict)
    pros: List[str] = field(default_factory=list)
    cons: List[str] = field(default_factory=list)
    risk_score: float = 0.0


@dataclass
class ToolResult:
    """Result from tool execution."""
    tool_name: str = ""
    success: bool = False
    data: Optional[Any] = None
    error: Optional[str] = None
    execution_time_seconds: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "tool_name": self.tool_name,
            "success": self.success,
            "data": str(self.data) if self.data else None,
            "error": self.error,
            "execution_time_seconds": self.execution_time_seconds,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class Error:
    """Error information."""
    error_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    error_type: str = ""
    message: str = ""
    severity: ErrorSeverity = ErrorSeverity.MEDIUM
    stack_trace: str = ""
    context: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "error_id": self.error_id,
            "error_type": self.error_type,
            "message": self.message,
            "severity": self.severity.value,
            "stack_trace": self.stack_trace,
            "context": self.context,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class Diagnosis:
    """Error diagnosis."""
    error: Error
    root_cause: str = ""
    suggested_corrections: List[str] = field(default_factory=list)
    preventable: bool = False
    similar_past_errors: List[Error] = field(default_factory=list)


@dataclass
class Correction:
    """Error correction."""
    correction_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    diagnosis: Optional[Diagnosis] = None
    correction_type: str = ""
    description: str = ""
    steps: List[str] = field(default_factory=list)
    expected_success_probability: float = 0.0


@dataclass
class Suggestion:
    """Proactive suggestion."""
    suggestion_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    suggestion_type: str = ""
    title: str = ""
    description: str = ""
    benefit: str = ""
    effort: str = ""
    priority: int = 0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class Warning:
    """Warning message."""
    warning_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    warning_type: str = ""
    message: str = ""
    severity: ErrorSeverity = ErrorSeverity.LOW
    mitigation: str = ""
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class Response:
    """Agent response to user."""
    response_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    request_id: str = ""
    success: bool = False
    message: str = ""
    data: Optional[Any] = None
    plan: Optional[Plan] = None
    suggestions: List[Suggestion] = field(default_factory=list)
    warnings: List[Warning] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "response_id": self.response_id,
            "request_id": self.request_id,
            "success": self.success,
            "message": self.message,
            "data": str(self.data) if self.data is not None else None,
            "plan": self.plan.to_dict() if self.plan is not None else None,
            "suggestions": [
                {"id": s.suggestion_id, "title": s.title, "description": s.description}
                for s in self.suggestions
            ],
            "warnings": [
                {"id": w.warning_id, "type": w.warning_type, "message": w.message}
                for w in self.warnings
            ],
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class ConversationTurn:
    """Single conversation turn."""
    turn_id: str
    user_message: str
    agent_response: str
    context_state: Dict[str, Any]
    timestamp: datetime

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "turn_id": self.turn_id,
            "user_message": self.user_message,
            "agent_response": self.agent_response,
            "context_state": self.context_state,
            "timestamp": self.timestamp.isoformat(),
        }
