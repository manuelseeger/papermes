"""
Configuration module for Papermes backend.

Uses pydantic-settings to load configuration from config.yml with environment variable support.
Supports hierarchical configuration loading from root and package-specific config files.
"""

from pathlib import Path
from typing import Optional, Tuple, Type

from pydantic import BaseModel, Field, SecretStr
from pydantic_settings import (
    BaseSettings,
    DotEnvSettingsSource,
    EnvSettingsSource,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    YamlConfigSettingsSource,
)


class OpenAIConfig(BaseModel):
    """OpenAI service configuration"""

    api_key: SecretStr = ""
    model: str = "gpt-4.1"
    prompt_token_cost: float = 0.0000020
    completion_token_cost: float = 0.000008


class AppConfig(BaseModel):
    """Application configuration"""

    default_currency: str = "USD"
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_date_format: str = "%Y-%m-%d %H:%M:%S"


class FireflyConfig(BaseModel):
    """Firefly service configuration"""

    host: str = "http://localhost:8080"
    api_key: Optional[str] = None
    timeout: int = 30  # seconds


class BaseConfig(BaseSettings):
    """
    Main configuration class for Papermes backend.

    Loads configuration from config.yml with environment variable substitution.
    Environment variables can override any configuration value using dot notation.

    Examples:
        - PAPERMES_HOST_API__PORT=8091 overrides host_api.port
        - PAPERMES_FIREFLY__HOST=http://localhost:8080 overrides firefly.host
    """

    model_config = SettingsConfigDict(
        env_prefix="PAPERMES_",
        env_nested_delimiter="__",
        case_sensitive=False,
        yaml_file="config.yml",
        yaml_file_encoding="utf-8",
        extra="allow",  # Allow extra fields in config
    )

    app: AppConfig = Field(default_factory=AppConfig)
    openai: OpenAIConfig = Field(default_factory=OpenAIConfig)
    firefly: FireflyConfig = Field(default_factory=FireflyConfig)

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: EnvSettingsSource,
        dotenv_settings: DotEnvSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> Tuple[PydanticBaseSettingsSource, ...]:
        # Build array of config file paths for hierarchical loading
        config_files = []

        current_dir = Path.cwd()

        # Find root backend/config.yml
        backend_config = None

        # Check if we're already in backend directory
        if (current_dir / "config.yml").exists() and current_dir.name == "backend":
            backend_config = current_dir / "config.yml"
        else:
            # Look for backend directory in parents
            for parent in current_dir.parents:
                backend_dir = parent / "backend"
                if backend_dir.exists() and (backend_dir / "config.yml").exists():
                    backend_config = backend_dir / "config.yml"
                    break

        if backend_config:
            config_files.append(str(backend_config))

        # Find package-specific config.yml
        # Look in current directory first, then parents (but not the backend config we already found)
        # Also look in packages subdirectories if we're in backend root
        search_dir = current_dir
        package_config = None

        # First, try current directory and parents
        while search_dir != search_dir.parent:
            config_file = search_dir / "config.yml"
            if (
                config_file.exists()
                and config_file != backend_config
                and str(config_file) not in config_files
            ):
                package_config = config_file
                break
            search_dir = search_dir.parent

        # If we're in backend root and didn't find a package config yet,
        # look for package configs in packages/ subdirectory
        if not package_config and current_dir.name == "backend":
            packages_dir = current_dir / "packages"
            if packages_dir.exists():
                # Look for any package config files and use the first one found
                # (or could be made more sophisticated to handle multiple packages)
                for package_path in packages_dir.iterdir():
                    if package_path.is_dir():
                        package_config_file = package_path / "config.yml"
                        if package_config_file.exists():
                            package_config = package_config_file
                            break

        if package_config:
            config_files.append(str(package_config))

        # Return with package config overriding backend config
        # (no need to reverse since we're adding them in the correct order now)
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            file_secret_settings,
            YamlConfigSettingsSource(settings_cls, yaml_file=config_files),
        )


# Global configuration instance
config = BaseConfig()


def get_config() -> BaseConfig:
    """Get the global configuration instance"""
    return config


def reload_config() -> BaseConfig:
    """Reload configuration from file"""
    global config
    config = BaseConfig()
    return config
