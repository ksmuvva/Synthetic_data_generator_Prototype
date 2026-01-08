"""
Problem Analyzer - Deep analysis of problems.

Implements:
- Problem type analysis
- Complexity assessment
- Potential issue detection
- Difficulty estimation
- Requirement identification
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum

from synth.agent.models.core import (
    Context,
    ParsedRequest,
    RequestType,
)


class ProblemComplexity(str, Enum):
    """Problem complexity level."""
    TRIVIAL = "trivial"
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    VERY_COMPLEX = "very_complex"


class ProblemType(str, Enum):
    """Problem type."""
    DATA_GENERATION = "data_generation"
    DATA_ANALYSIS = "data_analysis"
    DATA_VALIDATION = "data_validation"
    DATA_EXPORT = "data_export"
    MULTI_STEP = "multi_step"
    OPTIMIZATION = "optimization"
    UNKNOWN = "unknown"


@dataclass
class ProblemAnalysis:
    """Result of problem analysis."""
    problem_type: ProblemType
    complexity: ProblemComplexity
    difficulty_score: float  # 0-1
    requirements: List[str]
    potential_issues: List[str]
    estimated_duration_seconds: float
    confidence: float
    rationale: str


class ProblemAnalyzer:
    """
    Deep analysis of problems.

    Analyzes:
    1. Problem type
    2. Complexity level
    3. Potential issues
    4. Difficulty estimation
    5. Requirements identification
    """

    def __init__(self):
        """Initialize problem analyzer."""
        # Complexity thresholds
        self._complexity_weights = {
            "data_size": 0.3,
            "num_steps": 0.3,
            "constraints": 0.2,
            "novelty": 0.2,
        }

    def analyze(
        self,
        context: Context,
    ) -> ProblemAnalysis:
        """
        Analyze a problem.

        Args:
            context: Current execution context

        Returns:
            ProblemAnalysis object
        """
        request = context.request

        # 1. Determine problem type
        problem_type = self._analyze_problem_type(request)

        # 2. Assess complexity
        complexity, complexity_score = self._assess_complexity(request, context)

        # 3. Identify requirements
        requirements = self._identify_requirements(request, context)

        # 4. Detect potential issues
        potential_issues = self._detect_potential_issues(request, context)

        # 5. Estimate difficulty
        difficulty = self._estimate_difficulty(
            complexity_score,
            requirements,
            potential_issues,
        )

        # 6. Estimate duration
        duration = self._estimate_duration(
            problem_type,
            complexity,
            requirements,
        )

        # 7. Generate rationale
        rationale = self._generate_rationale(
            problem_type,
            complexity,
            requirements,
            potential_issues,
        )

        # 8. Calculate confidence
        confidence = self._calculate_confidence(request, context)

        return ProblemAnalysis(
            problem_type=problem_type,
            complexity=complexity,
            difficulty_score=difficulty,
            requirements=requirements,
            potential_issues=potential_issues,
            estimated_duration_seconds=duration,
            confidence=confidence,
            rationale=rationale,
        )

    def _analyze_problem_type(
        self,
        request: ParsedRequest,
    ) -> ProblemType:
        """Analyze problem type."""
        # Check for multi-step indicators
        multi_step_keywords = [
            "and then",
            "after that",
            "followed by",
            "then",
            "next",
        ]

        request_lower = request.original_text.lower()
        is_multi_step = any(keyword in request_lower for keyword in multi_step_keywords)

        if is_multi_step:
            return ProblemType.MULTI_STEP

        # Map request type to problem type
        type_mapping = {
            RequestType.DATA_GENERATION: ProblemType.DATA_GENERATION,
            RequestType.DATA_ANALYSIS: ProblemType.DATA_ANALYSIS,
            RequestType.DATA_VALIDATION: ProblemType.DATA_VALIDATION,
            RequestType.DATA_EXPORT: ProblemType.DATA_EXPORT,
        }

        return type_mapping.get(request.request_type, ProblemType.UNKNOWN)

    def _assess_complexity(
        self,
        request: ParsedRequest,
        context: Context,
    ) -> tuple[ProblemComplexity, float]:
        """
        Assess problem complexity.

        Returns tuple of (complexity_level, score_0_to_1)
        """
        score = 0.0
        factors = []

        # Factor 1: Data size
        data = context.working_variables.get("data")
        if data is not None:
            try:
                data_size = len(data)
                if data_size > 100000:
                    score += 1.0
                    factors.append("large_data")
                elif data_size > 10000:
                    score += 0.7
                    factors.append("medium_data")
                elif data_size > 1000:
                    score += 0.4
                    factors.append("small_data")
            except:
                pass

        # Factor 2: Number of steps (from entities)
        count = request.entities.get("count", 0)
        if count > 10000:
            score += 1.0
            factors.append("high_volume")
        elif count > 1000:
            score += 0.6
            factors.append("medium_volume")
        elif count > 0:
            score += 0.3
            factors.append("low_volume")

        # Factor 3: Constraints
        constraint_count = len(request.constraints)
        if constraint_count > 5:
            score += 0.8
            factors.append("many_constraints")
        elif constraint_count > 2:
            score += 0.5
            factors.append("some_constraints")
        elif constraint_count > 0:
            score += 0.2
            factors.append("few_constraints")

        # Factor 4: Novelty (from complexity score)
        novelty = request.complexity
        score += novelty * 0.5

        # Normalize to 0-1
        max_score = 4.0
        normalized_score = min(score / max_score, 1.0)

        # Determine complexity level
        if normalized_score >= 0.8:
            complexity = ProblemComplexity.VERY_COMPLEX
        elif normalized_score >= 0.6:
            complexity = ProblemComplexity.COMPLEX
        elif normalized_score >= 0.4:
            complexity = ProblemComplexity.MODERATE
        elif normalized_score >= 0.2:
            complexity = ProblemComplexity.SIMPLE
        else:
            complexity = ProblemComplexity.TRIVIAL

        return complexity, normalized_score

    def _identify_requirements(
        self,
        request: ParsedRequest,
        context: Context,
    ) -> List[str]:
        """Identify requirements for solving the problem."""
        requirements = []

        # Based on request type
        if request.request_type == RequestType.DATA_GENERATION:
            requirements.append("Input data for pattern learning")
            requirements.append("Sufficient memory for generation")

            # Check count requirement
            count = request.entities.get("count")
            if count and count > 1000:
                requirements.append("Efficient generation for large volumes")

        elif request.request_type == RequestType.DATA_VALIDATION:
            requirements.append("Original data for comparison")
            requirements.append("Synthetic data for validation")

        elif request.request_type == RequestType.DATA_ANALYSIS:
            requirements.append("Data for analysis")
            requirements.append("Statistical computation capabilities")

        # Based on environment
        if context.environment.available_memory_mb < 1000:
            requirements.append("Memory-efficient processing")

        return requirements

    def _detect_potential_issues(
        self,
        request: ParsedRequest,
        context: Context,
    ) -> List[str]:
        """Detect potential issues."""
        issues = []

        # Check memory constraints
        if context.environment.available_memory_mb < 500:
            issues.append("Limited memory may cause issues")

        # Check for large data sizes
        data = context.working_variables.get("data")
        if data is not None:
            try:
                data_size = len(data)
                if data_size > 50000:
                    issues.append(f"Large dataset ({data_size} records) may be slow")
            except:
                pass

        # Check for high generation counts
        count = request.entities.get("count", 0)
        if count > 50000:
            issues.append(f"Generating {count} records may take significant time")

        # Check for missing requirements
        if request.request_type == RequestType.DATA_VALIDATION:
            if "original" not in request.entities or "synthetic" not in request.entities:
                issues.append("Missing required data for validation")

        return issues

    def _estimate_difficulty(
        self,
        complexity_score: float,
        requirements: List[str],
        potential_issues: List[str],
    ) -> float:
        """Estimate difficulty score (0-1)."""
        difficulty = complexity_score

        # Adjust based on requirements
        requirement_factor = min(len(requirements) * 0.05, 0.2)
        difficulty += requirement_factor

        # Adjust based on issues
        issue_factor = min(len(potential_issues) * 0.1, 0.3)
        difficulty += issue_factor

        return min(difficulty, 1.0)

    def _estimate_duration(
        self,
        problem_type: ProblemType,
        complexity: ProblemComplexity,
        requirements: List[str],
    ) -> float:
        """Estimate duration in seconds."""
        base_duration = {
            ProblemType.DATA_GENERATION: 10.0,
            ProblemType.DATA_ANALYSIS: 5.0,
            ProblemType.DATA_VALIDATION: 8.0,
            ProblemType.DATA_EXPORT: 3.0,
            ProblemType.MULTI_STEP: 30.0,
            ProblemType.OPTIMIZATION: 15.0,
            ProblemType.UNKNOWN: 10.0,
        }

        duration = base_duration.get(problem_type, 10.0)

        # Adjust based on complexity
        complexity_multiplier = {
            ProblemComplexity.TRIVIAL: 0.5,
            ProblemComplexity.SIMPLE: 0.8,
            ProblemComplexity.MODERATE: 1.0,
            ProblemComplexity.COMPLEX: 1.5,
            ProblemComplexity.VERY_COMPLEX: 2.0,
        }

        duration *= complexity_multiplier.get(complexity, 1.0)

        # Adjust based on requirements
        duration *= (1 + len(requirements) * 0.1)

        return duration

    def _generate_rationale(
        self,
        problem_type: ProblemType,
        complexity: ProblemComplexity,
        requirements: List[str],
        potential_issues: List[str],
    ) -> str:
        """Generate rationale for the analysis."""
        parts = []

        parts.append(f"Problem type: {problem_type.value}")
        parts.append(f"Complexity: {complexity.value}")

        if requirements:
            parts.append(f"Requirements: {len(requirements)} identified")

        if potential_issues:
            parts.append(f"Potential issues: {len(potential_issues)} detected")

        return ". ".join(parts)

    def _calculate_confidence(
        self,
        request: ParsedRequest,
        context: Context,
    ) -> float:
        """Calculate confidence in the analysis (0-1)."""
        confidence = 0.5  # Base confidence

        # Higher confidence if request confidence is high
        confidence += request.confidence * 0.3

        # Higher confidence if we have data
        if context.working_variables.get("data") is not None:
            confidence += 0.2

        return min(confidence, 1.0)
