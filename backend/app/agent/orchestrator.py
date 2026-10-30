"""Text agent: streaming Gemini + MCP tools, up to 8 agentic hops per turn."""
import asyncio
import logging
import time

from google.genai import types

from ..config import settings
from ..core.llm import _transient, client, mark_thinking_unsupported, thinking_config
from ..services import learning, state
from ..services.memory import add_turn, recent_turns
from ..toolkit import widgets as widget_svc
from ..toolkit.registry import TOOLS
from .context import build_system
from .tool_client import ToolClient, declarations, split_widgets

log = logging.getLogger("agent")
MAX_HOPS = 8
FRIENDLY_STATUS = {
    "remember_tastes": "Getting to know your taste…", "show_taste_picker": "Finding suggestions you'll love…",
    "build_plan": "Starting to weave your plan…", "revise_plan": "Updating your plan…", "get_couple_dna": "Reading your Couple DNA…",
    "create_surprise": "Planning something secret…", "qloo_recommend": "Matching to both your tastes…",
    "create_event": "Creating your event space…", "update_event": "Saving that…",
    "save_cultural_roots": "Saving your cultural roots…",
}


def history_contents(turns: list[dict]) -> list[types.Content]:
    out: list[types.Content] = []
    for t in turns:
        text = t.get("text") or ""
        w = t.get("widget")
        if w and w.get("kind") not in (None, "refresh"):
            text = (text + "\n" if text else "") + f"[showed {w['kind']} card: {w.get('title', '')}" + (
                f" — answered: {w.get('values')}" if w.get("done") else "") + "]"
        if not text.strip():
            continue
        role = "model" if t["role"] == "agent" else "user"
        if out and out[-1].role == role:
            out[-1].parts.append(types.Part(text=text))
        else:
            out.append(types.Content(role=role, parts=[types.Part(text=text)]))
    while out and out[0].role != "user":
        out.pop(0)
    return out


def allowed_for(mode: str) -> set:
    return {n for n, t in TOOLS.items() if mode in t.modes}


async def _post_turn(uid: str, snap: state.Snapshot, count: int):
    await state.mark_stage_seen(uid, (snap.next or {}).get("stage"))
    if count % max(1, settings.LEARN_EVERY_N_TURNS) == 0:
        learning.schedule(uid)


async def run_turn(uid: str, text: str | None, widget_response: dict | None, emit):
    t_start = time.perf_counter()
    try:
        if widget_response:
            text = await widget_svc.apply(uid, widget_response)
            await emit({"type": "refresh"})
        else:
            await state.bump_taste_streak(uid, reset=True)
        text = (text or "").strip()[:4000]
        if not text:
            await emit({"type": "done"})
            return
        history = history_contents(await recent_turns(uid, 24))
        await add_turn(uid, "user", text)
        snap = await state.load(uid, query=text)
        contents = history + [types.Content(role="user", parts=[types.Part(text=text)])]
        model = settings.GEMINI_AGENT_MODEL
        count = 0
        async with ToolClient(uid, "text") as tc:
            specs = await tc.list_tools()
            for hop in range(MAX_HOPS):
                cfg = types.GenerateContentConfig(
                    system_instruction=build_system(snap), temperature=0.75, max_output_tokens=1500,
                    tools=declarations(specs, allowed_for(snap.mode)),
                    thinking_config=thinking_config(model, settings.AGENT_THINKING_BUDGET))
                parts, calls, seg = [], [], ""
                for attempt in range(3):
                    try:
                        stream = await client.aio.models.generate_content_stream(model=model, contents=contents, config=cfg)
                        async for chunk in stream:
                            cand = (chunk.candidates or [None])[0]
                            for p in ((cand.content.parts if cand and cand.content else None) or []):
                                parts.append(p)
                                if p.function_call:
                                    calls.append(p.function_call)
                                elif p.text and not getattr(p, "thought", False):
                                    if not seg:
                                        log.info("first token %.0fms", (time.perf_counter() - t_start) * 1000)
                                    seg += p.text
                                    await emit({"type": "delta", "text": p.text})
                        break
                    except Exception as e:  # noqa
                        if mark_thinking_unsupported(model, e):
                            cfg.thinking_config = None
                            continue
                        if attempt < 2 and not parts and _transient(e):
                            await asyncio.sleep(1.2 * (2 ** attempt))
                            continue
                        raise
                if seg.strip():
                    count = await add_turn(uid, "agent", seg.strip())
                    await emit({"type": "segment_end"})
                if not calls:
                    break
                contents.append(types.Content(role="model", parts=parts))
                responses, dirty = [], False
                for fc in calls:
                    await emit({"type": "status", "text": FRIENDLY_STATUS.get(fc.name, "Working on it…")})
                    try:
                        result = await tc.call(fc.name, dict(fc.args or {}))
                    except Exception as tool_err:
                        log.warning("Tool %s execution error: %s", fc.name, tool_err)
                        result = {"error": f"Tool error: {tool_err}"}
                    result, widgets = split_widgets(result)
                    for w in widgets:
                        if w.get("kind") == "refresh":
                            continue
                        await emit({"type": "widget", "widget": w})
                        count = await add_turn(uid, "agent", "", widget=w)
                    if any(w.get("kind") == "refresh" for w in widgets) or "_next" in result:
                        await emit({"type": "refresh"})
                        dirty = True
                    responses.append(types.Part.from_function_response(name=fc.name, response={"result": result}))
                contents.append(types.Content(role="user", parts=responses))
                if dirty:
                    snap = await state.load(uid, query=text, with_episodes=False)
            else:
                await emit({"type": "delta", "text": "Done! Anything you'd like to tweak? 😊"})
        await emit({"type": "done"})
        log.info("turn done %.0fms (transport=%s)", (time.perf_counter() - t_start) * 1000, tc.transport)
        await _post_turn(uid, snap, count)
    except Exception as e:  # noqa
        log.exception("turn failed")
        await emit({"type": "error", "message": "Sorry — something went wrong on my side. Could you say that again?"})
        await emit({"type": "done"})
