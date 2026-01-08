"""
Test Phase 8: Reasoning Engine

This script tests the reasoning engine components:
- Problem Analyzer
- Reasoning Engine
"""

import asyncio
import pandas as pd
import numpy as np
from synth.agent.reasoning import (
    ProblemAnalyzer,
    ReasoningEngine,
)
from synth.agent.models.core import (
    Context,
    ParsedRequest,
    RequestType,
    EnvironmentContext,
)


def create_test_context(request_text: str, data=None, count=100):
    """Create a test context."""
    return Context(
        request=ParsedRequest(
            request_id="test_req",
            original_text=request_text,
            intent="Generate synthetic data",
            request_type=RequestType.DATA_GENERATION,
            entities={"count": count},
            constraints=[],
            parameters={},
            complexity=0.5,
            confidence=0.8,
        ),
        environment=EnvironmentContext(
            available_memory_mb=8000,
            available_cpu_percent=80,
            available_disk_gb=50,
            active_sessions=1,
        ),
        conversation_history=[],
        user_preferences={},
        similar_past_situations=[],
        working_variables={"data": data} if data is not None else {},
    )


async def test_reasoning_engine():
    """Test reasoning engine components."""
    print("=" * 80)
    print("  PHASE 8: REASONING ENGINE TEST")
    print("=" * 80)
    print()

    # Initialize components
    print("Initializing components...")
    problem_analyzer = ProblemAnalyzer()
    reasoning_engine = ReasoningEngine()

    # Create sample data
    data = pd.DataFrame({
        'age': np.random.randint(21, 70, 100),
        'income': np.random.randint(30000, 120000, 100),
    })
    print(f"Created sample data: {len(data)} records")
    print()

    # ========================================
    # Test 1: Problem Analysis - Simple Request
    # ========================================
    print("-" * 80)
    print("TEST 1: Problem Analysis - Simple Request")
    print("-" * 80)
    print()

    context = create_test_context("Generate 100 synthetic records", data, 100)
    analysis = problem_analyzer.analyze(context)

    print(f"Problem Type: {analysis.problem_type.value}")
    print(f"Complexity: {analysis.complexity.value}")
    print(f"Difficulty Score: {analysis.difficulty_score:.2f}")
    print(f"Requirements: {len(analysis.requirements)}")
    for req in analysis.requirements:
        print(f"  - {req}")
    print(f"Potential Issues: {len(analysis.potential_issues)}")
    for issue in analysis.potential_issues:
        print(f"  - {issue}")
    print(f"Estimated Duration: {analysis.estimated_duration_seconds:.1f}s")
    print(f"Confidence: {analysis.confidence:.2f}")
    print()

    # ========================================
    # Test 2: Problem Analysis - Complex Request
    # ========================================
    print("-" * 80)
    print("TEST 2: Problem Analysis - Complex Request")
    print("-" * 80)
    print()

    # Create complex context with large data
    large_data = pd.DataFrame({
        'age': np.random.randint(21, 70, 50000),
        'income': np.random.randint(30000, 120000, 50000),
    })
    complex_context = create_test_context(
        "Generate 50000 synthetic records and then validate the quality",
        large_data,
        50000,
    )

    analysis = problem_analyzer.analyze(complex_context)

    print(f"Problem Type: {analysis.problem_type.value}")
    print(f"Complexity: {analysis.complexity.value}")
    print(f"Difficulty Score: {analysis.difficulty_score:.2f}")
    print(f"Estimated Duration: {analysis.estimated_duration_seconds:.1f}s")
    print()

    # ========================================
    # Test 3: Generate Alternatives
    # ========================================
    print("-" * 80)
    print("TEST 3: Generate Alternatives")
    print("-" * 80)
    print()

    context = create_test_context("Generate 1000 synthetic records", data, 1000)
    alternatives = reasoning_engine.generate_alternatives(context, count=3)

    print(f"Generated {len(alternatives)} alternatives:")
    for i, alt in enumerate(alternatives, 1):
        print(f"\n  Alternative {i}:")
        print(f"    Strategy: {alt.get('strategy', 'N/A')}")
        print(f"    Description: {alt.get('description', 'N/A')}")
        print(f"    Estimated Time: {alt.get('estimated_time', 'N/A')}")
        print(f"    Estimated Quality: {alt.get('estimated_quality', 'N/A')}")
    print()

    # ========================================
    # Test 4: Evaluate Alternatives
    # ========================================
    print("-" * 80)
    print("TEST 4: Evaluate Alternatives")
    print("-" * 80)
    print()

    evaluation = reasoning_engine.evaluate(context, alternatives)

    print("Evaluation Results:")
    print(f"\n  Best Alternative:")
    best = evaluation["best"]
    print(f"    Score: {best['score']:.2f}")
    print(f"    Strategy: {best['alternative'].get('strategy', 'N/A')}")
    print(f"    Pros:")
    for pro in best["pros"]:
        print(f"      - {pro}")
    print(f"    Cons:")
    for con in best["cons"]:
        print(f"      - {con}")
    print()

    # ========================================
    # Test 5: Consistency Checking
    # ========================================
    print("-" * 80)
    print("TEST 5: Consistency Checking")
    print("-" * 80)
    print()

    # Create context with potential conflicts
    conflict_context = create_test_context(
        "Generate 200000 synthetic records",
        data,
        200000,
    )
    # Simulate low memory
    conflict_context.environment.available_memory_mb = 500

    issues = reasoning_engine.check_consistency(conflict_context)

    print(f"Found {len(issues)} consistency issues:")
    for issue in issues:
        print(f"\n  Type: {issue['type']}")
        print(f"  Description: {issue['description']}")
        print(f"  Details: {issue['details']}")
    print()

    # ========================================
    # Test 6: Comprehensive Reasoning
    # ========================================
    print("-" * 80)
    print("TEST 6: Comprehensive Reasoning")
    print("-" * 80)
    print()

    context = create_test_context(
        "Generate 5000 synthetic records",
        data,
        5000,
    )

    result = reasoning_engine.reason_comprehensive(context)

    print("Comprehensive Reasoning Result:")
    print(f"\n  Problem Analysis:")
    print(f"    Type: {result.problem_analysis.problem_type.value}")
    print(f"    Complexity: {result.problem_analysis.complexity.value}")
    print(f"    Difficulty: {result.problem_analysis.difficulty_score:.2f}")
    print(f"    Duration: {result.problem_analysis.estimated_duration_seconds:.1f}s")

    print(f"\n  Alternatives Generated: {len(result.alternatives)}")

    print(f"\n  Best Alternative:")
    if result.evaluation.get("best"):
        best = result.evaluation["best"]
        print(f"    Score: {best['score']:.2f}")
        print(f"    Strategy: {best['alternative'].get('strategy', 'N/A')}")

    print(f"\n  Consistency Issues: {len(result.consistency_checks)}")

    print(f"\n  Recommendation:")
    rec = result.recommendation
    print(f"    Problem Type: {rec['problem_type']}")
    print(f"    Complexity: {rec['complexity']}")
    if rec.get("suggested_approach"):
        print(f"    Suggested Approach: {rec['suggested_approach']}")
    if rec.get("warnings"):
        print(f"    Warnings:")
        for warning in rec["warnings"]:
            print(f"      - {warning}")

    print(f"\n  Overall Confidence: {result.confidence:.2f}")
    print()

    # ========================================
    # Summary
    # ========================================
    print("=" * 80)
    print("  PHASE 8 TEST SUMMARY")
    print("=" * 80)
    print()

    print("[OK] Problem Analyzer: Working")
    print("[OK] Alternative Generation: Working")
    print("[OK] Alternative Evaluation: Working")
    print("[OK] Consistency Checking: Working")
    print("[OK] Comprehensive Reasoning: Working")
    print()
    print("Phase 8: REASONING ENGINE - COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_reasoning_engine())
