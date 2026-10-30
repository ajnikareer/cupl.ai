"""cupl toolkit registry — the single source of truth for every product capability.

Exposed to the agent through the cupl MCP server (app/mcp_server.py) and callable in-process as a fallback.
Every call goes through execute(): load state -> mode gate -> JSON-schema validation -> handler -> widget ids ->
director guidance (_next). The gate lives HERE, so no client (text agent, voice agent, external MCP client)
can plan without an event space or read a partner's private tastes."""
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable

import jsonschema

from ..db import new_id
from ..services import state

log = logging.getLogger("toolkit")

GUIDE, SETUP, PLANNER = "guide", "setup", "planner"
ALL = {GUIDE, SETUP, PLANNER}
SPACE = {SETUP, PLANNER}


@dataclass
class Tool:
    name: str
    group: str
    description: str
    params: dict
    handler: Callable[["Ctx", dict], Awaitable[dict]]
    modes: set
    mutates: bool = False
    slow: bool = False


@dataclass
class Ctx:
    uid: str
    snap: state.Snapshot
    channel: str = "text"
    extra: dict = field(default_factory=dict)

    @property
    def user(self):
        return self.snap.user

    @property
    def space(self):
        return self.snap.space


TOOLS: dict[str, Tool] = {}


def obj(props: dict, required: list | None = None) -> dict:
    return {"type": "object", "properties": props, "required": required or [], "additionalProperties": False}


def tool(name: str, group: str, description: str, params: dict | None = None, modes=ALL, mutates=False, slow=False):
    def deco(fn):
        TOOLS[name] = Tool(name, group, description.strip(), params or obj({}), fn, set(modes), mutates, slow)
        return fn
    return deco


def describe(name: str) -> str:
    t = TOOLS[name]
    tag = f"[{t.group}]" + (" [slow: say something warm BEFORE calling]" if t.slow else "")
    return f"{tag} {t.description}"


def list_specs() -> list[dict]:
    return [{"name": t.name, "description": describe(t.name), "inputSchema": t.params} for t in TOOLS.values()]


def _coerce(args: dict, schema: dict) -> dict:
    """LLMs often send '25,00,000' or '300' as strings — coerce to the schema's numeric types before validating."""
    props = schema.get("properties", {})
    for k, v in list(args.items()):
        t = props.get(k, {}).get("type")
        if t in ("number", "integer") and isinstance(v, str):
            try:
                n = float(v.replace(",", "").replace("₹", "").strip())
                args[k] = int(n) if t == "integer" else n
            except ValueError:
                pass
        elif t == "array" and isinstance(v, str):
            args[k] = [x.strip() for x in v.split(",") if x.strip()]
    return args


async def execute(name: str, args: dict | None, uid: str, channel: str = "text") -> dict:
    t0 = time.perf_counter()
    t = TOOLS.get(name)
    if not t:
        return {"ok": False, "error": f"Unknown tool '{name}'."}
    args = _coerce({k: v for k, v in (args or {}).items() if v is not None}, t.params)
    try:
        jsonschema.validate(args, t.params)
    except jsonschema.ValidationError as e:
        return {"ok": False, "error": f"Invalid arguments for {name}: {e.message}. Fix and retry."}
    snap = await state.load(uid, with_episodes=False)
    if snap.mode not in t.modes:
        hint = ("There is no active event space yet — create one first with create_event."
                if snap.mode == GUIDE else f"First complete the event details: {snap.space['missing_fields']}.")
        return {"ok": False, "error": f"'{name}' isn't available right now. {hint}",
                "_next": {"stage": snap.next.get("stage"), "goal": snap.next.get("goal")}}
    ctx = Ctx(uid=uid, snap=snap, channel=channel)
    try:
        result = await t.handler(ctx, args) or {}
    except Exception as e:  # noqa
        log.exception("tool %s failed", name)
        from ..services.qloo import QlooError
        msg = ("The taste-intelligence service is unavailable right now; tell the user kindly and offer to retry shortly."
               if isinstance(e, QlooError) else f"{name} failed: {str(e)[:200]}")
        return {"ok": False, "error": msg}
    result.setdefault("ok", True)
    for w in ([result["widget"]] if result.get("widget") else []) + result.get("widgets", []):
        w.setdefault("id", new_id("w"))
    if t.mutates:
        snap2 = await state.load(uid, with_episodes=False)
        result["_next"] = {"mode": snap2.mode, "stage": snap2.next.get("stage"), "goal": snap2.next.get("goal")}
    log.info("tool %s uid=%s %.0fms ok=%s", name, uid[:6], (time.perf_counter() - t0) * 1000, result.get("ok"))
    return result
