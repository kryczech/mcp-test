# app.py
from contextlib import asynccontextmanager
from starlette.applications import Starlette
from starlette.routing import Mount
from mcp_instance import mcp

# Import the tools package; its __init__ auto-loads all tool files
import tools  # noqa: F401

mcp_app = mcp.streamable_http_app()

@asynccontextmanager
async def lifespan(app):
    async with mcp.session_manager.run():
        yield

app = Starlette(lifespan=lifespan, routes=[Mount("/", app=mcp_app)])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000)
