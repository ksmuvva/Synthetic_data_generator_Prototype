"""
Logging System for the True AI Agent.

Provides comprehensive logging with:
- Structured logging with levels
- Console and file output
- Log rotation
- Request/response tracking
- Performance timing
- Component-specific loggers
"""

import logging
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
from contextlib import contextmanager
import time
import json

from synth.agent.config import LoggingConfig, LogLevel, get_config


class AgentLogger:
    """
    Structured logger for the SYNTH AI Agent.

    Provides component-specific loggers with automatic context tracking.

    Example:
        ```python
        from synth.agent.logging import get_logger

        logger = get_logger("memory")
        logger.info("Memory initialized", {"entries": 100})

        with logger.timer("operation"):
            # Do work
            pass
        ```
    """

    # Component loggers cache
    _loggers: Dict[str, "AgentLogger"] = {}

    def __init__(self, component: str):
        """
        Initialize logger for a component.

        Args:
            component: Component name (e.g., "memory", "planning", "llm")
        """
        self.component = component
        self._logger = logging.getLogger(f"synth.agent.{component}")
        self._timings: Dict[str, float] = {}

    @classmethod
    def get_logger(cls, component: str) -> "AgentLogger":
        """
        Get or create logger for a component.

        Args:
            component: Component name

        Returns:
            AgentLogger instance
        """
        if component not in cls._loggers:
            cls._loggers[component] = cls(component)
        return cls._loggers[component]

    def _log(
        self,
        level: LogLevel,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Internal logging method.

        Args:
            level: Log level
            message: Log message
            context: Additional context data
        """
        config = get_config()
        logging_config = config.logging

        if not logging_config.enabled:
            return

        # Build log record
        log_data = {
            "component": self.component,
            "message": message,
            "timestamp": datetime.now().isoformat(),
        }

        if context:
            log_data.update(context)

        # Format message
        formatted_parts = []
        if logging_config.include_timestamp:
            formatted_parts.append(log_data["timestamp"])
        if logging_config.include_level:
            formatted_parts.append(f"[{level.value}]")
        if logging_config.include_module:
            formatted_parts.append(f"[{self.component}]")

        formatted_parts.append(message)

        if context and config.debug_mode:
            context_str = json.dumps(context, default=str)
            formatted_parts.append(f"({context_str})")

        formatted_message = " ".join(formatted_parts)

        # Log at appropriate level
        if level == LogLevel.DEBUG:
            self._logger.debug(formatted_message)
        elif level == LogLevel.INFO:
            self._logger.info(formatted_message)
        elif level == LogLevel.WARNING:
            self._logger.warning(formatted_message)
        elif level == LogLevel.ERROR:
            self._logger.error(formatted_message)
        elif level == LogLevel.CRITICAL:
            self._logger.critical(formatted_message)

    def debug(self, message: str, context: Optional[Dict[str, Any]] = None):
        """Log debug message."""
        self._log(LogLevel.DEBUG, message, context)

    def info(self, message: str, context: Optional[Dict[str, Any]] = None):
        """Log info message."""
        self._log(LogLevel.INFO, message, context)

    def warning(self, message: str, context: Optional[Dict[str, Any]] = None):
        """Log warning message."""
        self._log(LogLevel.WARNING, message, context)

    def error(self, message: str, context: Optional[Dict[str, Any]] = None, exc_info: bool = False):
        """Log error message."""
        if exc_info:
            self._logger.exception(message)
        else:
            self._log(LogLevel.ERROR, message, context)

    def critical(self, message: str, context: Optional[Dict[str, Any]] = None):
        """Log critical message."""
        self._log(LogLevel.CRITICAL, message, context)

    @contextmanager
    def timer(self, operation: str):
        """
        Context manager for timing operations.

        Args:
            operation: Operation name

        Example:
            ```python
            with logger.timer("data_generation"):
                generate_data()
            ```
        """
        start_time = time.time()
        self.debug(f"Starting: {operation}")

        try:
            yield

        finally:
            elapsed = time.time() - start_time
            self._timings[operation] = elapsed
            self.debug(f"Completed: {operation}", {"duration_seconds": elapsed})

    def log_request(self, request_text: str, request_type: str):
        """Log incoming request."""
        self.info(
            f"Request: {request_type}",
            {"request_text": request_text[:100]}  # Truncate long requests
        )

    def log_response(self, success: bool, duration: float, metadata: Optional[Dict[str, Any]] = None):
        """Log response."""
        status = "success" if success else "failure"
        self.info(
            f"Response: {status}",
            {
                "duration_seconds": duration,
                **(metadata or {})
            }
        )

    def log_error(self, error: Exception, context: Optional[Dict[str, Any]] = None):
        """Log error with exception info."""
        error_context = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            **(context or {})
        }
        self.error(str(error), error_context, exc_info=True)

    def get_timing_stats(self) -> Dict[str, float]:
        """
        Get timing statistics for all timed operations.

        Returns:
            Dictionary of operation timings
        """
        return self._timings.copy()

    def clear_timings(self):
        """Clear all timing data."""
        self._timings.clear()


class RequestLogger:
    """
    Logger for tracking complete request/response cycles.

    Provides detailed logging for each request including:
    - Request details
    - Processing steps
    - Response details
    - Performance metrics
    - Errors and warnings
    """

    def __init__(self):
        """Initialize request logger."""
        self.logger = AgentLogger.get_logger("request")
        self._current_request: Optional[str] = None
        self._request_start_time: Optional[float] = None

    def start_request(self, request_id: str, request_text: str, request_type: str):
        """
        Log start of request processing.

        Args:
            request_id: Unique request identifier
            request_text: Request text
            request_type: Request type
        """
        self._current_request = request_id
        self._request_start_time = time.time()

        self.logger.info(
            f"Request started: {request_type}",
            {
                "request_id": request_id,
                "request_text": request_text[:200],
                "request_type": request_type,
            }
        )

    def log_step(self, step_name: str, step_data: Optional[Dict[str, Any]] = None):
        """
        Log a processing step.

        Args:
            step_name: Step name
            step_data: Step-specific data
        """
        if not self._current_request:
            return

        self.logger.debug(
            f"Step: {step_name}",
            {
                "request_id": self._current_request,
                **(step_data or {})
            }
        )

    def log_warning(self, warning_message: str, warning_data: Optional[Dict[str, Any]] = None):
        """
        Log a warning during request processing.

        Args:
            warning_message: Warning message
            warning_data: Warning-specific data
        """
        if not self._current_request:
            return

        self.logger.warning(
            f"Warning: {warning_message}",
            {
                "request_id": self._current_request,
                **(warning_data or {})
            }
        )

    def end_request(
        self,
        request_id: str,
        success: bool,
        response_message: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Log end of request processing.

        Args:
            request_id: Unique request identifier
            success: Whether request succeeded
            response_message: Response message
            metadata: Response metadata
        """
        if self._request_start_time:
            duration = time.time() - self._request_start_time
        else:
            duration = 0.0

        self.logger.info(
            f"Request completed: {'success' if success else 'failure'}",
            {
                "request_id": request_id,
                "duration_seconds": duration,
                "response_preview": response_message[:200],
                **(metadata or {})
            }
        )

        self._current_request = None
        self._request_start_time = None


class PerformanceLogger:
    """
    Logger for performance metrics and timing.

    Tracks:
    - Function execution times
    - Resource usage
    - Bottleneck identification
    """

    def __init__(self):
        """Initialize performance logger."""
        self.logger = AgentLogger.get_logger("performance")
        self._function_calls: Dict[str, List[float]] = {}

    @contextmanager
    def track_function(self, function_name: str):
        """
        Track function execution time.

        Args:
            function_name: Name of function to track

        Example:
            ```python
            perf_logger = PerformanceLogger()

            with perf_logger.track_function("generate_data"):
                generate_data()
            ```
        """
        start_time = time.time()

        try:
            yield

        finally:
            elapsed = time.time() - start_time

            if function_name not in self._function_calls:
                self._function_calls[function_name] = []

            self._function_calls[function_name].append(elapsed)

            self.logger.debug(
                f"Function: {function_name}",
                {"duration_seconds": elapsed}
            )

    def get_function_stats(self, function_name: str) -> Dict[str, Any]:
        """
        Get statistics for a function.

        Args:
            function_name: Function name

        Returns:
            Statistics dictionary
        """
        if function_name not in self._function_calls:
            return {
                "function": function_name,
                "call_count": 0,
            }

        times = self._function_calls[function_name]

        return {
            "function": function_name,
            "call_count": len(times),
            "total_time": sum(times),
            "avg_time": sum(times) / len(times),
            "min_time": min(times),
            "max_time": max(times),
        }

    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """
        Get statistics for all tracked functions.

        Returns:
            Dictionary of function statistics
        """
        return {
            func_name: self.get_function_stats(func_name)
            for func_name in self._function_calls
        }

    def get_bottlenecks(self, top_n: int = 5) -> List[Dict[str, Any]]:
        """
        Identify performance bottlenecks.

        Args:
            top_n: Number of bottlenecks to return

        Returns:
            List of bottleneck functions sorted by total time
        """
        all_stats = self.get_all_stats()

        bottlenecks = sorted(
            [
                {"name": name, **stats}
                for name, stats in all_stats.items()
            ],
            key=lambda x: x["total_time"],
            reverse=True
        )

        return bottlenecks[:top_n]

    def clear_stats(self):
        """Clear all performance statistics."""
        self._function_calls.clear()


class AuditLogger:
    """
    Logger for security and compliance auditing.

    Logs:
    - Agent actions
    - Data access
    - Configuration changes
    - Security events
    """

    def __init__(self):
        """Initialize audit logger."""
        self.logger = AgentLogger.get_logger("audit")

    def log_action(
        self,
        action: str,
        actor: str,
        target: Optional[str] = None,
        result: Optional[str] = None
    ):
        """
        Log an agent action.

        Args:
            action: Action performed
            actor: Who performed the action (e.g., "user", "system")
            target: Target of action (optional)
            result: Result of action (optional)
        """
        self.logger.info(
            f"Audit: {action}",
            {
                "actor": actor,
                "target": target,
                "result": result,
                "timestamp": datetime.now().isoformat(),
            }
        )

    def log_data_access(
        self,
        operation: str,
        data_source: str,
        record_count: Optional[int] = None
    ):
        """
        Log data access.

        Args:
            operation: Operation performed (e.g., "read", "write", "delete")
            data_source: Data source accessed
            record_count: Number of records affected
        """
        self.logger.info(
            f"Data Access: {operation}",
            {
                "data_source": data_source,
                "record_count": record_count,
                "timestamp": datetime.now().isoformat(),
            }
        )

    def log_config_change(
        self,
        config_path: str,
        old_value: Any,
        new_value: Any
    ):
        """
        Log configuration change.

        Args:
            config_path: Configuration path (e.g., "llm.temperature")
            old_value: Previous value
            new_value: New value
        """
        self.logger.info(
            f"Config Change: {config_path}",
            {
                "old_value": str(old_value),
                "new_value": str(new_value),
                "timestamp": datetime.now().isoformat(),
            }
        )


# Global logger instances
_request_logger: Optional[RequestLogger] = None
_performance_logger: Optional[PerformanceLogger] = None
_audit_logger: Optional[AuditLogger] = None


def get_logger(component: str) -> AgentLogger:
    """
    Get or create logger for a component.

    Args:
        component: Component name

    Returns:
        AgentLogger instance
    """
    return AgentLogger.get_logger(component)


def get_request_logger() -> RequestLogger:
    """Get global request logger instance."""
    global _request_logger
    if _request_logger is None:
        _request_logger = RequestLogger()
    return _request_logger


def get_performance_logger() -> PerformanceLogger:
    """Get global performance logger instance."""
    global _performance_logger
    if _performance_logger is None:
        _performance_logger = PerformanceLogger()
    return _performance_logger


def get_audit_logger() -> AuditLogger:
    """Get global audit logger instance."""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger


def setup_logging(config: Optional[LoggingConfig] = None):
    """
    Setup logging system based on configuration.

    Args:
        config: Logging configuration (uses global config if None)
    """
    if config is None:
        config = get_config().logging

    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, config.level.value))

    # Clear existing handlers
    root_logger.handlers.clear()

    # Create formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Add console handler
    if config.log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    # Add file handler
    if config.log_to_file:
        # Ensure log directory exists
        log_path = Path(config.log_file_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        # Create rotating file handler
        from logging.handlers import RotatingFileHandler

        file_handler = RotatingFileHandler(
            config.log_file_path,
            maxBytes=config.max_file_size_mb * 1024 * 1024,
            backupCount=config.backup_count
        )
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)


def shutdown_logging():
    """Shutdown logging system and flush all handlers."""
    logging.shutdown()


# Convenience decorators
def log_execution(logger: Optional[AgentLogger] = None):
    """
    Decorator to log function execution.

    Args:
        logger: Logger to use (creates component logger if None)

    Example:
        ```python
        @log_execution()
        def my_function():
            pass
        ```
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            component = logger.component if logger else func.__module__
            fn_logger = logger or get_logger(component)

            with fn_logger.timer(func.__name__):
                try:
                    result = func(*args, **kwargs)
                    fn_logger.debug(f"Completed: {func.__name__}")
                    return result
                except Exception as e:
                    fn_logger.log_error(e, {"function": func.__name__})
                    raise

        return wrapper
    return decorator


def log_performance(function_name: Optional[str] = None):
    """
    Decorator to track function performance.

    Args:
        function_name: Custom function name (uses actual name if None)

    Example:
        ```python
        @log_performance()
        def my_function():
            pass
        ```
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            perf_logger = get_performance_logger()
            name = function_name or func.__name__

            with perf_logger.track_function(name):
                return func(*args, **kwargs)

        return wrapper
    return decorator
