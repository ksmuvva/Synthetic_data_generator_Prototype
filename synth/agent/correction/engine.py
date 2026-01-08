"""
Self-Correction Engine - Unified self-correction system.

Implements:
- Error detection
- Error diagnosis
- Correction formulation
- Learning from corrections
"""

from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import time

from synth.agent.models.core import (
    Context,
    Error,
    ErrorSeverity,
    Correction,
    TaskStatus,
)


class ErrorType(str, Enum):
    """Types of errors."""
    EXECUTION_FAILURE = "execution_failure"
    INVALID_OUTPUT = "invalid_output"
    QUALITY_ISSUE = "quality_issue"
    TIMEOUT = "timeout"
    RESOURCE_ERROR = "resource_error"
    UNKNOWN = "unknown"


@dataclass
class ErrorDetection:
    """Detected error."""
    error_type: ErrorType
    severity: ErrorSeverity
    message: str
    details: Dict[str, Any]
    timestamp: float
    source: str


@dataclass
class CorrectionResult:
    """Result of applying a correction."""
    success: bool
    correction_applied: Dict[str, Any]
    outcome: str
    error_message: Optional[str] = None
    attempts_made: int = 0


class SelfCorrectionEngine:
    """
    Unified self-correction system.

    Handles:
    1. Error detection
    2. Error diagnosis
    3. Correction formulation
    4. Learning from corrections
    """

    def __init__(self, max_retries: int = 3):
        """
        Initialize self-correction engine.

        Args:
            max_retries: Maximum number of retry attempts
        """
        self.max_retries = max_retries
        self._error_patterns: Dict[str, List[Dict]] = {}
        self._solutions_learned: Dict[str, List[Dict]] = {}

    async def detect_and_correct(
        self,
        error: Exception,
        context: Context,
        retry_fn: Optional[Callable] = None,
    ) -> CorrectionResult:
        """
        Detect error type and apply correction.

        Args:
            error: The exception that occurred
            context: Current execution context
            retry_fn: Optional function to retry with correction

        Returns:
            CorrectionResult
        """
        # 1. Detect error type
        detection = self._detect_error(error, context)

        # 2. Diagnose root cause
        diagnosis = self._diagnose_error(detection, context)

        # 3. Generate corrections
        corrections = self._generate_corrections(detection, diagnosis, context)

        # 4. Apply corrections
        result = await self._apply_corrections(
            corrections,
            context,
            retry_fn,
        )

        # 5. Learn from outcome
        self._learn_from_correction(detection, diagnosis, result)

        return result

    def _detect_error(
        self,
        error: Exception,
        context: Context,
    ) -> ErrorDetection:
        """Detect error type and severity."""
        error_type = ErrorType.UNKNOWN
        severity = ErrorSeverity.MEDIUM
        details = {}

        error_message = str(error).lower()

        # Detect error type
        if "timeout" in error_message or "timed out" in error_message:
            error_type = ErrorType.TIMEOUT
            severity = ErrorSeverity.MEDIUM
        elif "memory" in error_message or "out of memory" in error_message:
            error_type = ErrorType.RESOURCE_ERROR
            severity = ErrorSeverity.HIGH
        elif "value" in error_message or "invalid" in error_message:
            error_type = ErrorType.INVALID_OUTPUT
            severity = ErrorSeverity.MEDIUM
        elif "permission" in error_message or "access" in error_message:
            error_type = ErrorType.RESOURCE_ERROR
            severity = ErrorSeverity.HIGH
        elif "failed" in error_message:
            error_type = ErrorType.EXECUTION_FAILURE
            severity = ErrorSeverity.HIGH
        else:
            # Try to determine from exception type
            error_type = ErrorType.EXECUTION_FAILURE

        return ErrorDetection(
            error_type=error_type,
            severity=severity,
            message=str(error),
            details={
                "exception_type": type(error).__name__,
                "context_info": self._get_context_info(context),
            },
            timestamp=time.time(),
            source=str(type(error)),
        )

    def _diagnose_error(
        self,
        detection: ErrorDetection,
        context: Context,
    ) -> Dict[str, Any]:
        """Diagnose root cause of error."""
        diagnosis = {
            "root_cause": "unknown",
            "suggested_fixes": [],
            "prevention": [],
        }

        # Diagnose based on error type
        if detection.error_type == ErrorType.TIMEOUT:
            diagnosis["root_cause"] = "operation took too long"
            diagnosis["suggested_fixes"] = [
                "reduce data size",
                "optimize parameters",
                "increase timeout",
            ]
            diagnosis["prevention"] = [
                "check data size before operation",
                "use progress monitoring",
            ]

        elif detection.error_type == ErrorType.RESOURCE_ERROR:
            diagnosis["root_cause"] = "insufficient system resources"
            diagnosis["suggested_fixes"] = [
                "reduce memory usage",
                "process in batches",
                "free up resources",
            ]
            diagnosis["prevention"] = [
                "check available resources first",
                "implement resource monitoring",
            ]

        elif detection.error_type == ErrorType.INVALID_OUTPUT:
            diagnosis["root_cause"] = "generated output doesn't meet requirements"
            diagnosis["suggested_fixes"] = [
                "adjust parameters",
                "use different strategy",
                "add validation",
            ]
            diagnosis["prevention"] = [
                "validate input parameters",
                "test with small sample first",
            ]

        elif detection.error_type == ErrorType.EXECUTION_FAILURE:
            diagnosis["root_cause"] = "operation failed during execution"
            diagnosis["suggested_fixes"] = [
                "retry operation",
                "check inputs",
                "use alternative method",
            ]
            diagnosis["prevention"] = [
                "add input validation",
                "implement checkpointing",
            ]

        return diagnosis

    def _generate_corrections(
        self,
        detection: ErrorDetection,
        diagnosis: Dict[str, Any],
        context: Context,
    ) -> List[Dict[str, Any]]:
        """Generate potential corrections."""
        corrections = []

        # Generate corrections based on diagnosis
        for fix in diagnosis.get("suggested_fixes", []):
            correction = {
                "fix_description": fix,
                "confidence": 0.7,
                "parameters": {},
            }

            # Add specific parameters based on fix type
            if "reduce data size" in fix.lower():
                count = context.request.entities.get("count", 100)
                correction["parameters"] = {"count": max(count // 2, 10)}
                correction["confidence"] = 0.8

            elif "reduce memory usage" in fix.lower():
                correction["parameters"] = {"batch_size": 100}
                correction["confidence"] = 0.9

            elif "increase timeout" in fix.lower():
                correction["parameters"] = {"timeout_multiplier": 2}
                correction["confidence"] = 0.7

            corrections.append(correction)

        return corrections

    async def _apply_corrections(
        self,
        corrections: List[Dict[str, Any]],
        context: Context,
        retry_fn: Optional[Callable],
    ) -> CorrectionResult:
        """Apply corrections with retry logic."""
        if not corrections:
            return CorrectionResult(
                success=False,
                correction_applied={},
                outcome="No corrections available",
                attempts_made=0,
            )

        # Sort corrections by confidence
        corrections.sort(key=lambda x: x.get("confidence", 0), reverse=True)

        # Try each correction
        for i, correction in enumerate(corrections[:self.max_retries]):
            attempt = i + 1

            try:
                # Apply correction
                if retry_fn:
                    # Modify context with correction parameters
                    modified_context = self._apply_correction_to_context(
                        context,
                        correction,
                    )

                    # Retry with correction
                    result = await retry_fn(modified_context)

                    if result:
                        return CorrectionResult(
                            success=True,
                            correction_applied=correction,
                            outcome=f"Correction successful on attempt {attempt}",
                            attempts_made=attempt,
                        )
                else:
                    # No retry function, just report the correction
                    return CorrectionResult(
                        success=True,
                        correction_applied=correction,
                        outcome="Correction formulated (no retry function provided)",
                        attempts_made=attempt,
                    )

            except Exception as e:
                # Correction failed, try next one
                continue

        # All corrections failed
        return CorrectionResult(
            success=False,
            correction_applied=corrections[0] if corrections else {},
            outcome=f"All {self.max_retries} correction attempts failed",
            attempts_made=min(len(corrections), self.max_retries),
        )

    def _apply_correction_to_context(
        self,
        context: Context,
        correction: Dict[str, Any],
    ) -> Context:
        """Apply correction parameters to context."""
        # Create a modified context with correction applied
        # Note: This is a simplified version
        # In production, would create a deep copy

        modified_params = context.request.entities.copy()
        modified_params.update(correction.get("parameters", {}))

        # Update context (in a real system, would be immutable)
        context.request.entities.update(modified_params)

        return context

    def _learn_from_correction(
        self,
        detection: ErrorDetection,
        diagnosis: Dict[str, Any],
        result: CorrectionResult,
    ):
        """Learn from correction outcome."""
        error_key = f"{detection.error_type.value}_{detection.source}"

        # Store error pattern
        if error_key not in self._error_patterns:
            self._error_patterns[error_key] = []

        self._error_patterns[error_key].append({
            "timestamp": detection.timestamp,
            "severity": detection.severity.value,
            "diagnosis": diagnosis,
            "outcome": result.outcome,
            "success": result.success,
        })

        # Store successful solutions
        if result.success:
            if error_key not in self._solutions_learned:
                self._solutions_learned[error_key] = []

            self._solutions_learned[error_key].append({
                "correction": result.correction_applied,
                "attempts": result.attempts_made,
                "timestamp": time.time(),
                "success_rate": 1.0 / result.attempts_made,
            })

    def get_error_stats(self) -> Dict[str, Any]:
        """Get error statistics."""
        total_errors = sum(len(patterns) for patterns in self._error_patterns.values())

        return {
            "total_errors_detected": total_errors,
            "error_types": len(self._error_patterns),
            "solutions_learned": len(self._solutions_learned),
            "most_common_errors": self._get_most_common_errors(),
        }

    def _get_most_common_errors(self) -> List[Dict[str, Any]]:
        """Get most common error types."""
        error_counts = {
            k: len(v)
            for k, v in self._error_patterns.items()
        }

        sorted_errors = sorted(
            error_counts.items(),
            key=lambda x: x[1],
            reverse=True,
        )

        return [
            {"error_type": k, "count": v}
            for k, v in sorted_errors[:5]
        ]

    def _get_context_info(self, context: Context) -> Dict[str, Any]:
        """Get relevant context information."""
        return {
            "request_type": context.request.request_type.value,
            "available_memory_mb": context.environment.available_memory_mb,
            "data_size": len(context.working_variables.get("data", [])),
        }

    async def retry_with_backoff(
        self,
        fn: Callable,
        max_retries: int = 3,
        base_delay: float = 1.0,
    ) -> Any:
        """
        Retry function with exponential backoff.

        Args:
            fn: Async function to retry
            max_retries: Maximum retry attempts
            base_delay: Base delay in seconds

        Returns:
            Result of function call

        Raises:
            Last exception if all retries fail
        """
        last_exception = None

        for attempt in range(max_retries):
            try:
                return await fn()
            except Exception as e:
                last_exception = e

                if attempt < max_retries - 1:
                    # Calculate delay with exponential backoff
                    delay = base_delay * (2 ** attempt)
                    await asyncio.sleep(delay)

        # All retries failed
        raise last_exception

    def is_transient_error(self, error: Exception) -> bool:
        """
        Check if an error is transient (retryable).

        Args:
            error: Exception to check

        Returns:
            True if transient, False otherwise
        """
        error_message = str(error).lower()

        # Transient error indicators
        transient_keywords = [
            "timeout",
            "temporary",
            "unavailable",
            "connection",
            "network",
        ]

        return any(keyword in error_message for keyword in transient_keywords)
