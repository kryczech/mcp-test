from app import mcp

@mcp.tool()
def ping(message: str = "ping") -> str:
    return f"pong: {message}"