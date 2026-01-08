"""
Configuration System for the True AI Agent.

Provides centralized configuration management with support for:
- Environment variables
- Configuration files (YAML/JSON)
- Default values
- Validation
- Type safety
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional, List, Type, TypeVar
from dataclasses import dataclass, field, fields
from enum import Enum
import json


class LogLevel(str, Enum):
    """Log levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LLMProvider(str, Enum):
    """LLM providers."""
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    OLLAMA = "ollama"
    AZURE = "azure"


@dataclass
class MemoryConfig:
    """Configuration for memory systems."""

    # Storage paths
    storage_path: str = ".agent_memory"
    short_term_max_entries: int = 100
    long_term_path: str = ".agent_memory/long_term.json"

    # Learning settings
    pattern_learning_enabled: bool = True
    strategy_learning_enabled: bool = True
    error_learning_enabled: bool = True

    # Retention policies
    min_pattern_occurrences: int = 3
    strategy_success_threshold: float = 0.7
    error_solution_min_confidence: float = 0.6


@dataclass
class LLMConfig:
    """Configuration for LLM providers."""

    provider: LLMProvider = LLMProvider.ANTHROPIC

    # API settings
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    model: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 4096
    timeout_seconds: int = 60

    # Retry settings
    max_retries: int = 3
    retry_delay_seconds: float = 1.0

    # Rate limiting
    requests_per_minute: int = 60
    tokens_per_minute: int = 90000


@dataclass
class GenerationConfig:
    """Configuration for data generation."""

    # Default parameters
    default_count: int = 1000
    default_distribution: str = "statistical"
    default_output_format: str = "csv"

    # Quality settings
    min_quality_score: float = 0.8
    validation_enabled: bool = True
    validation_sample_size: int = 1000

    # Performance settings
    batch_size: int = 100
    parallel_workers: int = 1
    max_records_per_batch: int = 10000


@dataclass
class ValidationConfig:
    """Configuration for data validation."""

    # Validation thresholds
    statistical_similarity_threshold: float = 0.8
    correlation_threshold: float = 0.7
    distribution_match_threshold: float = 0.75

    # Privacy validation
    privacy_validation_enabled: bool = True
    privacy_threshold: float = 0.95
    privacy_sample_size: int = 500

    # Schema validation
    schema_validation_enabled: bool = True
    type_checking_enabled: bool = True


@dataclass
class PlanningConfig:
    """Configuration for planning engine."""

    # Goal decomposition
    max_sub_goal_depth: int = 5
    complexity_threshold: float = 0.6

    # Plan creation
    enable_checkpoints: bool = True
    checkpoint_interval: int = 3
    estimated_duration_safety_margin: float = 1.5

    # Adaptive planning
    adaptive_enabled: bool = True
    replan_threshold: float = 0.5
    stall_timeout_multiplier: float = 3.0


@dataclass
class OptimizationConfig:
    """Configuration for parameter optimization."""

    # Learning settings
    learning_enabled: bool = True
    min_samples_for_learning: int = 5
    learning_rate: float = 0.1

    # Optimization targets
    optimize_sample_size: bool = True
    optimize_distribution: bool = True
    optimize_thresholds: bool = True

    # Memory constraints
    memory_safety_factor: float = 0.5
    min_memory_mb: int = 500


@dataclass
class CorrectionConfig:
    """Configuration for self-correction."""

    # Detection settings
    detection_enabled: bool = True
    error_patterns_enabled: bool = True
    validation_check_enabled: bool = True

    # Retry settings
    max_correction_attempts: int = 3
    base_retry_delay: float = 1.0
    max_retry_delay: float = 60.0
    backoff_multiplier: float = 2.0

    # Learning from corrections
    learn_from_corrections: bool = True
    min_correction_confidence: float = 0.7


@dataclass
class LoggingConfig:
    """Configuration for logging."""

    # Basic settings
    enabled: bool = True
    level: LogLevel = LogLevel.INFO

    # Output settings
    log_to_console: bool = True
    log_to_file: bool = False
    log_file_path: str = ".agent_memory/agent.log"

    # Format settings
    include_timestamp: bool = True
    include_level: bool = True
    include_module: bool = True
    include_function: bool = False

    # Rotation settings
    max_file_size_mb: int = 10
    backup_count: int = 5


@dataclass
class MetricsConfig:
    """Configuration for metrics collection."""

    # Collection settings
    enabled: bool = True
    collect_performance_metrics: bool = True
    collect_quality_metrics: bool = True
    collect_resource_metrics: bool = True

    # Storage settings
    storage_path: str = ".agent_memory/metrics.json"
    retention_days: int = 30

    # Reporting settings
    aggregate_interval_seconds: int = 60
    report_on_shutdown: bool = True


@dataclass
class CLIConfig:
    """Configuration for CLI interface."""

    # Display settings
    use_rich: bool = True
    show_progress: bool = True
    show_metadata: bool = True
    show_suggestions: bool = True
    show_warnings: bool = True

    # Interactive settings
    prompt_color: str = "blue"
    response_color: str = "green"
    error_color: str = "red"

    # Output formatting
    max_preview_rows: int = 5
    max_string_length: int = 500


@dataclass
class AgentConfig:
    """
    Main configuration for the SYNTH AI Agent.

    This is the primary configuration class that aggregates all
    subsystem configurations.

    Example:
        ```python
        from synth.agent.config import AgentConfig, get_config

        # Use default configuration
        config = get_config()

        # Load from environment
        config = AgentConfig.from_env()

        # Load from file
        config = AgentConfig.from_file("config.yaml")

        # Save configuration
        config.to_file("config.yaml")
        ```
    """

    # Subsystem configurations
    memory: MemoryConfig = field(default_factory=MemoryConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    generation: GenerationConfig = field(default_factory=GenerationConfig)
    validation: ValidationConfig = field(default_factory=ValidationConfig)
    planning: PlanningConfig = field(default_factory=PlanningConfig)
    optimization: OptimizationConfig = field(default_factory=OptimizationConfig)
    correction: CorrectionConfig = field(default_factory=CorrectionConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    metrics: MetricsConfig = field(default_factory=MetricsConfig)
    cli: CLIConfig = field(default_factory=CLIConfig)

    # Agent settings
    agent_name: str = "SYNTH"
    version: str = "1.0.0"
    debug_mode: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to dictionary.

        Returns:
            Dictionary representation of configuration
        """
        result = {}
        for f in fields(self):
            value = getattr(self, f.name)
            if isinstance(value, (MemoryConfig, LLMConfig, GenerationConfig,
                                 ValidationConfig, PlanningConfig,
                                 OptimizationConfig, CorrectionConfig,
                                 LoggingConfig, MetricsConfig, CLIConfig)):
                result[f.name] = {
                    sf.name: getattr(value, sf.name)
                    for sf in fields(value)
                }
            else:
                result[f.name] = value
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentConfig":
        """
        Create configuration from dictionary.

        Args:
            data: Dictionary with configuration values

        Returns:
            AgentConfig instance
        """
        # Create subsystem configs
        config_map = {
            "memory": MemoryConfig,
            "llm": LLMConfig,
            "generation": GenerationConfig,
            "validation": ValidationConfig,
            "planning": PlanningConfig,
            "optimization": OptimizationConfig,
            "correction": CorrectionConfig,
            "logging": LoggingConfig,
            "metrics": MetricsConfig,
            "cli": CLIConfig,
        }

        subsystem_configs = {}
        for key, config_class in config_map.items():
            if key in data and isinstance(data[key], dict):
                subsystem_configs[key] = config_class(**data[key])

        # Create main config
        main_config = {
            k: v for k, v in data.items()
            if k not in config_map
        }

        return cls(**subsystem_configs, **main_config)

    def to_file(self, path: str, format: str = "json"):
        """
        Save configuration to file.

        Args:
            path: Path to save configuration
            format: File format ("json" or "yaml")
        """
        data = self.to_dict()

        if format == "json":
            with open(path, "w") as f:
                json.dump(data, f, indent=2, default=str)
        elif format == "yaml":
            try:
                import yaml
                with open(path, "w") as f:
                    yaml.dump(data, f, default_flow_style=False)
            except ImportError:
                raise ImportError("PyYAML is required for YAML format. Install with: pip install pyyaml")
        else:
            raise ValueError(f"Unsupported format: {format}")

    @classmethod
    def from_file(cls, path: str) -> "AgentConfig":
        """
        Load configuration from file.

        Args:
            path: Path to configuration file

        Returns:
            AgentConfig instance
        """
        path_obj = Path(path)

        if not path_obj.exists():
            raise FileNotFoundError(f"Configuration file not found: {path}")

        if path_obj.suffix == ".json":
            with open(path, "r") as f:
                data = json.load(f)
        elif path_obj.suffix in [".yaml", ".yml"]:
            try:
                import yaml
                with open(path, "r") as f:
                    data = yaml.safe_load(f)
            except ImportError:
                raise ImportError("PyYAML is required for YAML format. Install with: pip install pyyaml")
        else:
            raise ValueError(f"Unsupported file format: {path_obj.suffix}")

        return cls.from_dict(data)

    @classmethod
    def from_env(cls, prefix: str = "SYNTH_") -> "AgentConfig":
        """
        Load configuration from environment variables.

        Environment variables should be named with the prefix followed by
        the config path, e.g., SYNTH_LLM_PROVIDER, SYNTH_MEMORY_STORAGE_PATH.

        Args:
            prefix: Environment variable prefix

        Returns:
            AgentConfig instance
        """
        config = cls()

        # Update LLM config from environment
        if f"{prefix}LLM_PROVIDER" in os.environ:
            config.llm.provider = LLMProvider(os.environ[f"{prefix}LLM_PROVIDER"])
        if f"{prefix}LLM_API_KEY" in os.environ:
            config.llm.api_key = os.environ[f"{prefix}LLM_API_KEY"]
        if f"{prefix}LLM_MODEL" in os.environ:
            config.llm.model = os.environ[f"{prefix}LLM_MODEL"]

        # Update memory config from environment
        if f"{prefix}MEMORY_STORAGE_PATH" in os.environ:
            config.memory.storage_path = os.environ[f"{prefix}MEMORY_STORAGE_PATH"]

        # Update logging config from environment
        if f"{prefix}LOG_LEVEL" in os.environ:
            config.logging.level = LogLevel(os.environ[f"{prefix}LOG_LEVEL"])
        if f"{prefix}LOG_FILE_PATH" in os.environ:
            config.logging.log_file_path = os.environ[f"{prefix}LOG_FILE_PATH"]

        return config

    def validate(self) -> List[str]:
        """
        Validate configuration values.

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        # Validate LLM config
        if self.llm.provider == LLMProvider.ANTHROPIC and not self.llm.api_key:
            errors.append("LLM_API_KEY is required for Anthropic provider")

        if self.llm.temperature < 0 or self.llm.temperature > 2:
            errors.append("LLM temperature must be between 0 and 2")

        if self.llm.max_tokens <= 0:
            errors.append("LLM max_tokens must be positive")

        # Validate generation config
        if self.generation.default_count <= 0:
            errors.append("Default count must be positive")

        if self.generation.min_quality_score < 0 or self.generation.min_quality_score > 1:
            errors.append("Min quality score must be between 0 and 1")

        # Validate validation config
        for threshold_name, threshold_value in [
            ("statistical_similarity", self.validation.statistical_similarity_threshold),
            ("correlation", self.validation.correlation_threshold),
            ("distribution_match", self.validation.distribution_match_threshold),
        ]:
            if threshold_value < 0 or threshold_value > 1:
                errors.append(f"Validation {threshold_name}_threshold must be between 0 and 1")

        # Validate logging config
        log_path = Path(self.logging.log_file_path)
        if log_path.exists() and not log_path.is_file():
            errors.append("Log file path exists but is not a file")

        return errors

    def merge(self, other: "AgentConfig") -> "AgentConfig":
        """
        Merge another configuration into this one.

        Values from `other` take precedence.

        Args:
            other: Configuration to merge

        Returns:
            New merged configuration
        """
        merged_dict = self.to_dict()
        other_dict = other.to_dict()

        # Deep merge
        for key, value in other_dict.items():
            if isinstance(value, dict) and key in merged_dict:
                merged_dict[key].update(value)
            else:
                merged_dict[key] = value

        return self.__class__.from_dict(merged_dict)


# Global configuration instance
_global_config: Optional[AgentConfig] = None


def get_config() -> AgentConfig:
    """
    Get the global configuration instance.

    Creates default configuration if none exists.

    Returns:
        AgentConfig instance
    """
    global _global_config

    if _global_config is None:
        _global_config = AgentConfig.from_env()

    return _global_config


def set_config(config: AgentConfig):
    """
    Set the global configuration instance.

    Args:
        config: Configuration to set as global
    """
    global _global_config
    _global_config = config


def reset_config():
    """Reset the global configuration to defaults."""
    global _global_config
    _global_config = None


def load_config_file(path: str) -> AgentConfig:
    """
    Load configuration from file and set as global.

    Args:
        path: Path to configuration file

    Returns:
        Loaded AgentConfig instance
    """
    config = AgentConfig.from_file(path)
    set_config(config)
    return config


def get_config_summary() -> Dict[str, Any]:
    """
    Get a summary of the current configuration.

    Returns:
        Dictionary with configuration summary
    """
    config = get_config()
    config_dict = config.to_dict()

    return {
        "agent_name": config.agent_name,
        "version": config.version,
        "debug_mode": config.debug_mode,
        "llm_provider": config.llm.provider.value,
        "llm_model": config.llm.model,
        "memory_enabled": config.memory.pattern_learning_enabled,
        "logging_enabled": config.logging.enabled,
        "log_level": config.logging.level.value,
        "metrics_enabled": config.metrics.enabled,
    }
