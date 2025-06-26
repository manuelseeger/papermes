"""
Configuration module for Papermes backend.

Uses pydantic-settings to load configuration from config.yml with environment variable support.
"""

from typing import Optional, Tuple, Type

from pydantic import BaseModel, Field
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

    api_key: Optional[str] = None
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
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            file_secret_settings,
            YamlConfigSettingsSource(settings_cls),
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
