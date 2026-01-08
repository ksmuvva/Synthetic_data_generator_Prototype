"""
LLM-Enhanced Reasoning Engine.

Uses LLM for intelligent problem analysis, alternative generation,
and dynamic strategy selection.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from synth.agent.models.core import Context, RequestType


@dataclass
class LLMReasoningResult:
    """Result of LLM reasoning process."""
    problem_type: str
    complexity: str
    difficulty_score: float
    requirements: List[str]
    potential_issues: List[str]
    rationale: str
    suggested_approach: Dict[str, Any]
    alternatives: List[Dict[str, Any]]
    confidence: float
    next_action: str
    estimated_duration_seconds: float


class LLMReasoningEngine:
    """
    LLM-powered reasoning engine.

    Uses LLM for:
    - Intelligent problem analysis
    - Dynamic alternative generation
    - Context-aware strategy selection
    - Chain-of-thought reasoning
    """

    def __init__(self, llm_provider=None, enable_thinking: bool = True):
        """
        Initialize LLM reasoning engine.

        Args:
            llm_provider: LLM provider instance
            enable_thinking: Enable extended thinking mode
        """
        self.llm = llm_provider
        self.enable_thinking = enable_thinking

        # Reasoning schema for structured output
        self._reasoning_schema = {
            "type": "object",
            "properties": {
                "problem_type": {
                    "type": "string",
                    "enum": ["data_generation", "data_analysis", "data_validation", "data_export", "multi_step", "unknown"]
                },
                "complexity": {"type": "string", "enum": ["simple", "moderate", "complex", "very_complex"]},
                "difficulty_score": {"type": "number", "minimum": 0, "maximum": 1},
                "requirements": {"type": "array", "items": {"type": "string"}},
                "potential_issues": {"type": "array", "items": {"type": "string"}},
                "rationale": {"type": "string"},
                "suggested_approach": {
                    "type": "object",
                    "properties": {
                        "strategy": {"type": "string"},
                        "reasoning": {"type": "string"},
                        "expected_outcome": {"type": "string"},
                    }
                },
                "alternatives": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "approach": {"type": "string"},
                            "pros": {"type": "array", "items": {"type": "string"}},
                            "cons": {"type": "array", "items": {"type": "string"}},
                            "confidence": {"type": "number"}
                        }
                    }
                },
                "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                "next_action": {"type": "string"},
                "estimated_duration_seconds": {"type": "number"}
            }
        }

    def reason(
        self,
        context: Context,
        similar_situations: Optional[List[Dict]] = None,
    ) -> LLMReasoningResult:
        """
        Perform comprehensive reasoning using LLM.

        Args:
            context: Current execution context
            similar_situations: Optional list of similar past situations

        Returns:
            LLMReasoningResult with comprehensive analysis
        """
        if self.llm is None:
            # Fallback to basic reasoning
            return self._basic_reasoning(context)

        try:
            # Build reasoning prompt
            prompt = self._build_reasoning_prompt(context, similar_situations)

            # Get structured reasoning from LLM
            result = self.llm.generate_structured(
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                schema=self._reasoning_schema,
                temperature=0.7 if self.enable_thinking else 0.5
            )

            return self._parse_reasoning_result(result)

        except Exception as e:
            print(f"Warning: LLM reasoning failed: {e}. Using basic reasoning.")
            return self._basic_reasoning(context)

    def _get_system_prompt(self) -> str:
        """Get system prompt for reasoning."""
        return """You are an AI reasoning engine for a synthetic data generation agent.

**Your Role:**
Analyze user requests and provide intelligent recommendations for:
1. Problem classification and complexity assessment
2. Requirements identification
3. Potential issues and risks
4. Optimal approaches with rationale
5. Alternative solutions with pros/cons
6. Next actions and time estimates

**Problem Types:**
- data_generation: Creating synthetic data
- data_analysis: Analyzing existing data
- data_validation: Checking data quality
- data_export: Exporting data to files
- multi_step: Complex workflows with multiple operations

**Complexity Levels:**
- simple: Single operation, clear requirements
- moderate: 2-3 operations, some ambiguity
- complex: Multiple operations, many constraints
- very_complex: High ambiguity, requires clarification

Provide your analysis as structured JSON matching the provided schema."""

    def _build_reasoning_prompt(
        self,
        context: Context,
        similar_situations: Optional[List[Dict]],
    ) -> str:
        """Build reasoning prompt from context."""
        prompt_parts = []

        # Current request
        prompt_parts.append(f"**Current Request:**\n{context.request.original_text}")

        # Request type
        if context.request.request_type:
            prompt_parts.append(f"\n**Request Type:** {context.request.request_type.value}")

        # Entities extracted
        if context.request.entities:
            prompt_parts.append("\n**Extracted Information:**")
            for key, value in context.request.entities.items():
                if value:
                    prompt_parts.append(f"  - {key}: {value}")

        # Similar past situations (if available)
        if similar_situations:
            prompt_parts.append("\n**Similar Past Situations:**")
            for i, situation in enumerate(similar_situations[:3], 1):
                similarity = situation.get("similarity", 0)
                past_request = situation.get("request", "")[:100]
                prompt_parts.append(f"  {i}. (similarity: {similarity:.2f}) {past_request}...")

        # Environment context
        if context.environment:
            env = context.environment
            prompt_parts.append("\n**Environment:**")
            prompt_parts.append(f"  - Available memory: {env.available_memory_mb:.0f} MB")
            prompt_parts.append(f"  - CPU: {env.available_cpu_percent:.0f}% available")

        prompt_parts.append("\n\nProvide comprehensive reasoning analysis as JSON.")

        return "\n".join(prompt_parts)

    def _parse_reasoning_result(self, result: Dict) -> LLMReasoningResult:
        """Parse LLM reasoning result."""
        suggested = result.get("suggested_approach", {})
        alternatives = result.get("alternatives", [])

        return LLMReasoningResult(
            problem_type=result.get("problem_type", "unknown"),
            complexity=result.get("complexity", "moderate"),
            difficulty_score=result.get("difficulty_score", 0.5),
            requirements=result.get("requirements", []),
            potential_issues=result.get("potential_issues", []),
            rationale=result.get("rationale", ""),
            suggested_approach={
                "strategy": suggested.get("strategy", "default"),
                "reasoning": suggested.get("reasoning", ""),
                "expected_outcome": suggested.get("expected_outcome", ""),
            },
            alternatives=alternatives,
            confidence=result.get("confidence", 0.7),
            next_action=result.get("next_action", "proceed"),
            estimated_duration_seconds=result.get("estimated_duration_seconds", 60.0),
        )

    def _basic_reasoning(self, context: Context) -> LLMReasoningResult:
        """Basic fallback reasoning without LLM."""
        request_type = context.request.request_type

        # Map request type to problem type
        problem_type_map = {
            RequestType.DATA_GENERATION: "data_generation",
            RequestType.DATA_ANALYSIS: "data_analysis",
            RequestType.DATA_VALIDATION: "data_validation",
            RequestType.DATA_EXPORT: "data_export",
            RequestType.MULTI_OBJECTIVE: "multi_step",
        }

        problem_type = problem_type_map.get(request_type, "unknown")

        # Determine complexity based on entities
        entities_count = len(context.request.entities)
        if entities_count <= 2:
            complexity = "simple"
            difficulty = 0.2
        elif entities_count <= 4:
            complexity = "moderate"
            difficulty = 0.5
        else:
            complexity = "complex"
            difficulty = 0.7

        # Build requirements
        requirements = []
        if "count" in context.request.entities:
            requirements.append(f"Generate {context.request.entities['count']} records")
        if "entity_type" in context.request.entities:
            requirements.append(f"Create {context.request.entities['entity_type']} data")

        # Estimate duration
        count = context.request.entities.get("count", 100)
        estimated_duration = max(5, count * 0.1)

        return LLMReasoningResult(
            problem_type=problem_type,
            complexity=complexity,
            difficulty_score=difficulty,
            requirements=requirements,
            potential_issues=[],
            rationale="Basic rule-based reasoning",
            suggested_approach={
                "strategy": "default",
                "reasoning": "Using default approach based on request type",
                "expected_outcome": "Complete the requested operation",
            },
            alternatives=[],
            confidence=0.6,
            next_action="proceed",
            estimated_duration_seconds=estimated_duration,
        )

    def select_strategy(
        self,
        context: Context,
        reasoning_result: LLMReasoningResult,
        available_strategies: List[str],
    ) -> str:
        """
        Select best strategy using LLM reasoning.

        Args:
            context: Current execution context
            reasoning_result: Result from reasoning analysis
            available_strategies: List of available strategies

        Returns:
            Selected strategy name
        """
        # Use LLM-suggested strategy if available and valid
        suggested = reasoning_result.suggested_approach.get("strategy", "default")

        if suggested in available_strategies:
            return suggested

        # Fall back to first available strategy
        if available_strategies:
            return available_strategies[0]

        return "default"

    def adapt_plan(
        self,
        context: Context,
        current_plan: Dict,
        execution_status: Dict,
    ) -> Optional[Dict]:
        """
        Adapt plan based on execution status using LLM reasoning.

        Args:
            context: Current execution context
            current_plan: Current execution plan
            execution_status: Status of plan execution

        Returns:
            Adapted plan or None if no adaptation needed
        """
        if not execution_status.get("needs_adaptation", False):
            return None

        if self.llm is None:
            # Basic adaptation: retry with different parameters
            return self._basic_adaptation(current_plan, execution_status)

        # For now, return None (can be enhanced with LLM-based replanning)
        return None

    def _basic_adaptation(self, current_plan: Dict, execution_status: Dict) -> Dict:
        """Basic plan adaptation without LLM."""
        error = execution_status.get("error", "")

        # Simple adaptation strategies
        if "timeout" in error.lower() or "too long" in error.lower():
            # Reduce batch size
            adapted = current_plan.copy()
            adapted["batch_size"] = adapted.get("batch_size", 100) // 2
            return adapted

        if "memory" in error.lower():
            # Process in smaller chunks
            adapted = current_plan.copy()
            adapted["chunk_size"] = adapted.get("chunk_size", 1000) // 2
            return adapted

        return None
