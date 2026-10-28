import asyncio, json, os, sys, types as pt
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, "stubs")); sys.path.insert(0, os.path.join(HERE, "..", "..")); sys.path.insert(0, HERE)
os.environ.update(GCP_PROJECT="p", QLOO_API_KEY="k", MCP_INTERNAL_TOKEN="x"*32, PORT="8767", CRON_SECRET="c"*20, ALLOWED_ORIGINS="http://localhost:5173")
import fakes  # noqa  (fake QLOO + Gemini JSON)
from app import main
from app.core import llm
from app.agent import live
from app.services import events
from google.cloud.firestore import STORE
import uvicorn, websockets

SENT = []
CONNECTS = []
def NS(**k): return pt.SimpleNamespace(**{**dict(tool_call=None, server_content=None, session_resumption_update=None, go_away=None), **k})
class FakeSession:
    def __init__(self, n): self.n = n; self.q = asyncio.Queue()
    async def send_client_content(self, turns, turn_complete):
        SENT.append(("content", turns.parts[0].text)); 
        if "SESSION START" in turns.parts[0].text:
            await self.q.put([NS(session_resumption_update=pt.SimpleNamespace(new_handle="H1")),
                              NS(tool_call=pt.SimpleNamespace(function_calls=[pt.SimpleNamespace(id="c1", name="get_next_step", args={})]))])
            await self.q.put([NS(server_content=pt.SimpleNamespace(interrupted=False, input_transcription=None,
                              output_transcription=pt.SimpleNamespace(text="Hi Priya!"), model_turn=pt.SimpleNamespace(parts=[pt.SimpleNamespace(inline_data=pt.SimpleNamespace(data=b"\x01\x02"*10))]), turn_complete=True))])
        elif "PLAN READY" in turns.parts[0].text:
            await self.q.put([NS(go_away=pt.SimpleNamespace(time_left="1s"))])
    async def send_tool_response(self, function_responses): SENT.append(("tool", function_responses[0].name))
    async def send_realtime_input(self, audio): SENT.append(("audio", len(audio.data)))
    async def receive(self):
        batch = await self.q.get()
        for r in batch: yield r
class FakeConnect:
    def __init__(self, model, config):
        CONNECTS.append(config); self.s = FakeSession(len(CONNECTS))
        if len(CONNECTS) == 1 and getattr(config, "enable_affective_dialog", None):
            raise RuntimeError("unsupported field enable_affective_dialog")
    async def __aenter__(self): return self.s
    async def __aexit__(self, *a): return False
llm.client.aio.live = pt.SimpleNamespace(connect=FakeConnect)

def ok(c, m): print(("PASS " if c else "FAIL ") + m); ok.f += 0 if c else 1
ok.f = 0
async def main_():
    srv = uvicorn.Server(uvicorn.Config(main.app, port=8767, log_level="warning")); t = asyncio.create_task(srv.serve())
    while not srv.started: await asyncio.sleep(0.05)
    async with websockets.connect("ws://127.0.0.1:8767/ws/voice", origin="http://localhost:5173") as ws:
        await ws.send(json.dumps({"type": "start", "token": "tok-priya"}))
        got = []
        async def reader():
            async for m in ws: got.append(m)
        r = asyncio.create_task(reader())
        await asyncio.sleep(1.0)
        await ws.send(b"\x00\x00" * 320)
        await asyncio.sleep(0.3)
        uid = [p.split("/")[1] for p in STORE if p.startswith("users/")][0]
        events.publish([uid], {"type": "plan_ready", "space_id": "s", "title": "Wedding", "summary": {"sections": [{"title": "Venue", "top": ["A"]}]}})
        await asyncio.sleep(2.5)
        await ws.send(json.dumps({"type": "stop"}))
        await asyncio.sleep(0.3); r.cancel()
    js = [json.loads(m) for m in got if isinstance(m, str)]
    ok(len(CONNECTS) >= 2 and not getattr(CONNECTS[1], "enable_affective_dialog", None), "unsupported live feature auto-dropped & retried")
    ok(any(j["type"] == "ready" for j in js), "ready sent")
    ok(("tool", "get_next_step") in SENT, "voice tool call executed via MCP and answered")
    ok(any(isinstance(m, bytes) for m in got), "audio streamed to browser")
    ok(any(j["type"] == "transcript" and j["text"] == "Hi Priya!" for j in js), "transcript streamed")
    ok(("audio", 640) in SENT, "mic audio forwarded to Gemini")
    ok(any("PLAN READY" in x[1] for x in SENT if x[0] == "content"), "plan-ready event injected at a quiet moment")
    ok(any(j["type"] == "reconnecting" for j in js) and getattr(CONNECTS[-1].session_resumption, "handle", None) == "H1", "go_away -> resumed with handle")
    ok(sum(1 for x in SENT if x[0] == "content" and "SESSION START" in x[1]) == 1, "greets only once across reconnects")
    turns = [d for p, d in STORE.items() if "/turns/" in p]
    ok(any(d["text"] == "Hi Priya!" for d in turns), "voice transcript persisted")
    srv.should_exit = True; await t
    print("FAILS:", ok.f)
async def guarded():
    try:
        await asyncio.wait_for(main_(), 25)
    except asyncio.TimeoutError:
        print("TIMEOUT"); import traceback
        for tk in asyncio.all_tasks(): print(tk.get_coro())
        os._exit(1)
asyncio.run(guarded())
