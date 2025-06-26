#!/usr/bin/env python3
"""
MCP Server Package Entry Point

This allows running the MCP server with: python -m mcp_server
"""

from .server import run_server

if __name__ == "__main__":
    run_server()
