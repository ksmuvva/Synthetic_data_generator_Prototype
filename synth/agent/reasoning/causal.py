"""
Causal Reasoning - Explanation and inference.

Implements:
- Causal relationship modeling
- Counterfactual reasoning ("what if" scenarios)
- Explanation generation
- Root cause analysis
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import time

from synth.agent.models.core import Context, Plan, Step
from synth.agent.reasoning.analyzer import ProblemAnalysis


class CausalRelationType(str, Enum):
    """Types of causal relations."""
    DIRECT = "direct"
    INDIRECT = "indirect"
    CONTRIBUTING = "contributing"
    NECESSARY = "necessary"
    SUFFICIENT = "sufficient"


@dataclass
class CausalRelation:
    """A causal relationship."""
    cause: str
    effect: str
    relation_type: CausalRelationType
    strength: float  # 0-1
    confidence: float  # 0-1


@dataclass
class CounterfactualScenario:
    """A counterfactual (what-if) scenario."""
    description: str
    changed_factor: str
    predicted_outcome: str
    confidence: float
    reasoning: str


@dataclass
class Explanation:
    """Explanation of reasoning."""
    what: str  # What happened
    why: str  # Why it happened
    how: str  # How it happened
    factors: List[str]  # Contributing factors
    confidence: float
    evidence: List[Dict[str, Any]]


class CausalReasoningEngine:
    """
    Causal reasoning and explanation engine.

    Provides:
    - Causal relationship inference
    - Counterfactual analysis
    - Human-readable explanations
    - Root cause identification
    """

    def __init__(self):
        """Initialize causal reasoning engine."""
        self._causal_links: List[CausalRelation] = []
        self._past_outcomes: List[Dict[str, Any]] = []

    def analyze_outcome(
        self,
        context: Context,
        plan: Plan,
        result: Dict[str, Any],
    ) -> Explanation:
        """
        Analyze outcome and generate explanation.

        Args:
            context: Execution context
            plan: The plan that was executed
            result: The result of execution

        Returns:
            Explanation object
        """
        # Determine what happened
        what = self._describe_outcome(plan, result)

        # Determine why it happened
        why = self._identify_causes(context, plan, result)

        # Determine how it happened
        how = self._describe_mechanism(plan, result)

        # Identify contributing factors
        factors = self._identify_contributing_factors(context, plan, result)

        # Calculate confidence
        confidence = self._calculate_explanation_confidence(context, result)

        # Gather evidence
        evidence = self._gather_evidence(context, plan, result)

        return Explanation(
            what=what,
            why=why,
            how=how,
            factors=factors,
            confidence=confidence,
            evidence=evidence,
        )

    def _describe_outcome(self, plan: Plan, result: Dict[str, Any]) -> str:
        """Describe what happened."""
        success = result.get("success", False)
        steps_completed = result.get("steps_completed", 0)
        steps_total = len(plan.steps)

        if success:
            return f"Successfully completed {steps_completed} of {steps_total} planned steps"
        else:
            failed_step = result.get("message", "Unknown error")
            return f"Failed after {steps_completed} steps: {failed_step}"

    def _identify_causes(
        self,
        context: Context,
        plan: Plan,
        result: Dict[str, Any],
    ) -> str:
        """Identify causes of the outcome."""
        if result.get("success"):
            # Identify success factors
            success_factors = []

            # Check data quality
            data = context.working_variables.get("data")
            if data is not None:
                try:
                    data_size = len(data)
                    if data_size > 0:
                        success_factors.append(f"had {data_size} records of input data")
                except:
                    pass

            # Check resource availability
            memory_mb = context.environment.available_memory_mb
            if memory_mb > 500:
                success_factors.append("sufficient memory available")

            # Check strategy
            strategy = context.request.entities.get("strategy", "default")
            success_factors.append(f"used '{strategy}' strategy")

            if success_factors:
                return "Success due to: " + ", ".join(success_factors)
            else:
                return "Completed successfully"
        else:
            # Identify failure causes
            error_msg = result.get("message", "")
            error_lower = error_msg.lower()

            if "timeout" in error_lower:
                return "Operation timed out - likely due to large data size or slow processing"
            elif "memory" in error_lower:
                return "Insufficient memory - dataset or operation too large for available resources"
            elif "invalid" in error_lower or "value" in error_lower:
                return "Invalid parameters - input values don't meet requirements"
            elif "permission" in error_lower or "access" in error_lower:
                return "Permission/access denied - insufficient privileges for the operation"
            else:
                return f"Failed due to: {error_msg}"

    def _describe_mechanism(self, plan: Plan, result: Dict[str, Any]) -> str:
        """Describe how the outcome occurred."""
        steps_desc = []
        for step in plan.steps:
            status = "completed" if step.status.value == "completed" else "failed"
            steps_desc.append(f"{step.action} ({status})")

        if steps_desc:
            return " → ".join(steps_desc)
        else:
            return "No steps were executed"

    def _identify_contributing_factors(
        self,
        context: Context,
        plan: Plan,
        result: Dict[str, Any],
    ) -> List[str]:
        """Identify factors that contributed to the outcome."""
        factors = []

        # Data factors
        data = context.working_variables.get("data")
        if data is not None:
            try:
                data_size = len(data)
                factors.append(f"Data size: {data_size} records")

                # Check data quality
                if hasattr(data, "describe"):
                    factors.append("Data had statistical summary available")
            except:
                factors.append("Data present but size unknown")

        # Resource factors
        memory_mb = context.environment.available_memory_mb
        if memory_mb < 1000:
            factors.append(f"Low memory: {memory_mb:.0f}MB available")

        # Parameter factors
        count = context.request.entities.get("count")
        if count:
            factors.append(f"Requested count: {count}")

        # Strategy factors
        strategy = context.request.entities.get("strategy")
        if strategy:
            factors.append(f"Strategy: {strategy}")

        return factors

    def _calculate_explanation_confidence(
        self,
        context: Context,
        result: Dict[str, Any],
    ) -> float:
        """Calculate confidence in the explanation."""
        base_confidence = 0.7

        # Higher confidence for clear outcomes
        if result.get("success"):
            base_confidence += 0.2
        else:
            error_msg = result.get("message", "")
            if any(keyword in error_msg.lower() for keyword in ["timeout", "memory", "invalid"]):
                base_confidence += 0.1

        return min(base_confidence, 1.0)

    def _gather_evidence(
        self,
        context: Context,
        plan: Plan,
        result: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Gather evidence supporting the explanation."""
        evidence = []

        # Step outcomes
        for step in plan.steps:
            if step.status.value == "completed":
                evidence.append({
                    "type": "completed_step",
                    "step": step.action,
                    "tool": step.tool,
                    "duration": (
                        step.completed_at.timestamp() - step.started_at.timestamp()
                        if step.completed_at and step.started_at
                        else None
                    ),
                })
            elif step.status.value == "failed":
                evidence.append({
                    "type": "failed_step",
                    "step": step.action,
                    "error": step.error,
                })

        # Resource usage
        evidence.append({
            "type": "resource_usage",
            "memory_mb": context.environment.available_memory_mb,
        })

        return evidence

    def generate_counterfactuals(
        self,
        context: Context,
        plan: Plan,
        result: Dict[str, Any],
        num_scenarios: int = 3,
    ) -> List[CounterfactualScenario]:
        """
        Generate counterfactual (what-if) scenarios.

        Args:
            context: Execution context
            plan: The plan that was executed
            result: The actual result
            num_scenarios: Number of scenarios to generate

        Returns:
            List of counterfactual scenarios
        """
        scenarios = []

        # Scenario 1: What if we used different parameters?
        count = context.request.entities.get("count")
        if count and count > 100:
            scenarios.append(CounterfactualScenario(
                description=f"What if we requested fewer records?",
                changed_factor=f"count from {count} to {count // 2}",
                predicted_outcome=f"Would likely complete faster with {count // 2} records",
                confidence=0.8,
                reasoning="Smaller data size reduces processing time and memory usage",
            ))

        # Scenario 2: What if we used a different strategy?
        strategy = context.request.entities.get("strategy")
        if strategy and strategy != "copula":
            scenarios.append(CounterfactualScenario(
                description="What if we used copula-based generation?",
                changed_factor=f"strategy from {strategy} to copula",
                predicted_outcome="Would preserve correlations better but be slower",
                confidence=0.7,
                reasoning="Copula strategy better captures dependencies but has higher computational cost",
            ))

        # Scenario 3: What if we had more memory?
        memory_mb = context.environment.available_memory_mb
        if memory_mb < 1000:
            scenarios.append(CounterfactualScenario(
                description="What if we had more memory available?",
                changed_factor=f"memory from {memory_mb}MB to 2000MB",
                predicted_outcome="Could handle larger datasets and more complex operations",
                confidence=0.9,
                reasoning="More memory allows processing larger datasets without batching",
            ))

        # Scenario 4: What if we did validation first?
        steps = [s.action for s in plan.steps]
        if "validate_data" in steps:
            validate_idx = steps.index("validate_data")
            if validate_idx > 0:
                scenarios.append(CounterfactualScenario(
                    description="What if we validated data before generation?",
                    changed_factor="move validation to first step",
                    predicted_outcome="Would catch issues earlier but require original data",
                    confidence=0.75,
                    reasoning="Early validation catches problems before spending time on generation",
                ))

        return scenarios[:num_scenarios]

    def infer_causal_relations(
        self,
        context: Context,
        plan: Plan,
        result: Dict[str, Any],
    ) -> List[CausalRelation]:
        """
        Infer causal relationships from execution.

        Args:
            context: Execution context
            plan: The plan that was executed
            result: The result of execution

        Returns:
            List of inferred causal relations
        """
        relations = []
        success = result.get("success", False)

        if success:
            # Success causes
            data = context.working_variables.get("data")
            if data is not None:
                try:
                    relations.append(CausalRelation(
                        cause="having_input_data",
                        effect="successful_generation",
                        relation_type=CausalRelationType.NECESSARY,
                        strength=0.9,
                        confidence=0.95,
                    ))
                except:
                    pass

            # Strategy effectiveness
            strategy = context.request.entities.get("strategy")
            if strategy:
                relations.append(CausalRelation(
                    cause=f"using_{strategy}_strategy",
                    effect="successful_completion",
                    relation_type=CausalRelationType.CONTRIBUTING,
                    strength=0.6,
                    confidence=0.7,
                ))

        else:
            # Failure causes
            error_msg = result.get("message", "").lower()

            if "timeout" in error_msg:
                relations.append(CausalRelation(
                    cause="large_data_size",
                    effect="operation_timeout",
                    relation_type=CausalRelationType.DIRECT,
                    strength=0.8,
                    confidence=0.85,
                ))

            if "memory" in error_msg:
                relations.append(CausalRelation(
                    cause="insufficient_memory",
                    effect="operation_failure",
                    relation_type=CausalRelationType.DIRECT,
                    strength=0.9,
                    confidence=0.9,
                ))

        return relations

    def explain_reasoning(
        self,
        problem_analysis: ProblemAnalysis,
        reasoning_result: Dict[str, Any],
    ) -> str:
        """
        Explain the reasoning process in human-readable form.

        Args:
            problem_analysis: Problem analysis results
            reasoning_result: Full reasoning results

        Returns:
            Human-readable explanation
        """
        explanation_parts = []

        # Explain problem understanding
        explanation_parts.append(
            f"I analyzed this as a {problem_analysis.complexity.value} "
            f"{problem_analysis.problem_type.value} problem."
        )

        # Explain requirements
        if problem_analysis.requirements:
            explanation_parts.append(
                f"Identified {len(problem_analysis.requirements)} requirements "
                f"that need to be satisfied."
            )

        # Explain alternatives considered
        alternatives = reasoning_result.get("alternatives_considered", 0)
        if alternatives > 0:
            explanation_parts.append(
                f"Considered {alternatives} different approaches "
                f"and selected the best one based on quality and efficiency."
            )

        # Explain confidence
        confidence = reasoning_result.get("confidence", 0)
        if confidence > 0.8:
            explanation_parts.append(
                f"I'm {confidence:.0%} confident in this analysis "
                f"because the requirements are clear."
            )
        elif confidence > 0.5:
            explanation_parts.append(
                f"I'm {confidence:.0%} confident in this analysis "
                f"but there are some ambiguities."
            )

        return " ".join(explanation_parts)

    def get_root_cause_analysis(
        self,
        error: Exception,
        context: Context,
    ) -> Dict[str, Any]:
        """
        Perform root cause analysis for an error.

        Args:
            error: The error that occurred
            context: Execution context

        Returns:
            Root cause analysis
        """
        error_msg = str(error).lower()
        root_causes = []

        # Identify root causes
        if "timeout" in error_msg:
            root_causes.append({
                "cause": "operation_timeout",
                "root_cause": "operation took longer than allowed time",
                "contributing_factors": [
                    "large data size",
                    "slow processing",
                    "insufficient timeout setting",
                ],
                "suggested_fixes": [
                    "reduce data size",
                    "optimize processing",
                    "increase timeout",
                ],
            })

        if "memory" in error_msg:
            root_causes.append({
                "cause": "out_of_memory",
                "root_cause": "insufficient memory for operation",
                "contributing_factors": [
                    "large dataset",
                    "other processes using memory",
                    "memory leak",
                ],
                "suggested_fixes": [
                    "reduce batch size",
                    "close other applications",
                    "use streaming processing",
                ],
            })

        if "invalid" in error_msg or "value" in error_msg:
            root_causes.append({
                "cause": "invalid_parameter",
                "root_cause": "parameter value doesn't meet requirements",
                "contributing_factors": [
                    "wrong data type",
                    "out of range value",
                    "missing required field",
                ],
                "suggested_fixes": [
                    "validate input parameters",
                    "check data type requirements",
                    "review parameter constraints",
                ],
            })

        return {
            "error": str(error),
            "root_causes": root_causes,
            "most_likely_cause": root_causes[0] if root_causes else None,
            "confidence": 0.8 if root_causes else 0.3,
        }
