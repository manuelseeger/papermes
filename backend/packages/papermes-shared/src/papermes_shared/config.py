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
    access_token: Optional[SecretStr] = None
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
        def find_config_files(filename: str):
            """Find config files (YAML or .env) following the same hierarchy logic."""
            config_files = []
            current_dir = Path.cwd()

            # Find root backend file
            backend_config = None

            # Check if we're already in backend directory
            if (current_dir / filename).exists() and current_dir.name == "backend":
                backend_config = current_dir / filename
            else:
                # Look for backend directory in parents
                for parent in current_dir.parents:
                    backend_dir = parent / "backend"
                    if backend_dir.exists() and (backend_dir / filename).exists():
                        backend_config = backend_dir / filename
                        break

            if backend_config:
                config_files.append(str(backend_config))

            # Find package-specific file
            search_dir = current_dir
            package_config = None

            # First, try current directory and parents
            while search_dir != search_dir.parent:
                config_file = search_dir / filename
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
                    for package_path in packages_dir.iterdir():
                        if package_path.is_dir():
                            package_config_file = package_path / filename
                            if package_config_file.exists():
                                package_config = package_config_file
                                break

            if package_config:
                config_files.append(str(package_config))

            return config_files

        # Build YAML config files
        yaml_files = find_config_files("config.yml")

        # Build .env files
        env_files = find_config_files(".env")

        # Create sources
        yaml_source = (
            YamlConfigSettingsSource(settings_cls, yaml_file=yaml_files)
            if yaml_files
            else None
        )
        dotenv_source = (
            DotEnvSettingsSource(settings_cls, env_file=env_files)
            if env_files
            else dotenv_settings
        )

        return (
            init_settings,
            env_settings,
            dotenv_source,
            file_secret_settings,
            yaml_source,
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
