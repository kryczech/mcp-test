from app import mcp

@mcp.tool()
def pong(message: str = "pong") -> str:
    return f"ping: {message}"