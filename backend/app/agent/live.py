"""Voice agent: browser <-> FastAPI WebSocket <-> Gemini Live API (native audio), tools via the WeaveWed MCP server.

Human-like behaviour:
  * native-audio model, chosen voice, affective dialog + proactive audio when supported (auto-fallback if not)
  * tuned turn-taking (quick barge-in, patient end-of-speech so people can pause to think)
  * interruptions flush playback instantly on the client
  * long jobs (plan builds) run in background; when ready the agent is nudged at the next quiet moment
  * session resumption + context-window compression for long calls; transparent reconnect on go_away
"""
import asyncio
import contextlib
import json
import logging
import time

from fastapi import WebSocket, WebSocketDisconnect
from google.genai import types

from ..auth import verify_token
from ..config import settings
from ..core.llm import client
from ..services import events, learning, state
from ..services.memory import add_turn
from ..toolkit import widgets as widget_svc
from .context import build_system
from .tool_client import ToolClient, declarations, split_widgets

log = logging.getLogger("voice")
OPTIONAL = ["enable_affective_dialog", "proactivity", "realtime_input_config", "context_window_compression",
            "session_resumption"]
_disabled: set[str] = set()   # features the deployed model rejected; remembered for the process lifetime


def _config(system: str, tools, handle: str | None, drop: set) -> types.LiveConnectConfig:
    speech = {"voice_config": types.VoiceConfig(prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=settings.LIVE_VOICE_NAME))}
    if settings.LIVE_LANGUAGE:
        speech["language_code"] = settings.LIVE_LANGUAGE
    cfg = {"response_modalities": [types.Modality.AUDIO],
           "system_instruction": types.Content(parts=[types.Part(text=system)]),
           "tools": tools,
           "speech_config": types.SpeechConfig(**speech),
           "input_audio_transcription": types.AudioTranscriptionConfig(),
           "output_audio_transcription": types.AudioTranscriptionConfig()}
    opt = {}
    if settings.LIVE_AFFECTIVE_DIALOG:
        opt["enable_affective_dialog"] = True
    if settings.LIVE_PROACTIVE_AUDIO:
        opt["proactivity"] = types.ProactivityConfig(proactive_audio=True)
    opt["realtime_input_config"] = types.RealtimeInputConfig(automatic_activity_detection=types.AutomaticActivityDetection(
        disabled=False,
        start_of_speech_sensitivity=getattr(types.StartSensitivity, f"START_SENSITIVITY_{settings.LIVE_START_SENSITIVITY.upper()}"),
        end_of_speech_sensitivity=getattr(types.EndSensitivity, f"END_SENSITIVITY_{settings.LIVE_END_SENSITIVITY.upper()}"),
        prefix_padding_ms=settings.LIVE_PREFIX_PADDING_MS, silence_duration_ms=settings.LIVE_SILENCE_MS))
    opt["context_window_compression"] = types.ContextWindowCompressionConfig(sliding_window=types.SlidingWindow())
    opt["session_resumption"] = types.SessionResumptionConfig(handle=handle) if handle else types.SessionResumptionConfig()
    for k, v in opt.items():
        if k not in drop and k not in _disabled:
            cfg[k] = v
    return types.LiveConnectConfig(**cfg)


class VS:
    def __init__(self):
        self.session = None
        self.handle: str | None = None
        self.speaking = False
        self.last_user = 0.0
        self.closed = asyncio.Event()
        self.ubuf = ""
        self.abuf = ""
        self.produced = False


async def voice_session(ws: WebSocket):
    await ws.accept()
    try:
        first = json.loads(await asyncio.wait_for(ws.receive_text(), timeout=15))
        user = await verify_token(first.get("token", ""))
    except Exception as e:  # noqa
        await ws.send_json({"type": "error", "message": f"auth failed: {e}"})
        await ws.close()
        return
    uid = user["uid"]
    vs = VS()

    async def emit(ev):
        try:
            await ws.send_json(ev)
        except Exception:  # noqa
            vs.closed.set()

    evq = events.subscribe(uid)
    try:
        async with ToolClient(uid, "voice") as tc:
            specs = await tc.list_tools()
            tools = declarations(specs)

            async def handle_tool_call(tool_call):
                outs = []
                for fc in tool_call.function_calls or []:
                    await emit({"type": "status", "text": "…"})
                    result = await tc.call(fc.name, dict(fc.args or {}))
                    result, widgets = split_widgets(result)
                    for w in widgets:
                        if w.get("kind") == "refresh":
                            await emit({"type": "refresh"})
                            continue
                        await emit({"type": "widget", "widget": w})
                        await add_turn(uid, "agent", "", widget=w, channel="voice")
                    if "_next" in result:
                        await emit({"type": "refresh"})
                    outs.append(types.FunctionResponse(id=fc.id, name=fc.name, response={"result": result}))
                if vs.session:
                    await vs.session.send_tool_response(function_responses=outs)

            async def flush_transcripts():
                if vs.ubuf.strip():
                    await add_turn(uid, "user", vs.ubuf.strip(), channel="voice")
                if vs.abuf.strip():
                    await add_turn(uid, "agent", vs.abuf.strip(), channel="voice")
                vs.ubuf = vs.abuf = ""

            async def downstream(session) -> str:
                while not vs.closed.is_set():
                    got = 0
                    async for resp in session.receive():
                        got += 1
                        vs.produced = True
                        if resp.session_resumption_update and resp.session_resumption_update.new_handle:
                            vs.handle = resp.session_resumption_update.new_handle
                        if resp.go_away is not None:
                            log.info("go_away received; resuming")
                            return "goaway"
                        if resp.tool_call:
                            await handle_tool_call(resp.tool_call)
                            continue
                        sc = resp.server_content
                        if not sc:
                            continue
                        if sc.interrupted:
                            vs.speaking = False
                            await emit({"type": "interrupted"})
                        if sc.input_transcription and sc.input_transcription.text:
                            vs.last_user = time.time()
                            vs.ubuf += sc.input_transcription.text
                            await emit({"type": "transcript", "role": "user", "text": sc.input_transcription.text})
                        if sc.output_transcription and sc.output_transcription.text:
                            vs.abuf += sc.output_transcription.text
                            await emit({"type": "transcript", "role": "agent", "text": sc.output_transcription.text})
                        if sc.model_turn:
                            for p in sc.model_turn.parts or []:
                                if p.inline_data and p.inline_data.data:
                                    vs.speaking = True
                                    try:
                                        await ws.send_bytes(p.inline_data.data)
                                    except Exception:  # noqa
                                        vs.closed.set()
                        if sc.turn_complete:
                            vs.speaking = False
                            await flush_transcripts()
                            await emit({"type": "turn_complete"})
                            asyncio.create_task(state.mark_stage_seen(uid))
                    if got == 0:
                        return "ended"
                return "closed"

            async def upstream():
                try:
                    while not vs.closed.is_set():
                        msg = await ws.receive()
                        if msg.get("type") == "websocket.disconnect":
                            break
                        s = vs.session
                        if msg.get("bytes"):
                            if s:
                                await s.send_realtime_input(audio=types.Blob(data=msg["bytes"], mime_type="audio/pcm;rate=16000"))
                            continue
                        if not msg.get("text"):
                            continue
                        data = json.loads(msg["text"])
                        typ = data.get("type")
                        if typ == "stop":
                            break
                        if typ == "text" and data.get("text") and s:
                            await add_turn(uid, "user", data["text"][:2000], channel="voice")
                            await s.send_client_content(turns=types.Content(role="user", parts=[types.Part(text=data["text"][:2000])]),
                                                        turn_complete=True)
                        if typ == "widget_response" and s:
                            t = await widget_svc.apply(uid, data)
                            await add_turn(uid, "user", t, channel="voice")
                            await emit({"type": "refresh"})
                            await s.send_client_content(turns=types.Content(role="user", parts=[types.Part(text=t)]), turn_complete=True)
                        if typ == "couple_mode" and s:
                            enabled = bool(data.get("enabled", False))
                            snap = await state.load(uid, with_episodes=False)
                            pname = (snap.partner or {}).get("name") or "your partner"
                            uname = (snap.user.get("name") or "You").split(" ")[0]
                            if enabled:
                                prompt = (
                                    f"[COUPLE MODE ACTIVATED] {uname} and {pname} are sitting together right now "
                                    "in front of the screen. Speak directly to BOTH of them as a couple. Use 'you two', 'both of you', "
                                    "ask for each partner's perspective, playfully bridge their tastes, and plan together. "
                                    f"Warmly greet {uname} and {pname} together right now."
                                )
                            else:
                                prompt = f"[INDIVIDUAL MODE] Returning to 1-on-1 mode with {uname}."
                            await s.send_client_content(turns=types.Content(role="user", parts=[types.Part(text=prompt)]), turn_complete=True)
                except (WebSocketDisconnect, RuntimeError):
                    pass
                except Exception:  # noqa
                    log.exception("upstream error")
                finally:
                    vs.closed.set()

            async def event_pump():
                while not vs.closed.is_set():
                    ev = await evq.get()
                    if ev.get("type") == "plan_ready":
                        secs = "; ".join(f"{s['title']}: {', '.join(s['top'])}" for s in ev["summary"]["sections"] if s.get("top"))
                        text = (f"[PLAN READY — system event, not said by the user] The '{ev.get('title')}' plan is ready"
                                + (f" (change: {ev['instruction']})" if ev.get("instruction") else "")
                                + f". Highlights: {secs}. At this natural pause, tell them warmly and briefly, then show ONE "
                                  "highlight with show_plan_section.")
                    elif ev.get("type") == "plan_failed":
                        text = "[SYSTEM EVENT] The plan build failed. Apologise briefly and offer to try again."
                    else:
                        continue
                    for _ in range(60):   # wait for a quiet moment (not speaking, user silent 1.5s), max 30s
                        if not vs.speaking and time.time() - vs.last_user > 1.5:
                            break
                        await asyncio.sleep(0.5)
                    await emit({"type": "refresh"})
                    if vs.session:
                        await add_turn(uid, "system", text, channel="voice")
                        try:
                            await vs.session.send_client_content(turns=types.Content(role="user", parts=[types.Part(text=text)]),
                                                                 turn_complete=True)
                        except Exception as e:  # noqa
                            log.warning("event inject failed: %s", e)

            up = asyncio.create_task(upstream())
            pump = asyncio.create_task(event_pump())
            greeted, failures, drop = False, 0, set()
            try:
                while not vs.closed.is_set():
                    snap = await state.load(uid)
                    system = build_system(snap, voice=True)
                    try:
                        cfg = _config(system, tools, vs.handle, drop)
                    except Exception as e:  # the installed SDK doesn't know an optional field
                        nxt = next((k for k in OPTIONAL if k not in drop and k not in _disabled), None)
                        if not nxt:
                            raise
                        log.warning("config field %s unsupported by SDK: %s", nxt, e)
                        _disabled.add(nxt)
                        continue
                    t0, reason = time.time(), "error"
                    try:
                        async with client.aio.live.connect(model=settings.GEMINI_LIVE_MODEL, config=cfg) as session:
                            vs.session = session
                            await emit({"type": "ready", "mode": snap.mode,
                                        "features": sorted(set(OPTIONAL) - _disabled - drop)})
                            if not greeted:
                                await session.send_client_content(turns=types.Content(role="user", parts=[types.Part(
                                    text="[SESSION START — system event] The user just opened voice mode. Greet them warmly by "
                                         "name in one short, smiling sentence, then follow YOUR NEXT MOVE.")]), turn_complete=True)
                                greeted = True
                            down = asyncio.create_task(downstream(session))
                            closed_wait = asyncio.create_task(vs.closed.wait())
                            done, _ = await asyncio.wait({down, closed_wait}, return_when=asyncio.FIRST_COMPLETED)
                            closed_wait.cancel()
                            if down in done:
                                reason = down.result()
                            else:   # user hung up: stop the Gemini session immediately (no leaked, billed sessions)
                                down.cancel()
                                with contextlib.suppress(BaseException):
                                    await down
                                reason = "closed"
                    except Exception as e:  # noqa
                        nxt = next((k for k in OPTIONAL if k not in drop and k not in _disabled), None)
                        if time.time() - t0 < 4 and nxt and not vs.produced:
                            # model/region rejected an optional feature: drop it and retry immediately
                            log.warning("live connect failed (%s); retrying without %s", e, nxt)
                            drop.add(nxt)
                            _disabled.add(nxt)
                            greeted = False
                            continue
                        log.exception("live session error")
                    finally:
                        vs.session = None
                        vs.speaking = False
                    if vs.closed.is_set() or reason == "closed":
                        break
                    if reason != "goaway":
                        failures += 1
                        if failures >= 3:
                            await emit({"type": "error", "message": "Voice connection is unstable. Let's continue by text for now."})
                            break
                        await asyncio.sleep(0.5)
                    await emit({"type": "reconnecting"})
            finally:
                vs.closed.set()
                up.cancel()
                pump.cancel()
    except Exception:  # noqa
        log.exception("voice session crashed")
        await emit({"type": "error", "message": "Voice connection problem. Switching to text."})
    finally:
        events.unsubscribe(uid, evq)
        learning.schedule(uid)
        try:
            await ws.close()
        except Exception:  # noqa
            pass

