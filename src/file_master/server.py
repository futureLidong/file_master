#!/usr/bin/env python3
"""
File Master - MCP Server

Main entry point for the file processing MCP server.
Registers all file processing plugins as MCP tools.
"""

import asyncio
import logging
import sys
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    Tool,
    TextContent,
    ErrorContent,
)

from .config import Config, config
from .plugins import PDFExtractPlugin

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("file_master")


class FileMasterServer:
    """MCP Server for file processing plugins."""
    
    def __init__(self, config: Config):
        self.config = config
        self.server = Server("file-master")
        
        # Initialize plugins
        self.pdf_plugin = PDFExtractPlugin(config)
        
        # Register handlers
        self.server.list_tools()(self.handle_list_tools)
        self.server.call_tool()(self.handle_call_tool)
    
    def get_all_tools(self) -> list[Tool]:
        """Get all tools from all plugins."""
        tools = []
        tools.extend(self.pdf_plugin.get_tools())
        return tools
    
    async def handle_list_tools(self) -> list[Tool]:
        """Handle list_tools request."""
        return self.get_all_tools()
    
    async def handle_call_tool(
        self,
        name: str,
        arguments: dict[str, Any] | None = None,
    ) -> CallToolResult:
        """Handle call_tool request."""
        logger.info(f"Calling tool: {name} with args: {arguments}")
        
        # Route to appropriate plugin
        if name.startswith("pdf_"):
            results = await self.pdf_plugin.handle_tool(name, arguments)
        else:
            results = [ErrorContent(type="text", text=f"Unknown tool: {name}")]
        
        # Check for errors
        has_error = any(isinstance(r, ErrorContent) for r in results)
        
        return CallToolResult(
            content=results,
            isError=has_error,
        )
    
    async def run(self):
        """Run the MCP server."""
        logger.info(f"Starting File Master MCP server (model: {self.config.model})")
        
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options(),
            )


def main():
    """Main entry point."""
    # Check API key
    if not config.api_key:
        print(
            "Error: DASHSCOPE_API_KEY environment variable not set.\n"
            "Please set it with:\n"
            "  export DASHSCOPE_API_KEY=your_api_key",
            file=sys.stderr,
        )
        sys.exit(1)
    
    logger.info(f"Configuration loaded: model={config.model}")
    
    # Run server
    server = FileMasterServer(config)
    asyncio.run(server.run())


if __name__ == "__main__":
    main()
