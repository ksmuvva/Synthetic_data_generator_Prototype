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
from synth.agent.state import IntentType
from synth.agent.memory.layer import MemoryLayer
from synth.agent.tools.registry import ToolRegistry
from synth.agent.tools.core_tools import (
    DataGenerationTool,
    DataValidationTool,
    DataAnalysisTool,
    DataExportTool,
)
from synth.agent.reasoning.engine import ReasoningEngine, ReasoningResult

# LLM Integration imports
try:
    from synth.agent.llm import get_llm_provider, LLMProvider
    from synth.agent.llm.parser import LLMIntentParser, LLMReasoningEngine as LLMReasoning
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False

# Cognitive Layer imports
from synth.agent.cognitive.layer import CognitiveLayer
from synth.agent.cognitive.strategy import StrategySelector, StrategyFit
from synth.agent.cognitive.tool_selector import ToolSelector
from synth.agent.cognitive.decision import DecisionEngine
from synth.agent.cognitive.optimizer import ParameterOptimizer
from synth.agent.cognitive.progress import ProgressTracker

# Planning imports
from synth.agent.planning.goal import GoalDecomposer
from synth.agent.planning.planner import PlanningEngine, PlanOptions
from synth.agent.planning.adaptive import AdaptivePlanner


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
        enable_llm: bool = True,
    ):
        """
        Initialize True AI Agent.

        Args:
            storage_path: Path for persistent memory storage
            llm_provider: LLM provider to use (optional: "claude", "openai", "gemini")
            enable_llm: Whether to enable LLM integration (default: True)
        """
        # Initialize memory
        self.memory = MemoryLayer(storage_path=storage_path)

        # Initialize LLM components - TRUE AI AGENT CAPABILITY
        self.llm_enabled = enable_llm and LLM_AVAILABLE
        self.llm_provider_name = llm_provider or "claude"
        self.llm = None
        self.llm_parser = None
        self.llm_reasoning = None

        if self.llm_enabled:
            try:
                self.llm = get_llm_provider(provider=self.llm_provider_name)
                self.llm_parser = LLMIntentParser(llm=self.llm)
                self.llm_reasoning = LLMReasoning(llm=self.llm)
            except Exception as e:
                # LLM initialization failed, fall back to rule-based
                print(f"Warning: LLM initialization failed: {e}. Using rule-based parsing.")
                self.llm_enabled = False

        # Initialize tools
        self.tools = ToolRegistry()
        self._register_tools()

        # Initialize reasoning engine - TRUE AI AGENT CAPABILITY
        self.reasoning = ReasoningEngine()

        # Initialize cognitive layer - TRUE AI AGENT CAPABILITY
        # Note: Pass tool_registry to components that need it
        self.cognitive = CognitiveLayer(tool_registry=self.tools)
        self.strategy_selector = StrategySelector()
        self.tool_selector = ToolSelector(tool_registry=self.tools)
        self.decision_engine = DecisionEngine(tool_registry=self.tools)
        self.parameter_optimizer = ParameterOptimizer()
        self.progress_tracker = ProgressTracker()

        # Initialize planning engine - TRUE AI AGENT CAPABILITY
        self.goal_decomposer = GoalDecomposer()
        self.planning_engine = PlanningEngine()
        self.adaptive_planner = AdaptivePlanner()

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

            # Step 3: Think - Reason, plan, and decide using COGNITIVE LAYER
            # 3a. Perform comprehensive reasoning
            reasoning_result = self.reasoning.reason_comprehensive(context)

            # 3b. Create plan informed by reasoning - TRUE AI AGENT
            plan = await self._create_plan_with_reasoning(context, reasoning_result)

            # Step 4: Act - Execute the plan
            result = await self._execute_plan(plan, context)

            # Step 5: Learn - Store outcomes in memory
            await self._learn_from_outcome(parsed_request, result, context)

            # Record parameter outcome for learning
            if result.get("success"):
                used_params = context.request.entities.copy()
                self.parameter_optimizer.record_outcome(
                    context,
                    used_params,
                    True,
                    {"quality": 0.9, "duration": result.get("duration", 0)}
                )

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
                    "reasoning": self._format_reasoning_for_response(reasoning_result),
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

        Uses LLM-powered parsing when available, with fallback to rule-based.
        """
        # Try LLM-powered parsing first - TRUE AI AGENT CAPABILITY
        if self.llm_enabled and self.llm_parser:
            try:
                # Build context for LLM parser
                context = {
                    "previous_messages": [],  # Could add conversation history here
                    "current_state": {},      # Could add current state tracking here
                }

                # Use LLM intent parser
                llm_intent = self.llm_parser.parse(request, context=context)

                # Convert LLM intent to ParsedRequest
                return self._convert_llm_intent_to_request(llm_intent, request)

            except Exception as e:
                # LLM parsing failed, fall back to rule-based
                print(f"Warning: LLM parsing failed: {e}. Using rule-based fallback.")

        # Fallback to rule-based parsing
        return await self._parse_request_rule_based(request)

    def _convert_llm_intent_to_request(
        self,
        llm_intent: Any,
        original_request: str
    ) -> ParsedRequest:
        """
        Convert LLM parsed intent to ParsedRequest.

        Args:
            llm_intent: ParsedIntent from LLMIntentParser
            original_request: Original user request string

        Returns:
            ParsedRequest with extracted information
        """
        # Map LLM intent types to RequestType
        intent_to_request_type = {
            IntentType.GENERATE: RequestType.DATA_GENERATION,
            IntentType.LEARN: RequestType.DATA_ANALYSIS,
            IntentType.VALIDATE: RequestType.DATA_VALIDATION,
            IntentType.INSPECT: RequestType.DATA_ANALYSIS,
            IntentType.UPLOAD: RequestType.UNKNOWN,
            IntentType.USE_TEMPLATE: RequestType.DATA_GENERATION,
            IntentType.EXIT: RequestType.UNKNOWN,
            IntentType.HELP: RequestType.UNKNOWN,
            IntentType.UNKNOWN: RequestType.UNKNOWN,
        }

        request_type = intent_to_request_type.get(
            llm_intent.intent_type,
            RequestType.UNKNOWN
        )

        # Build entities from LLM intent
        entities = {}

        if llm_intent.entity_type:
            entities["entity_type"] = llm_intent.entity_type

        if llm_intent.record_count:
            entities["count"] = llm_intent.record_count

        if llm_intent.output_format:
            entities["format"] = llm_intent.output_format

        # Extract field names if present
        if llm_intent.fields:
            entities["fields"] = [f.name for f in llm_intent.fields]

        # Store constraints if present
        if llm_intent.constraints:
            entities["constraints"] = [
                {
                    "field": c.field,
                    "type": c.type,
                    "value": c.value
                }
                for c in llm_intent.constraints
            ]

        return ParsedRequest(
            original_text=original_request,
            intent=llm_intent.raw_input,
            request_type=request_type,
            entities=entities,
            constraints=[],  # Already stored in entities
            complexity=0.5 if llm_intent.metadata else 0.3,
            confidence=llm_intent.confidence,
        )

    async def _parse_request_rule_based(self, request: str) -> ParsedRequest:
        """
        Rule-based request parsing (fallback when LLM unavailable).

        Extracts:
        - Intent
        - Request type
        - Entities
        - Constraints
        - Parameters
        """
        # Simple parsing (can be enhanced with LLM)
        request_lower = request.lower()

        # Detect ALL request types present (for multi-objective requests)
        detected_types = []
        if any(word in request_lower for word in ["generate", "create", "synthetic"]):
            detected_types.append(RequestType.DATA_GENERATION)
        if any(word in request_lower for word in ["analyze", "examine", "study"]):
            detected_types.append(RequestType.DATA_ANALYSIS)
        if any(word in request_lower for word in ["validate", "check", "verify"]):
            detected_types.append(RequestType.DATA_VALIDATION)
        if any(word in request_lower for word in ["export", "save", "write"]):
            detected_types.append(RequestType.DATA_EXPORT)

        # Determine request type - MULTI_OBJECTIVE if multiple detected
        if len(detected_types) > 1:
            request_type = RequestType.MULTI_OBJECTIVE
        elif len(detected_types) == 1:
            request_type = detected_types[0]
        else:
            request_type = RequestType.UNKNOWN

        # Store detected types for multi-objective planning
        entities = {"detected_types": detected_types}

        if "csv" in request_lower:
            entities["format"] = "csv"
        if "json" in request_lower:
            entities["format"] = "json"

        # Extract count if mentioned
        import re
        count_match = re.search(r'(\d+)\s+(records|rows|samples)', request)
        if count_match:
            entities["count"] = int(count_match.group(1))

        # Extract path if mentioned
        path_match = re.search(r'(?:to|as)\s+["\']?([^"\']+\.(?:csv|json|parquet))["\']?', request_lower)
        if path_match:
            entities["path"] = path_match.group(1)

        return ParsedRequest(
            original_text=request,
            intent="Generate synthetic data" if request_type == RequestType.DATA_GENERATION else request,
            request_type=request_type,
            entities=entities,
            constraints=[],
            complexity=0.5 if request_type == RequestType.MULTI_OBJECTIVE else 0.3,
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
        detected_types = context.request.entities.get("detected_types", [])

        # Handle multi-objective requests - TRUE AI AGENT BEHAVIOR
        if request_type == RequestType.MULTI_OBJECTIVE:
            steps = []
            dependencies = []
            generation_step_id = None  # Track the data generation step for export

            # Create steps in logical order
            for req_type in detected_types:
                step = None
                if req_type == RequestType.DATA_GENERATION:
                    step = Step(
                        action="generate_data",
                        tool="DataGenerationTool",
                        parameters={
                            "data": context.working_variables.get("data"),
                            "count": context.request.entities.get("count", 100),
                        },
                        dependencies=dependencies.copy(),
                    )
                    generation_step_id = step.step_id  # Save for export step
                    last_step_id = step.step_id
                    steps.append(step)
                    dependencies = [last_step_id]  # Next steps depend on generation

                elif req_type == RequestType.DATA_ANALYSIS:
                    # Analyze can run in parallel with generation if data provided
                    # Or depend on previous step
                    step = Step(
                        action="analyze_data",
                        tool="DataAnalysisTool",
                        parameters={"data": context.working_variables.get("data")},
                        dependencies=dependencies.copy(),
                    )
                    last_step_id = step.step_id
                    steps.append(step)
                    # Keep dependencies for next step

                elif req_type == RequestType.DATA_VALIDATION:
                    # Validation needs both original and synthetic data
                    # Use generation_step_id to get the actual generated data
                    step = Step(
                        action="validate_data",
                        tool="DataValidationTool",
                        parameters={
                            "original": context.working_variables.get("data"),
                            "synthetic": f"${generation_step_id}_result" if generation_step_id else None,
                        },
                        dependencies=[generation_step_id] if generation_step_id else [],
                    )
                    last_step_id = step.step_id
                    steps.append(step)
                    # Don't update dependencies - export should still use generation_step_id

                elif req_type == RequestType.DATA_EXPORT:
                    # Export the GENERATED data, not the validation results
                    step = Step(
                        action="export_data",
                        tool="DataExportTool",
                        parameters={
                            "data": f"${generation_step_id}_result" if generation_step_id else None,
                            "format": context.request.entities.get("format", "csv"),
                            "path": context.request.entities.get("path", "output.csv"),
                        },
                        dependencies=[generation_step_id] if generation_step_id else [],
                    )
                    steps.append(step)

            plan.steps = steps

        elif request_type == RequestType.DATA_GENERATION:
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

    async def _create_plan_with_reasoning(
        self, context: Context, reasoning: ReasoningResult
    ) -> Plan:
        """
        Create a plan informed by reasoning results.

        Args:
            context: Current execution context
            reasoning: Results from reasoning engine

        Returns:
            Optimized execution plan
        """
        # First, get the base plan
        plan = await self._create_plan(context)

        # Enhance plan with reasoning insights
        # 1. Add reasoning metadata to the plan
        plan.reasoning = {
            "problem_type": reasoning.problem_analysis.problem_type.value,
            "complexity": reasoning.problem_analysis.complexity.value,
            "confidence": reasoning.confidence,
            "recommendation": reasoning.recommendation,
            "alternatives_considered": len(reasoning.alternatives),
        }

        # 2. If consistency issues found, add warnings to steps
        if reasoning.consistency_checks:
            for issue in reasoning.consistency_checks:
                plan.warnings.append({
                    "type": issue["type"],
                    "message": issue["description"],
                    "details": issue.get("details", []),
                })

        # 3. Use recommended strategy if available
        if reasoning.recommendation.get("suggested_approach"):
            suggested = reasoning.recommendation["suggested_approach"]
            strategy = suggested.get("strategy")

            # Update generation steps with recommended strategy
            for step in plan.steps:
                if step.action == "generate_data" and strategy:
                    step.parameters["strategy"] = strategy

        # 4. Adjust duration estimate based on reasoning
        if reasoning.problem_analysis.estimated_duration_seconds > 0:
            # Use reasoning estimate if it's more pessimistic (safer)
            plan.estimated_duration_seconds = max(
                plan.estimated_duration_seconds,
                reasoning.problem_analysis.estimated_duration_seconds,
            )

        return plan

    def _format_reasoning_for_response(self, reasoning: ReasoningResult) -> Dict[str, Any]:
        """
        Format reasoning results for response metadata.

        Args:
            reasoning: Reasoning result

        Returns:
            Formatted reasoning dict
        """
        return {
            "problem_analysis": {
                "type": reasoning.problem_analysis.problem_type.value,
                "complexity": reasoning.problem_analysis.complexity.value,
                "difficulty_score": reasoning.problem_analysis.difficulty_score,
                "requirements": reasoning.problem_analysis.requirements,
                "potential_issues": reasoning.problem_analysis.potential_issues,
                "rationale": reasoning.problem_analysis.rationale,
            },
            "alternatives_considered": len(reasoning.alternatives),
            "best_alternative": reasoning.evaluation.get("best", {}).get("alternative") if reasoning.evaluation else None,
            "consistency_checks": {
                "issues_found": len(reasoning.consistency_checks),
                "issues": reasoning.consistency_checks,
            },
            "recommendation": reasoning.recommendation,
            "confidence": reasoning.confidence,
        }

    async def _create_plan_with_cognitive_layer(
        self,
        context: Context,
        reasoning: ReasoningResult,
        strategy_fit: StrategyFit
    ) -> Plan:
        """
        Create a plan using the full cognitive layer.

        This replaces the hardcoded plan creation with intelligent planning
        that uses goal decomposition, strategy selection, and parameter optimization.

        Args:
            context: Current execution context
            reasoning: Results from reasoning engine
            strategy_fit: Selected strategy from StrategySelector

        Returns:
            Optimized execution plan
        """
        # Step 1: Analyze goal complexity using GoalDecomposer - TRUE AI AGENT
        complexity_assessment = self.goal_decomposer.analyze_goal_complexity(context)

        # Step 2: Decompose goal into sub-goals if complex - TRUE AI AGENT
        if complexity_assessment.overall_complexity > 0.6:
            decomposition_result = self.goal_decomposer.decompose_goal(context)

            # Store sub-goals in context for execution
            context.working_variables["sub_goals"] = [
                {"description": sg.description, "priority": sg.priority}
                for sg in decomposition_result["sub_goals"]
            ]
        else:
            decomposition_result = None

        # Step 3: Create plan using PlanningEngine - TRUE AI AGENT
        plan_options = PlanOptions(
            enable_checkpoints=True,
            include_dependencies=True,
            estimate_durations=True
        )

        plan = self.planning_engine.create_plan(context, plan_options)

        # Step 4: Make plan adaptive - TRUE AI AGENT
        plan = self.adaptive_planner.create_adaptive_plan(context)

        # Step 5: Enhance plan with cognitive layer insights
        # Add reasoning metadata
        plan.metadata["reasoning"] = {
            "problem_type": reasoning.problem_analysis.problem_type.value,
            "complexity": reasoning.problem_analysis.complexity.value,
            "confidence": reasoning.confidence,
            "recommendation": reasoning.recommendation,
            "alternatives_considered": len(reasoning.alternatives),
        }

        # Add strategy metadata
        plan.metadata["strategy"] = {
            "selected": strategy_fit.strategy_type.value,
            "fit_score": strategy_fit.fit_score,
            "rationale": strategy_fit.rationale,
        }

        # Add complexity assessment
        if decomposition_result:
            plan.metadata["complexity_assessment"] = {
                "complexity": complexity_assessment.overall_complexity,
                "factors": complexity_assessment.complexity_factors,
                "sub_goal_count": len(decomposition_result["sub_goals"]),
            }

        # Add consistency warnings from reasoning
        if reasoning.consistency_checks:
            for issue in reasoning.consistency_checks:
                plan.warnings.append({
                    "type": issue["type"],
                    "message": issue["description"],
                    "details": issue.get("details", []),
                })

        # Apply recommended strategy from reasoning
        if reasoning.recommendation.get("suggested_approach"):
            suggested = reasoning.recommendation["suggested_approach"]
            strategy = suggested.get("strategy")

            # Update generation steps with recommended strategy
            for step in plan.steps:
                if step.action == "generate_data" and strategy:
                    step.parameters["strategy"] = strategy

        # Adjust duration estimate based on reasoning and safety margin
        if reasoning.problem_analysis.estimated_duration_seconds > 0:
            # Use reasoning estimate with adaptive planner's safety margin
            plan.estimated_duration_seconds = max(
                plan.estimated_duration_seconds,
                reasoning.problem_analysis.estimated_duration_seconds *
                plan.metadata.get("replan_threshold", 1.5)
            )

        return plan

    def _format_reasoning_for_response(self, reasoning: ReasoningResult) -> Dict[str, Any]:
        """
        Format reasoning results for response metadata.

        Args:
            reasoning: Reasoning result

        Returns:
            Formatted reasoning dict
        """
        return {
            "problem_analysis": {
                "type": reasoning.problem_analysis.problem_type.value,
                "complexity": reasoning.problem_analysis.complexity.value,
                "difficulty_score": reasoning.problem_analysis.difficulty_score,
                "requirements": reasoning.problem_analysis.requirements,
                "potential_issues": reasoning.problem_analysis.potential_issues,
                "rationale": reasoning.problem_analysis.rationale,
            },
            "alternatives_considered": len(reasoning.alternatives),
            "best_alternative": reasoning.evaluation.get("best", {}).get("alternative") if reasoning.evaluation else None,
            "consistency_checks": {
                "issues_found": len(reasoning.consistency_checks),
                "issues": reasoning.consistency_checks,
            },
            "recommendation": reasoning.recommendation,
            "confidence": reasoning.confidence,
        }

    async def _execute_plan_adaptive(self, plan: Plan, context: Context) -> Dict[str, Any]:
        """
        Execute the plan with adaptive replanning capabilities.

        This replaces the basic execution with intelligent execution that:
        - Monitors progress using ProgressTracker - TRUE AI AGENT
        - Replans on failures using AdaptivePlanner - TRUE AI AGENT
        - Recovers from errors automatically
        - Preserves completed work

        Args:
            plan: Execution plan
            context: Current execution context

        Returns:
            Execution results
        """
        results = {
            "success": True,
            "message": "",
            "data": None,
            "steps_completed": 0,
            "steps_failed": 0,
        }

        # Initialize progress tracking - TRUE AI AGENT
        self.progress_tracker.start_plan(plan)

        completed_steps = []
        replan_count = 0
        max_replans = 3  # Prevent infinite replanning loops

        for step in plan.steps:
            # Check if step is ready
            if not step.is_ready(completed_steps):
                continue

            # Update progress - TRUE AI AGENT
            self.progress_tracker.start_step(step)

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
                        step.completed_at = datetime.now()
                        results["steps_completed"] += 1

                        # Update progress - TRUE AI AGENT
                        self.progress_tracker.complete_step(step, True)

                        # Store result in context for dependent steps
                        context.working_variables[f"{step.step_id}_result"] = tool_result.data
                        completed_steps.append(step.step_id)

                    else:
                        # Step failed - attempt adaptive replanning - TRUE AI AGENT
                        step.status = TaskStatus.FAILED
                        step.error = tool_result.error
                        step.completed_at = datetime.now()
                        results["steps_failed"] += 1

                        # Update progress - TRUE AI AGENT
                        self.progress_tracker.complete_step(step, False, str(tool_result.error))

                        # Check if we should replan
                        if replan_count < max_replans and self.adaptive_planner.should_replan(plan, context):
                            try:
                                # Trigger replanning - TRUE AI AGENT
                                plan = self.adaptive_planner.trigger_replan(
                                    plan, step, Exception(tool_result.error), context
                                )
                                replan_count += 1

                                # Restart execution with new plan (preserving completed steps)
                                # Continue from the next step after current position
                                continue

                            except Exception as replan_error:
                                # Replanning failed, abort
                                results["success"] = False
                                results["message"] = f"Replanning failed: {str(replan_error)}"
                                break
                        else:
                            # Cannot recover
                            results["success"] = False
                            results["message"] = f"Step failed: {step.error}"
                            break

                except Exception as e:
                    # Step exception - attempt adaptive replanning - TRUE AI AGENT
                    step.status = TaskStatus.FAILED
                    step.error = str(e)
                    step.completed_at = datetime.now()
                    results["steps_failed"] += 1

                    # Update progress - TRUE AI AGENT
                    self.progress_tracker.complete_step(step, False, str(e))

                    # Check if we should replan
                    if replan_count < max_replans and self.adaptive_planner.should_replan(plan, context):
                        try:
                            # Trigger replanning - TRUE AI AGENT
                            plan = self.adaptive_planner.trigger_replan(plan, step, e, context)
                            replan_count += 1

                            # Restart execution with new plan
                            continue

                        except Exception as replan_error:
                            # Replanning failed, abort
                            results["success"] = False
                            results["message"] = f"Replanning failed: {str(replan_error)}"
                            break
                    else:
                        # Cannot recover
                        results["success"] = False
                        results["message"] = f"Step exception: {str(e)}"
                        break
            else:
                # Non-tool step (just mark complete)
                step.status = TaskStatus.COMPLETED
                step.completed_at = datetime.now()
                results["steps_completed"] += 1

                # Update progress - TRUE AI AGENT
                self.progress_tracker.complete_step(step, True)
                completed_steps.append(step.step_id)

        # Get final result
        if plan.steps:
            last_step = plan.steps[-1]
            if last_step.result is not None:
                results["data"] = last_step.result
                results["message"] = f"Completed {results['steps_completed']} steps successfully"
                if replan_count > 0:
                    results["message"] += f" (after {replan_count} adaptive replans)"

        # Update final plan status - TRUE AI AGENT
        plan.status = TaskStatus.COMPLETED if results["success"] else TaskStatus.FAILED

        # Get final progress snapshot - TRUE AI AGENT
        final_progress = self.progress_tracker.get_plan_progress(plan)
        results["progress"] = {
            "steps_completed": final_progress.steps_completed,
            "steps_failed": final_progress.steps_failed,
            "replan_count": replan_count,
        }

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

    async def _execute_plan(self, plan: Plan, context: Context) -> Dict[str, Any]:
        """Execute the plan - simple version without adaptive features."""
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
                        step.completed_at = datetime.now()
                        results["steps_completed"] += 1

                        # Store result in context for dependent steps
                        context.working_variables[f"{step.step_id}_result"] = tool_result.data
                        completed_steps.append(step.step_id)

                    else:
                        step.status = TaskStatus.FAILED
                        step.error = tool_result.error
                        step.completed_at = datetime.now()
                        results["steps_failed"] += 1
                        results["success"] = False
                        results["message"] = f"Step failed: {step.error}"
                        break

                except Exception as e:
                    step.status = TaskStatus.FAILED
                    step.error = str(e)
                    step.completed_at = datetime.now()
                    results["steps_failed"] += 1
                    results["success"] = False
                    results["message"] = f"Step exception: {str(e)}"
                    break
            else:
                # Non-tool step (just mark complete)
                step.status = TaskStatus.COMPLETED
                step.completed_at = datetime.now()
                results["steps_completed"] += 1
                completed_steps.append(step.step_id)

        # Get final result
        if plan.steps:
            last_step = plan.steps[-1]
            if last_step.result is not None:
                results["data"] = last_step.result
                results["message"] = f"Completed {results['steps_completed']} steps successfully"

        plan.status = TaskStatus.COMPLETED if results["success"] else TaskStatus.FAILED

        return results

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
