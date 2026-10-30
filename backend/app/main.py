import contextlib
import logging
import time

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

from .config import settings, startup_guard

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
startup_guard()

from .agent.live import voice_session  # noqa: E402
from .agent.tool_client import ToolClient, mcp_status  # noqa: E402
from .mcp_server import mcp_asgi, session_manager  # noqa: E402
from .routers import api, internal  # noqa: E402
from .toolkit.registry import TOOLS  # noqa: E402

log = logging.getLogger("main")


@contextlib.asynccontextmanager
async def lifespan(app):
    async with session_manager.run():
        log.info("WeaveWed MCP server ready at /mcp/ with %d tools", len(TOOLS))
        yield


app = FastAPI(title="WeaveTwo API", version="2.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=settings.origins, allow_origin_regex=r"https?://.*", allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])
app.include_router(api.router)
app.include_router(internal.router)
app.mount("/mcp", mcp_asgi)


@app.get("/health")
@app.get("/healthz")
@app.get("/api/health")
async def healthz(deep: bool = False):
    out = {"ok": True, "env": settings.APP_ENV, "tools": len(TOOLS), "mcp": mcp_status()}
    if not deep:
        return out
    checks = {}

    async def check(name, coro):
        t0 = time.perf_counter()
        try:
            r = await coro
            checks[name] = {"ok": True, "ms": round((time.perf_counter() - t0) * 1000), "detail": r}
        except Exception as e:  # noqa
            checks[name] = {"ok": False, "error": str(e)[:300]}
            out["ok"] = False

    from .db import db
    from .services import qloo, taste_intel
    from .core.llm import gen_json

    async def fs():
        await db.document("health/ping").set({"t": time.time()})
        return "write ok"

    async def ql():
        r = await qloo.search("Arijit Singh", [qloo.ARTIST], take=3)
        return [x["name"] for x in r]

    async def gm():
        return await gen_json("Reply with ok=true", {"type": "OBJECT", "properties": {"ok": {"type": "BOOLEAN"}}, "required": ["ok"]})

    async def mcp():
        async with ToolClient("healthcheck", "health") as tc:
            specs = await tc.list_tools()
            return {"transport": tc.transport, "tools": len(specs)}

    async def ti():
        r = await taste_intel.resolve("Arijit Singh", "music", "entity", "singer")
        return {"status": r["status"], "name": r.get("name"), "category": r["category"]}

    for n, c in [("firestore", fs()), ("qloo", ql()), ("gemini", gm()), ("mcp", mcp()), ("taste_intel", ti())]:
        await check(n, c)
    out["checks"] = checks
    return out


@app.websocket("/ws/voice")
async def ws_voice(ws: WebSocket):
    origin = (ws.headers.get("origin") or "").rstrip("/")
    if origin and "*" not in settings.origins and origin not in settings.origins:
        await ws.close(code=4403)
        return
    await voice_session(ws)


import os
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

dist_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "dist")
if not os.path.isdir(dist_dir):
    dist_dir = os.path.join(os.getcwd(), "dist")

if os.path.isdir(dist_dir):
    assets_dir = os.path.join(dist_dir, "assets")
    if os.path.isdir(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")
    img_dir = os.path.join(dist_dir, "img")
    if os.path.isdir(img_dir):
        app.mount("/img", StaticFiles(directory=img_dir), name="img")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        target = os.path.join(dist_dir, full_path)
        if full_path and os.path.isfile(target):
            return FileResponse(target)
        index_file = os.path.join(dist_dir, "index.html")
        if os.path.isfile(index_file):
            return FileResponse(index_file)
        return {"error": "Not found"}

