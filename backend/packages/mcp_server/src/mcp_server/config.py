from papermes_shared.config import BaseConfig
from pydantic import BaseModel


class TemplatesConfig(BaseModel):
    """Templates configuration"""

    autoescape: bool = False
    trim_blocks: bool = True
    lstrip_blocks: bool = True
    prompts_dir: str = "prompts"


class MCPServerConfig(BaseModel):
    name: str = "papermes-mcp-server"
    host: str = "localhost"
    port: int = 8100
    transport: str = "streamable-http"


class MCPConfig(BaseConfig):
    """MCP server configuration"""

    mcp_server: MCPServerConfig = MCPServerConfig()
    templates: TemplatesConfig = TemplatesConfig()


config = MCPConfig()
