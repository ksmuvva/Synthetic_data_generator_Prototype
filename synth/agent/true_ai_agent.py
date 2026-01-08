"""
True AI Agent - Main orchestrator.

Transforms SYNTH from a tool to a True AI Agent with:
- Autonomous decision making
- Persistent memory
- Multi-step planning
- Tool use
- Self-correction
- Proactive behavior
"""

import time
from typing import Optional, Dict, Any, List
from datetime import datetime

from synth.agent.models.core import (
    RequestType,
    ParsedRequest,
    Context,
    EnvironmentContext,
    Goal,
    SubGoal,
    Step,
    Plan,
    TaskStatus,
    Response,
    Suggestion,
    Warning,
    Error,
    ErrorSeverity,
)
from synth.agent.memory.layer import MemoryLayer
from synth.agent.tools.registry import ToolRegistry
from synth.agent.tools.core_tools import (
    DataGenerationTool,
    DataValidationTool,
    DataAnalysisTool,
    DataExportTool,
)


class TrueAIAgent:
    """
    True AI Agent orchestrator.

    Coordinates all components to deliver intelligent behavior:
    - Understands goals and context
    - Observes environment
    - Recalls relevant memory
    - Plans multi-step solutions
    - Makes autonomous decisions
    - Uses tools effectively
    - Learns from outcomes
    - Suggests improvements
    """

    def __init__(
        self,
        storage_path: str = ".agent_memory",
        llm_provider: Optional[str] = None,
    ):
        """
        Initialize True AI Agent.

        Args:
            storage_path: Path for persistent memory storage
            llm_provider: LLM provider to use (optional)
        """
        # Initialize memory
        self.memory = MemoryLayer(storage_path=storage_path)

        # Initialize tools
        self.tools = ToolRegistry()
        self._register_tools()

        # Agent state
        self._initialized = False
        self._request_count = 0
        self._start_time = datetime.now()

    def _register_tools(self):
        """Register all available tools."""
        self.tools.register_tool(DataGenerationTool())
        self.tools.register_tool(DataValidationTool())
        self.tools.register_tool(DataAnalysisTool())
        self.tools.register_tool(DataExportTool())

    def initialize(self):
        """Initialize the agent."""
        if self._initialized:
            return

        # Load any saved state
        self._initialized = True

    async def process_request(
        self,
        request: str,
        user_id: Optional[str] = None,
        context_params: Optional[Dict[str, Any]] = None,
    ) -> Response:
        """
        Process a user request through the full AI agent pipeline.

        Pipeline:
        1. Perceive (understand request + environment)
        2. Recall (relevant memory)
        3. Think (reason, plan, decide)
        4. Act (execute tools)
        5. Learn (update memory)
        6. Respond (format response)

        Args:
            request: User request string
            user_id: Optional user identifier
            context_params: Optional additional context

        Returns:
            Response with results
        """
        start_time = time.time()
        self._request_count += 1

        request_id = f"req_{self._request_count}_{int(start_time)}"

        try:
            # Step 1: Perceive - Understand request and environment
            parsed_request = await self._parse_request(request)
            environment = await self._observe_environment()

            # Build full context
            context = await self._build_context(
                parsed_request, environment, user_id, context_params
            )

            # Step 2: Recall - Find relevant information from memory
            similar_situations = self.memory.find_similar_situations(request)
            user_preferences = self.memory.get_preferences(user_id) if user_id else None
            context.similar_past_situations = similar_situations
            context.user_preferences = user_preferences or {}

            # Step 3: Think - Reason, plan, and decide
            plan = await self._create_plan(context)

            # Step 4: Act - Execute the plan
            result = await self._execute_plan(plan, context)

            # Step 5: Learn - Store outcomes in memory
            await self._learn_from_outcome(parsed_request, result, context)

            # Step 6: Generate proactive suggestions
            suggestions = await self._generate_suggestions(context, result)
            warnings = await self._generate_warnings(context, plan)

            # Format response
            response = Response(
                request_id=request_id,
                success=result.get("success", False),
                message=result.get("message", ""),
                data=result.get("data"),
                plan=plan,
                suggestions=suggestions,
                warnings=warnings,
                metadata={
                    "processing_time_seconds": time.time() - start_time,
                    "steps_executed": len(plan.steps),
                    "tools_used": [s.tool for s in plan.steps if s.tool],
                },
            )

            # Record interaction
            self.memory.record_interaction(
                parsed_request,
                response.to_dict(),
                {"context": context.to_dict()},
            )

            return response

        except Exception as e:
            # Return error response with full traceback
            import traceback
            tb = traceback.format_exc()
            return Response(
                request_id=request_id,
                success=False,
                message=f"Error processing request: {str(e)}\nTraceback:\n{tb}",
                metadata={
                    "processing_time_seconds": time.time() - start_time,
                    "error": str(e),
                },
            )

    async def _parse_request(self, request: str) -> ParsedRequest:
        """
        Parse user request.

        Extracts:
        - Intent
        - Request type
        - Entities
        - Constraints
        - Parameters
        """
        # Simple parsing (can be enhanced with LLM)
        request_lower = request.lower()

        # Detect request type
        request_type = RequestType.UNKNOWN
        if any(word in request_lower for word in ["generate", "create", "synthetic"]):
            request_type = RequestType.DATA_GENERATION
        elif any(word in request_lower for word in ["analyze", "examine", "study"]):
            request_type = RequestType.DATA_ANALYSIS
        elif any(word in request_lower for word in ["validate", "check", "verify"]):
            request_type = RequestType.DATA_VALIDATION
        elif any(word in request_lower for word in ["export", "save", "write"]):
            request_type = RequestType.DATA_EXPORT

        # Extract basic entities
        entities = {}
        if "csv" in request_lower:
            entities["format"] = "csv"
        if "json" in request_lower:
            entities["format"] = "json"

        # Extract count if mentioned
        import re
        count_match = re.search(r'(\d+)\s+(records|rows|samples)', request)
        if count_match:
            entities["count"] = int(count_match.group(1))

        return ParsedRequest(
            original_text=request,
            intent="Generate synthetic data" if request_type == RequestType.DATA_GENERATION else request,
            request_type=request_type,
            entities=entities,
            complexity=0.5,  # Can be improved with actual analysis
            confidence=0.8,
        )

    async def _observe_environment(self) -> EnvironmentContext:
        """Observe system environment."""
        import psutil
        import os

        # Get disk usage with error handling for Windows path issues
        try:
            disk_free = psutil.disk_usage(os.path.abspath('.')).free / (1024**3)
        except (OSError, SystemError):
            # Fallback to current drive root on Windows
            try:
                disk_free = psutil.disk_usage('C:').free / (1024**3)
            except:
                disk_free = 0.0

        return EnvironmentContext(
            available_memory_mb=psutil.virtual_memory().available / 1024 / 1024,
            available_cpu_percent=psutil.cpu_percent(),
            available_disk_gb=disk_free,
            active_sessions=1,  # Simplified
        )

    async def _build_context(
        self,
        parsed_request: ParsedRequest,
        environment: EnvironmentContext,
        user_id: Optional[str],
        context_params: Optional[Dict[str, Any]],
    ) -> Context:
        """Build full context for decision making."""
        # Get conversation history
        conversation_history = self.memory.get_conversation_history(5)

        return Context(
            request=parsed_request,
            environment=environment,
            conversation_history=conversation_history,
            working_variables=context_params or {},
        )

    async def _create_plan(self, context: Context) -> Plan:
        """
        Create execution plan.

        Analyzes the request and creates a step-by-step plan.
        """
        plan = Plan()
        plan.goal = Goal(description=context.request.original_text)

        request_type = context.request.request_type

        if request_type == RequestType.DATA_GENERATION:
            # Data generation plan
            # Get data from working variables (where context_params are stored)
            data = context.working_variables.get("data")
            plan.steps = [
                Step(
                    action="generate_data",
                    tool="DataGenerationTool",
                    parameters={
                        "data": data,
                        "count": context.request.entities.get("count", 100),
                    },
                    dependencies=[],
                ),
            ]
        elif request_type == RequestType.DATA_ANALYSIS:
            # Data analysis plan
            data = context.working_variables.get("data")
            plan.steps = [
                Step(
                    action="analyze_data",
                    tool="DataAnalysisTool",
                    parameters={"data": data},
                    dependencies=[],
                ),
            ]
        elif request_type == RequestType.DATA_VALIDATION:
            # Data validation plan
            plan.steps = [
                Step(
                    action="validate_data",
                    tool="DataValidationTool",
                    parameters={
                        "original": context.request.entities.get("original"),
                        "synthetic": context.request.entities.get("synthetic"),
                    },
                    dependencies=[],
                ),
            ]
        elif request_type == RequestType.DATA_EXPORT:
            # Data export plan
            plan.steps = [
                Step(
                    action="export_data",
                    tool="DataExportTool",
                    parameters={
                        "data": context.request.entities.get("data"),
                        "format": context.request.entities.get("format", "csv"),
                        "path": context.request.entities.get("path"),
                    },
                    dependencies=[],
                ),
            ]

        # Estimate duration
        plan.estimated_duration_seconds = sum(
            self.tools.get_tool(step.tool).estimate_cost(**step.parameters).get("time_seconds", 1.0)
            for step in plan.steps
            if step.tool and self.tools.get_tool(step.tool)
        )

        return plan

    async def _execute_plan(self, plan: Plan, context: Context) -> Dict[str, Any]:
        """Execute the plan."""
        results = {
            "success": True,
            "message": "",
            "data": None,
            "steps_completed": 0,
            "steps_failed": 0,
        }

        completed_steps = []

        for step in plan.steps:
            # Check if step is ready
            if not step.is_ready(completed_steps):
                continue

            step.status = TaskStatus.IN_PROGRESS
            step.started_at = datetime.now()

            # Execute the tool
            if step.tool:
                try:
                    # Process parameters (resolve references)
                    params = self._process_step_parameters(step, context)

                    tool_result = await self.tools.execute_tool(step.tool, **params)

                    if tool_result.success:
                        step.status = TaskStatus.COMPLETED
                        step.result = tool_result.data
                        results["steps_completed"] += 1

                        # Store result in context for dependent steps
                        context.working_variables[f"{step.step_id}_result"] = tool_result.data
                    else:
                        step.status = TaskStatus.FAILED
                        step.error = tool_result.error
                        results["steps_failed"] += 1
                        results["success"] = False
                        results["message"] = f"Step failed: {step.error}"
                        break
                except Exception as e:
                    step.status = TaskStatus.FAILED
                    step.error = str(e)
                    results["steps_failed"] += 1
                    results["success"] = False
                    results["message"] = f"Step exception: {str(e)}"
                    break
            else:
                # Non-tool step (just mark complete)
                step.status = TaskStatus.COMPLETED
                results["steps_completed"] += 1

            step.completed_at = datetime.now()
            completed_steps.append(step.step_id)

        # Get final result
        if plan.steps:
            last_step = plan.steps[-1]
            if last_step.result is not None:
                results["data"] = last_step.result
                results["message"] = f"Completed {results['steps_completed']} steps successfully"

        plan.status = TaskStatus.COMPLETED if results["success"] else TaskStatus.FAILED

        return results

    def _process_step_parameters(self, step: Step, context: Context) -> Dict[str, Any]:
        """Process step parameters, resolving any references."""
        params = step.parameters.copy()

        # Resolve context references
        for key, value in params.items():
            if isinstance(value, str) and value.startswith("$"):
                ref = value[1:]
                # Check working variables first
                if ref in context.working_variables:
                    params[key] = context.working_variables[ref]
                # Then check request entities
                elif ref in context.request.entities:
                    params[key] = context.request.entities[ref]

        return params

    async def _learn_from_outcome(
        self, request: ParsedRequest, result: Dict[str, Any], context: Context
    ):
        """Learn from the outcome."""
        # Record strategy effectiveness
        if result.get("success"):
            strategy = context.request.request_type.value
            metrics = {
                "duration": result.get("metadata", {}).get("processing_time_seconds", 0),
                "quality": 1.0,  # Can be improved
            }
            self.memory.learn_strategy_outcome(strategy, context, True, metrics)

    async def _generate_suggestions(
        self, context: Context, result: Dict[str, Any]
    ) -> List[Suggestion]:
        """Generate proactive suggestions."""
        suggestions = []

        # Suggest validation if data was generated
        if context.request.request_type == RequestType.DATA_GENERATION:
            suggestions.append(Suggestion(
                suggestion_type="validation",
                title="Validate Generated Data",
                description="Would you like me to validate the quality of the generated data?",
                benefit="Ensures data quality matches requirements",
                effort="Low",
                priority=1,
            ))

        # Suggest export if data was generated
        if context.request.request_type == RequestType.DATA_GENERATION:
            suggestions.append(Suggestion(
                suggestion_type="export",
                title="Export Data",
                description="Would you like me to export this data to a file?",
                benefit="Save results for later use",
                effort="Low",
                priority=2,
            ))

        return suggestions

    async def _generate_warnings(self, context: Context, plan: Plan) -> List[Warning]:
        """Generate proactive warnings."""
        warnings = []

        # Warn about memory usage if generating large datasets
        if context.request.request_type == RequestType.DATA_GENERATION:
            count = context.request.entities.get("count", 100)
            if count > 10000:
                warnings.append(Warning(
                    warning_type="resource",
                    message=f"Generating {count} records may require significant memory",
                    severity=ErrorSeverity.MEDIUM,
                    mitigation="Consider generating in smaller batches",
                ))

        return warnings

    def get_status(self) -> Dict[str, Any]:
        """Get agent status."""
        uptime = (datetime.now() - self._start_time).total_seconds()

        return {
            "initialized": self._initialized,
            "requests_processed": self._request_count,
            "uptime_seconds": uptime,
            "tools_registered": len(self.tools.list_tools()),
            "memory_stats": self.memory.get_stats(),
        }

    def shutdown(self):
        """Shutdown the agent."""
        # Cleanup resources
        pass
