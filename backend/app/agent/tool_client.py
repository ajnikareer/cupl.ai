"""The agent's connection to the WeaveWed MCP server (Streamable HTTP), with transparent in-process fallback.

Tools are discovered from the MCP server (list_tools) and converted to Gemini function declarations.
Widgets returned by tools are split out for the UI; the model only sees a compact result."""
import contextlib
import json
import logging
import time

from google.genai import types

from ..config import settings
from ..toolkit import tools as _tools  # noqa: F401
from ..toolkit.registry import execute, list_specs

log = logging.getLogger("tool_client")
_tools_cache: tuple[float, list[dict]] | None = None
_mcp_healthy = True

GENAI_KEYS = {"type", "description", "enum", "items", "properties", "required", "format", "minimum", "maximum", "minItems", "maxItems"}


def to_genai_schema(s: dict) -> dict:
    """JSON Schema (MCP) -> Gemini OpenAPI-subset schema."""
    out = {}
    for k, v in s.items():
        if k not in GENAI_KEYS:
            continue
        if k == "type":
            out["type"] = str(v).upper()
        elif k == "properties":
            out["properties"] = {pk: to_genai_schema(pv) for pk, pv in v.items()}
        elif k == "items":
            out["items"] = to_genai_schema(v)
        elif k in ("minItems", "maxItems"):
            out["min_items" if k == "minItems" else "max_items"] = int(v)
        elif k == "required" and not v:
            continue
        else:
            out[k] = v
    if out.get("type") == "OBJECT" and not out.get("properties"):
        return {}
    return out


def declarations(specs: list[dict], allowed: set | None = None) -> list[types.Tool]:
    fns = []
    for s in specs:
        if allowed is not None and s["name"] not in allowed:
            continue
        params = to_genai_schema(s.get("inputSchema") or {})
        fns.append(types.FunctionDeclaration(name=s["name"], description=s["description"], parameters=params or None))
    return [types.Tool(function_declarations=fns)]


def split_widgets(result: dict) -> tuple[dict, list[dict]]:
    widgets = []
    if result.get("widget"):
        widgets.append(result.pop("widget"))
    widgets += result.pop("widgets", []) or []
    shown = [w["kind"] for w in widgets if w.get("kind") != "refresh"]
    if shown:
        result["shown_on_screen"] = shown
    return result, widgets


class ToolClient:
    """Use as `async with ToolClient(uid, channel) as tc:` in the SAME task that will close it."""

    def __init__(self, uid: str, channel: str = "text"):
        self.uid, self.channel = uid, channel
        self.session = None
        self._stack = contextlib.AsyncExitStack()
        self.transport = "inprocess"

    async def __aenter__(self):
        global _mcp_healthy
        if settings.AGENT_TOOL_TRANSPORT == "mcp":
            try:
                from mcp import ClientSession
                from mcp.client.streamable_http import streamablehttp_client
                headers = {"Authorization": f"Bearer {settings.MCP_INTERNAL_TOKEN}", "X-WW-UID": self.uid,
                           "X-WW-Channel": self.channel}
                read, write, _ = await self._stack.enter_async_context(
                    streamablehttp_client(settings.mcp_url, headers=headers, timeout=30, sse_read_timeout=120))
                self.session = await self._stack.enter_async_context(ClientSession(read, write))
                await self.session.initialize()
                self.transport = "mcp"
                _mcp_healthy = True
            except Exception as e:  # noqa
                _mcp_healthy = False
                log.warning("MCP connect failed (%s); using in-process toolkit", e)
                await self._safe_close()
        return self

    async def _safe_close(self):
        try:
            await self._stack.aclose()
        except BaseException as e:  # noqa
            log.debug("close: %s", e)
        self._stack = contextlib.AsyncExitStack()
        self.session = None

    async def __aexit__(self, *exc):
        await self._safe_close()

    async def list_tools(self) -> list[dict]:
        global _tools_cache
        if _tools_cache and _tools_cache[0] > time.time():
            return _tools_cache[1]
        specs = None
        if self.session:
            try:
                res = await self.session.list_tools()
                specs = [{"name": t.name, "description": t.description or "", "inputSchema": t.inputSchema} for t in res.tools]
            except Exception as e:  # noqa
                log.warning("MCP list_tools failed: %s", e)
        specs = specs or list_specs()
        _tools_cache = (time.time() + 300, specs)
        return specs

    async def call(self, name: str, args: dict) -> dict:
        t0 = time.perf_counter()
        if self.session:
            try:
                res = await self.session.call_tool(name, args)
                text = "".join(getattr(c, "text", "") for c in res.content)
                out = json.loads(text) if text else {"ok": not res.isError}
                if res.isError and isinstance(out, dict):
                    out.setdefault("ok", False)
                log.info("mcp %s %.0fms", name, (time.perf_counter() - t0) * 1000)
                return out if isinstance(out, dict) else {"result": out}
            except Exception as e:  # noqa
                log.warning("MCP call %s failed (%s); falling back in-process", name, e)
        return await execute(name, args, self.uid, self.channel)


def mcp_status() -> dict:
    return {"transport": settings.AGENT_TOOL_TRANSPORT, "url": settings.mcp_url, "healthy": _mcp_healthy}
