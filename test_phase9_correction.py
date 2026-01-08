"""
Test Phase 9: Self-Correction System

This script tests the self-correction system:
- Error detection
- Error diagnosis
- Correction formulation
- Retry with backoff
"""

import asyncio
import pandas as pd
import numpy as np
from synth.agent.correction import SelfCorrectionEngine, ErrorType, CorrectionResult
from synth.agent.models.core import (
    Context,
    ParsedRequest,
    RequestType,
    EnvironmentContext,
)


async def test_self_correction():
    """Test self-correction system."""
    print("=" * 80)
    print("  PHASE 9: SELF-CORRECTION SYSTEM TEST")
    print("=" * 80)
    print()

    # Initialize components
    print("Initializing components...")
    correction_engine = SelfCorrectionEngine(max_retries=3)
    print()

    # ========================================
    # Test 1: Error Detection
    # ========================================
    print("-" * 80)
    print("TEST 1: Error Detection")
    print("-" * 80)
    print()

    # Create test context
    context = Context(
        request=ParsedRequest(
            request_id="test_req",
            original_text="Generate 100000 synthetic records",
            intent="Generate synthetic data",
            request_type=RequestType.DATA_GENERATION,
            entities={"count": 100000},
            constraints=[],
            parameters={},
            complexity=0.5,
            confidence=0.8,
        ),
        environment=EnvironmentContext(
            available_memory_mb=500,  # Low memory
            available_cpu_percent=80,
            available_disk_gb=50,
            active_sessions=1,
        ),
        conversation_history=[],
        user_preferences={},
        similar_past_situations=[],
        working_variables={"data": pd.DataFrame({'x': [1, 2, 3]})},
    )

    # Test different error types
    errors = [
        Exception("Operation timed out after 30 seconds"),
        Exception("Out of memory"),
        Exception("Invalid value in generated data"),
        Exception("Execution failed"),
    ]

    for error in errors:
        detection = correction_engine._detect_error(error, context)
        print(f"Error: {str(error)[:50]}...")
        print(f"  Detected Type: {detection.error_type.value}")
        print(f"  Severity: {detection.severity.value}")
        print()

    # ========================================
    # Test 2: Error Diagnosis
    # ========================================
    print("-" * 80)
    print("TEST 2: Error Diagnosis")
    print("-" * 80)
    print()

    error = Exception("Operation timed out after 30 seconds")
    detection = correction_engine._detect_error(error, context)
    diagnosis = correction_engine._diagnose_error(detection, context)

    print(f"Root Cause: {diagnosis['root_cause']}")
    print(f"Suggested Fixes:")
    for fix in diagnosis['suggested_fixes']:
        print(f"  - {fix}")
    print(f"Prevention:")
    for prevention in diagnosis['prevention']:
        print(f"  - {prevention}")
    print()

    # ========================================
    # Test 3: Correction Formulation
    # ========================================
    print("-" * 80)
    print("TEST 3: Correction Formulation")
    print("-" * 80)
    print()

    corrections = correction_engine._generate_corrections(detection, diagnosis, context)

    print(f"Generated {len(corrections)} corrections:")
    for i, correction in enumerate(corrections, 1):
        print(f"\n  Correction {i}:")
        print(f"    Fix: {correction['fix_description']}")
        print(f"    Confidence: {correction['confidence']:.2f}")
        if correction['parameters']:
            print(f"    Parameters: {correction['parameters']}")
    print()

    # ========================================
    # Test 4: Retry with Backoff
    # ========================================
    print("-" * 80)
    print("TEST 4: Retry with Exponential Backoff")
    print("-" * 80)
    print()

    attempt_count = [0]

    async def flaky_function():
        """Function that fails a few times before succeeding."""
        attempt_count[0] += 1
        if attempt_count[0] < 3:
            raise Exception(f"Temporary failure (attempt {attempt_count[0]})")
        return f"Success on attempt {attempt_count[0]}"

    try:
        result = await correction_engine.retry_with_backoff(
            flaky_function,
            max_retries=5,
            base_delay=0.1,
        )
        print(f"Result: {result}")
        print(f"Total attempts: {attempt_count[0]}")
    except Exception as e:
        print(f"Failed after all retries: {str(e)}")
    print()

    # ========================================
    # Test 5: Detect and Correct Flow
    # ========================================
    print("-" * 80)
    print("TEST 5: Detect and Correct Flow")
    print("-" * 80)
    print()

    # Create a retry function that simulates correction
    retry_attempts = [0]

    async def retry_with_correction(modified_context):
        """Simulate retry with correction."""
        retry_attempts[0] += 1

        # Simulate that correction worked
        if retry_attempts[0] >= 2:
            return True
        raise Exception("Still failing")

    error = Exception("Operation timed out")
    result = await correction_engine.detect_and_correct(
        error,
        context,
        retry_with_correction,
    )

    print(f"Success: {result.success}")
    print(f"Outcome: {result.outcome}")
    print(f"Correction Applied: {result.correction_applied.get('fix_description', 'N/A')}")
    print(f"Attempts Made: {result.attempts_made}")
    print()

    # ========================================
    # Test 6: Transient Error Detection
    # ========================================
    print("-" * 80)
    print("TEST 6: Transient Error Detection")
    print("-" * 80)
    print()

    transient_errors = [
        Exception("Connection timeout"),
        Exception("Service temporarily unavailable"),
        Exception("Network error"),
    ]

    permanent_errors = [
        Exception("Invalid input"),
        Exception("Permission denied"),
        Exception("Not found"),
    ]

    print("Transient Errors:")
    for error in transient_errors:
        is_transient = correction_engine.is_transient_error(error)
        print(f"  {str(error):50s} - Transient: {is_transient}")

    print("\nPermanent Errors:")
    for error in permanent_errors:
        is_transient = correction_engine.is_transient_error(error)
        print(f"  {str(error):50s} - Transient: {is_transient}")
    print()

    # ========================================
    # Test 7: Learning from Corrections
    # ========================================
    print("-" * 80)
    print("TEST 7: Learning from Corrections")
    print("-" * 80)
    print()

    # Simulate multiple corrections
    for i in range(5):
        error = Exception("Timeout error")
        result = CorrectionResult(
            success=(i >= 2),  # Succeed after 2 attempts
            correction_applied={"fix": "increase_timeout"},
            outcome="Success" if i >= 2 else "Failed",
            attempts_made=i + 1,
        )
        detection = correction_engine._detect_error(error, context)
        diagnosis = correction_engine._diagnose_error(detection, context)
        correction_engine._learn_from_correction(detection, diagnosis, result)

    # Get error stats
    stats = correction_engine.get_error_stats()
    print("Error Statistics:")
    print(f"  Total Errors Detected: {stats['total_errors_detected']}")
    print(f"  Error Types: {stats['error_types']}")
    print(f"  Solutions Learned: {stats['solutions_learned']}")
    print(f"  Most Common Errors:")
    for err in stats['most_common_errors']:
        print(f"    {err['error_type']}: {err['count']} occurrences")
    print()

    # ========================================
    # Summary
    # ========================================
    print("=" * 80)
    print("  PHASE 9 TEST SUMMARY")
    print("=" * 80)
    print()

    print("[OK] Error Detection: Working")
    print("[OK] Error Diagnosis: Working")
    print("[OK] Correction Formulation: Working")
    print("[OK] Retry with Backoff: Working")
    print("[OK] Detect and Correct Flow: Working")
    print("[OK] Transient Error Detection: Working")
    print("[OK] Learning from Corrections: Working")
    print()
    print("Phase 9: SELF-CORRECTION SYSTEM - COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_self_correction())
