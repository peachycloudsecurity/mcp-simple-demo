#!/usr/bin/env python3
"""
MCP-compatible tool server using the registry pattern.

This server exposes registered tools via the MCP protocol over STDIO,
using a centralized registry for tool discovery and execution.
"""

import asyncio
import json
import logging
import sys
import os
from typing import Any, Dict

# Ensure parent directory is in path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from src.config import get_config
from src.tools import registry

# Configure logging
cfg = get_config()
logging.basicConfig(
    level=getattr(logging, cfg.log_level),
    format='[%(levelname)s] %(name)s: %(message)s'
)
log = logging.getLogger("server")


class ToolServer:
    """
    MCP server that delegates tool execution to the registry.
    
    Uses a centralized registry pattern instead of hardcoded dispatch,
    making the server agnostic to specific tool implementations.
    """
    
    def __init__(self):
        self._mcp = Server(cfg.server.identifier)
        self._register_handlers()
    
    def _register_handlers(self):
        """Wire up MCP protocol handlers."""
        
        @self._mcp.list_tools()
        async def handle_list_tools():
            """Dynamically generate tool list from registry."""
            log.info("Client requested tool listing")
            definitions = registry.get_mcp_definitions()
            return [
                Tool(
                    name=d["name"],
                    description=d["description"],
                    inputSchema=d["inputSchema"]
                )
                for d in definitions
            ]
        
        @self._mcp.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]):
            """Delegate tool execution to registry."""
            log.info(f"Executing tool: {name}")
            result = registry.execute(name, arguments)
            log.debug(f"Tool result: {result}")
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
    
    async def serve(self):
        """Start the STDIO server loop."""
        log.info(f"Server '{cfg.server.identifier}' starting...")
        async with stdio_server() as streams:
            log.info("Client connected")
            await self._mcp.run(
                streams[0],
                streams[1],
                self._mcp.create_initialization_options()
            )
            log.info("Client disconnected")


async def main():
    """Entry point for standalone server execution."""
    server = ToolServer()
    await server.serve()


if __name__ == "__main__":
    asyncio.run(main())
