"""
MCP Server package for papermes document management system.

This package provides Model Context Protocol (MCP) server functionality
for receipt analysis and document management integration.
"""

from .client import main as run_client
from .server import run_server as run_server

__version__ = "0.1.0"
__all__ = ["run_client", "run_server"]
