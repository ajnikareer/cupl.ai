"""cupl MCP server — publishes every product capability (QLOO taste intelligence, events, plans, memory,
companion, conversational UI) over MCP Streamable HTTP at /mcp/.

Auth:
  * Internal (the cupl agent):  Authorization: Bearer <MCP_INTERNAL_TOKEN>  +  X-WW-UID: <uid>  (+ X-WW-Channel)
  * External MCP clients (VS Code, other agents): Authorization: Bearer <Firebase ID token of the user>
Every call is executed by toolkit.registry.execute (mode gate, validation, privacy) on behalf of that user."""
import hmac
import json
import logging

import mcp.types as mt
from mcp.server.lowlevel import Server
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager

from .config import settings
from .toolkit import tools as _tools  # noqa: F401  (registers tools)
from .toolkit.registry import execute, list_specs

log = logging.getLogger("mcp")
server = Server("cupl")


@server.list_tools()
async def _list_tools() -> list[mt.Tool]:
    return [mt.Tool(name=s["name"], description=s["description"], inputSchema=s["inputSchema"]) for s in list_specs()]


async def _uid_from_headers(headers) -> tuple[str, str]:
    auth = headers.get("authorization", "")
    token = auth[7:] if auth.lower().startswith("bearer ") else ""
    if token and settings.MCP_INTERNAL_TOKEN and hmac.compare_digest(token, settings.MCP_INTERNAL_TOKEN):
        uid = headers.get("x-ww-uid")
        if not uid:
            raise PermissionError("X-WW-UID header required with the internal token")
        return uid, headers.get("x-ww-channel", "text")
    from .auth import verify_token
    user = await verify_token(token)
    return user["uid"], "mcp"


@server.call_tool(validate_input=False)
async def _call_tool(name: str, arguments: dict) -> list[mt.TextContent]:
    req = server.request_context.request
    if req is None:
        raise PermissionError("No HTTP request context")
    uid, channel = await _uid_from_headers(req.headers)
    result = await execute(name, arguments or {}, uid, channel)
    return [mt.TextContent(type="text", text=json.dumps(result, default=str))]


session_manager = StreamableHTTPSessionManager(app=server, json_response=True, stateless=True)


async def mcp_asgi(scope, receive, send):
    if scope["type"] != "http":
        return
    headers = {k.decode().lower(): v.decode() for k, v in scope.get("headers", [])}
    if not headers.get("authorization", "").lower().startswith("bearer "):
        body = b'{"error":"unauthorized"}'
        await send({"type": "http.response.start", "status": 401,
                    "headers": [(b"content-type", b"application/json"), (b"content-length", str(len(body)).encode())]})
        await send({"type": "http.response.body", "body": body})
        return
    await session_manager.handle_request(scope, receive, send)
