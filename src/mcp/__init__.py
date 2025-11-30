"""MCP Server"""


def create_mcp_server():
    from .server import mcp
    return mcp


def run_server():
    from .server import run_server as _run
    _run()


__all__ = ["create_mcp_server", "run_server"]
