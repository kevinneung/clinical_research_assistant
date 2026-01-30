"""Application configuration management."""

import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any

from dotenv import load_dotenv


@dataclass
class AppConfig:
    """Application configuration."""

    # Paths
    app_data_dir: Path = field(default_factory=lambda: Path.home() / ".clinical_research_assistant")
    workspaces_dir: Path = field(default_factory=lambda: Path.home() / ".clinical_research_assistant" / "workspaces")
    database_path: Path = field(default_factory=lambda: Path.home() / ".clinical_research_assistant" / "database.db")

    # API Keys
    anthropic_api_key: str = ""
    brave_api_key: str = ""

    # Model settings
    default_model: str = "anthropic:claude-sonnet-4-20250514"

    # UI settings
    window_width: int = 1200
    window_height: int = 800

    # Logging
    log_level: str = "INFO"
    log_file: Path | None = None

    def __post_init__(self):
        """Ensure directories exist after initialization."""
        self.app_data_dir.mkdir(parents=True, exist_ok=True)
        self.workspaces_dir.mkdir(parents=True, exist_ok=True)

    @classmethod
    def from_env(cls) -> "AppConfig":
        """Create config from environment variables.

        Returns:
            AppConfig instance populated from environment.
        """
        load_dotenv()

        config = cls()

        # Override with environment variables if set
        if app_data := os.environ.get("CRA_APP_DATA_DIR"):
            config.app_data_dir = Path(app_data)
            config.workspaces_dir = config.app_data_dir / "workspaces"
            config.database_path = config.app_data_dir / "database.db"

        if workspaces := os.environ.get("CRA_WORKSPACES_DIR"):
            config.workspaces_dir = Path(workspaces)

        if db_path := os.environ.get("CRA_DATABASE_PATH"):
            config.database_path = Path(db_path)

        config.anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        config.brave_api_key = os.environ.get("BRAVE_API_KEY", "")

        if model := os.environ.get("CRA_DEFAULT_MODEL"):
            config.default_model = model

        if log_level := os.environ.get("CRA_LOG_LEVEL"):
            config.log_level = log_level.upper()

        if log_file := os.environ.get("CRA_LOG_FILE"):
            config.log_file = Path(log_file)

        # Ensure directories exist
        config.__post_init__()

        return config

    def validate(self) -> list[str]:
        """Validate the configuration.

        Returns:
            List of validation error messages (empty if valid).
        """
        errors = []

        if not self.anthropic_api_key:
            errors.append("ANTHROPIC_API_KEY is not set")

        if not self.app_data_dir.exists():
            errors.append(f"App data directory does not exist: {self.app_data_dir}")

        return errors

    def to_dict(self) -> dict[str, Any]:
        """Convert config to dictionary.

        Returns:
            Dictionary representation of config (excluding sensitive data).
        """
        return {
            "app_data_dir": str(self.app_data_dir),
            "workspaces_dir": str(self.workspaces_dir),
            "database_path": str(self.database_path),
            "default_model": self.default_model,
            "window_width": self.window_width,
            "window_height": self.window_height,
            "log_level": self.log_level,
            "log_file": str(self.log_file) if self.log_file else None,
            "has_anthropic_key": bool(self.anthropic_api_key),
            "has_brave_key": bool(self.brave_api_key),
        }


# Global config instance
_config: AppConfig | None = None


def load_config() -> AppConfig:
    """Load or return the global configuration.

    Returns:
        The application configuration instance.
    """
    global _config
    if _config is None:
        _config = AppConfig.from_env()
    return _config


def get_config() -> AppConfig:
    """Get the current configuration.

    Returns:
        The application configuration instance.

    Raises:
        RuntimeError: If config has not been loaded.
    """
    if _config is None:
        return load_config()
    return _config
