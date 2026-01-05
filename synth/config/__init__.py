"""
Configuration and settings management for synth.
"""

from pathlib import Path
from typing import Optional
import yaml

from pydantic import BaseModel, Field


class ProjectConfig(BaseModel):
    """Project configuration."""

    name: str = "synth-project"
    type: str = "tabular"
    created: str = ""

    patterns_directory: str = "patterns"
    patterns_format: str = "json"

    data_directory: str = "data"
    supported_formats: list[str] = ["csv", "excel", "json"]

    output_directory: str = "output"
    default_format: str = "csv"

    validation_enabled: bool = True
    quality_threshold: float = 0.85


class Settings:
    """Global settings singleton."""

    def __init__(self):
        self._config: Optional[ProjectConfig] = None
        self._project_root: Optional[Path] = None

    @property
    def config(self) -> ProjectConfig:
        """Get current configuration."""
        if self._config is None:
            self._config = ProjectConfig()
        return self._config

    @property
    def project_root(self) -> Path:
        """Get project root directory."""
        if self._project_root is None:
            self._project_root = Path.cwd()
        return self._project_root

    def load_config(self, config_path: Optional[Path] = None) -> ProjectConfig:
        """Load configuration from file."""
        if config_path is None:
            config_path = self.project_root / "synth-config.yaml"

        if not config_path.exists():
            # Use default config
            self._config = ProjectConfig()
            return self._config

        with open(config_path) as f:
            data = yaml.safe_load(f)

        # Convert to ProjectConfig
        project_data = data.get("project", {})
        patterns_data = data.get("patterns", {})
        data_data = data.get("data", {})
        output_data = data.get("output", {})
        validation_data = data.get("validation", {})

        self._config = ProjectConfig(
            name=project_data.get("name", "synth-project"),
            type=project_data.get("type", "tabular"),
            created=project_data.get("created", ""),
            patterns_directory=patterns_data.get("directory", "patterns"),
            patterns_format=patterns_data.get("format", "json"),
            data_directory=data_data.get("directory", "data"),
            supported_formats=data_data.get("supported_formats", ["csv", "excel", "json"]),
            output_directory=output_data.get("directory", "output"),
            default_format=output_data.get("default_format", "csv"),
            validation_enabled=validation_data.get("enabled", True),
            quality_threshold=validation_data.get("quality_threshold", 0.85),
        )

        return self._config

    def set_project_root(self, path: Path) -> None:
        """Set project root directory."""
        self._project_root = path


# Global settings instance
settings = Settings()


__all__ = ["ProjectConfig", "Settings", "settings"]
