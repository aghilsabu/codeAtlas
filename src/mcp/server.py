"""MCP Server - FastMCP implementation"""

import logging
from fastmcp import FastMCP

logger = logging.getLogger("codeatlas.mcp")

mcp = FastMCP("CodeAtlas")

from . import tools  # noqa: F401, E402


def run_server():
    logger.info("Starting CodeAtlas MCP Server...")
    mcp.run()


if __name__ == "__main__":
    run_server()
