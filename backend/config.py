"""
Configuration module for Papermes backend.

Uses pydantic-settings to load configuration from config.yml with environment variable support.
"""

from pathlib import Path
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


class HostAPIConfig(BaseModel):
    """Host API server configuration"""

    host: str = "0.0.0.0"
    port: int = 8090
    reload: bool = True
    log_level: str = "info"


class MCPServerConfig(BaseModel):
    """MCP server configuration"""

    name: str = "papermes-mcp-server"
    host: str = "localhost"
    port: int = 8100
    transport: str = "streamable-http"


class FireflyConfig(BaseModel):
    """Firefly III service configuration"""

    host: Optional[str] = None
    access_token: Optional[str] = None
    timeout: float = 30.0


class OpenAIConfig(BaseModel):
    """OpenAI service configuration"""

    api_key: Optional[str] = None
    model: str = "gpt-4o"
    prompt_token_cost: float = 0.0000020
    completion_token_cost: float = 0.000008


class AppConfig(BaseModel):
    """Application configuration"""

    default_currency: str = "USD"
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_date_format: str = "%Y-%m-%d %H:%M:%S"


class TemplatesConfig(BaseModel):
    """Templates configuration"""

    autoescape: bool = False
    trim_blocks: bool = True
    lstrip_blocks: bool = True


class HTTPConfig(BaseModel):
    """HTTP client configuration"""

    timeout: float = 30.0
    ssl_verify: bool = True


class PathsConfig(BaseModel):
    """Paths configuration"""

    prompts_dir: str = "src/mcp_server/prompts"
    lib_dir: str = "src/lib"
    testdata_dir: str = "../testdata"


class Config(BaseSettings):
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
    )

    host_api: HostAPIConfig = Field(default_factory=HostAPIConfig)
    mcp_server: MCPServerConfig = Field(default_factory=MCPServerConfig)
    firefly: FireflyConfig = Field(default_factory=FireflyConfig)
    openai: OpenAIConfig = Field(default_factory=OpenAIConfig)
    app: AppConfig = Field(default_factory=AppConfig)
    templates: TemplatesConfig = Field(default_factory=TemplatesConfig)
    http: HTTPConfig = Field(default_factory=HTTPConfig)
    paths: PathsConfig = Field(default_factory=PathsConfig)

    def get_absolute_path(self, relative_path: str) -> Path:
        """Convert a relative path to absolute path from backend directory"""
        backend_dir = Path(__file__).parent
        return backend_dir / relative_path

    @property
    def prompts_dir_path(self) -> Path:
        """Get absolute path to prompts directory"""
        return self.get_absolute_path(self.paths.prompts_dir)

    @property
    def lib_dir_path(self) -> Path:
        """Get absolute path to lib directory"""
        return self.get_absolute_path(self.paths.lib_dir)

    @property
    def testdata_dir_path(self) -> Path:
        """Get absolute path to test data directory"""
        return self.get_absolute_path(self.paths.testdata_dir)

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
config = Config()


def get_config() -> Config:
    """Get the global configuration instance"""
    return config


def reload_config() -> Config:
    """Reload configuration from file"""
    global config
    config = Config()
    return config
