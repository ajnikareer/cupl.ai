import asyncio, os, sys, types as pytypes
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, "stubs")); sys.path.insert(0, os.path.join(HERE, "..", "..")); sys.path.insert(0, HERE)
os.environ.update(GCP_PROJECT="p", QLOO_API_KEY="k", MCP_INTERNAL_TOKEN="x"*32, PORT="8766", CRON_SECRET="c"*20)
import fakes  # noqa  (fake QLOO + Gemini JSON)
from app import main
from app.core import llm
from app.agent import orchestrator, context
from app.services import state, learning
from app.auth import verify_token
from google.cloud.firestore import STORE
import uvicorn

def P(text=None, fc=None):
    return pytypes.SimpleNamespace(text=text, function_call=fc, thought=False)
def FC(name, **args):
    return pytypes.SimpleNamespace(name=name, args=args)
def chunk(*parts):
    return pytypes.SimpleNamespace(candidates=[pytypes.SimpleNamespace(content=pytypes.SimpleNamespace(parts=list(parts)))])

SCRIPT = []
SEEN_SYSTEM = []
class FakeModels:
    async def generate_content_stream(self, model, contents, config):
        SEEN_SYSTEM.append(config.system_instruction)
        SEEN_SYSTEM.append([f.name for f in config.tools[0].function_declarations])
        step = SCRIPT.pop(0)
        async def gen():
            for c in step:
                yield c
        return gen()
llm.client.aio.models = FakeModels()

def ok(c, m):
    print(("PASS " if c else "FAIL ") + m); ok.f += 0 if c else 1
ok.f = 0

async def run(uid, text=None, wr=None):
    evs = []
    async def emit(e): evs.append(e)
    await orchestrator.run_turn(uid, text, wr, emit)
    return evs

async def main_():
    srv = uvicorn.Server(uvicorn.Config(main.app, port=8766, log_level="warning"))
    t = asyncio.create_task(srv.serve())
    while not srv.started: await asyncio.sleep(0.05)
    u = await verify_token("tok-priya"); uid = u["uid"]
    # turn 1: welcome, no tools
    SCRIPT.append([chunk(P("Hi Priya! I'm WeaveWed ")), chunk(P("— what are you two celebrating?"))])
    evs = await run(uid, "hi")
    ok([e["text"] for e in evs if e["type"] == "delta"] == ["Hi Priya! I'm WeaveWed ", "— what are you two celebrating?"], "streams deltas")
    ok("YOUR NEXT MOVE (stage: welcome)" in SEEN_SYSTEM[0], "director stage welcome in system prompt")
    ok("show_taste_picker" not in SEEN_SYSTEM[1] and "create_event" in SEEN_SYSTEM[1], "guide mode: model only sees allowed tools")
    # turn 2: user says wedding in Udaipur -> create_event, then ask one question
    SCRIPT.append([chunk(P(fc=FC("create_event", type="wedding", city="Udaipur")))])
    SCRIPT.append([chunk(P("Udaipur! Dreamy. When's the big day?"))])
    evs = await run(uid, "We're getting married in Udaipur!")
    ok(any(e["type"] == "status" for e in evs) and any(e["type"] == "refresh" for e in evs), "tool status + refresh emitted")
    ok(STORE[f"users/{uid}"]["active_space_id"], "event space created via MCP from the agent loop")
    sys2 = SEEN_SYSTEM[-2]
    ok("MODE: SETUP" in sys2 and "SKILL: WEDDING" in sys2, "context refreshed after mutating tool (setup mode + wedding skill)")
    # turn 3: taste in words -> remember_tastes
    SCRIPT.append([chunk(P(fc=FC("remember_tastes", text="I like Arijit Singh", category_hint="music")))])
    SCRIPT.append([chunk(P("Arijit! Goosebumps."))])
    await run(uid, "I like Arijit Singh")
    facts = [d for p, d in STORE.items() if p.startswith(f"users/{uid}/facts/")]
    ok(any(f.get("qloo_entity_id") == "ART_ARIJIT" for f in facts), "agent -> MCP -> taste_intel grounded Arijit")
    # turn 4: picker widget emitted & persisted
    SCRIPT.append([chunk(P("Okay, your movies! "), P(fc=FC("show_taste_picker", category="film", title="Films you love")))])
    SCRIPT.append([chunk(P("Tap a few 💕"))])
    evs = await run(uid, "ask me about movies")
    w = [e for e in evs if e["type"] == "widget"]
    ok(w and w[0]["widget"]["kind"] == "taste_picker" and w[0]["widget"]["suggestions"], "taste picker widget streamed to UI")
    # turn 5: user taps picker -> deterministic save, agent acknowledges
    SCRIPT.append([chunk(P("Love those picks!"))])
    evs = await run(uid, None, {"widget_id": w[0]["widget"]["id"], "kind": "taste_picker", "values": [{"name": "Movie Pick 1", "entity_id": "movie_1"}]})
    ok(any(f.get("qloo_entity_id") == "movie_1" for p, f in STORE.items() if p.startswith(f"users/{uid}/facts/")), "picker selection saved with entity id")
    hist = [d for p, d in STORE.items() if p.startswith(f"conversations/{uid}/turns/")]
    ok(any(d["text"].startswith("[picked") for d in hist), "picker answer recorded as user turn")
    ok(STORE[f"conversations/{uid}"].get("taste_streak") == 1, "taste streak tracked")
    # history conversion includes widget answered
    contents = orchestrator.history_contents(sorted(hist, key=lambda d: d["ts"]))
    ok(contents[0].role == "user" and any("showed taste_picker card" in p.text for c in contents for p in c.parts), "history rebuilt incl. widgets")
    # gemini error -> graceful
    SCRIPT.append([])
    async def boom(**k): raise RuntimeError("503 UNAVAILABLE")
    orig = llm.client.aio.models.generate_content_stream
    llm.client.aio.models.generate_content_stream = boom
    evs = await run(uid, "hello?")
    ok(any(e["type"] == "error" for e in evs) and evs[-1]["type"] == "done", "LLM failure -> friendly error + done")
    llm.client.aio.models.generate_content_stream = orig; SCRIPT.clear()
    # learning worker
    await learning.run(uid)
    ok(STORE[f"conversations/{uid}"].get("learned_upto") and STORE[f"users/{uid}"]["profile"].get("partner_name") == "Karan", "learning: profile + summary saved")
    # director progression
    from app.services.spaces import update_space
    snap = await state.load(uid)
    ok(snap.next["stage"] in ("rapport", "event_basics"), f"director after welcome: {snap.next['stage']}")
    await update_space(u["active_space_id"] if u.get("active_space_id") else STORE[f"users/{uid}"]["active_space_id"], u["couple_id"],
                       {"start_date": "2027-02-15", "guests": 300, "budget": 2500000, "ceremonies": ["Sangeet"]})
    STORE[f"conversations/{uid}"]["turn_count"] = 20; STORE[f"conversations/{uid}"]["taste_streak"] = 0
    snap = await state.load(uid)
    ok(snap.next["stage"] == "know_tastes" and snap.next["detail"]["category"] in ("food", "fashion", "film", "music"), f"director asks one taste category: {snap.next['detail'].get('category')}")
    STORE[f"conversations/{uid}"]["taste_streak"] = 2
    snap = await state.load(uid)
    ok(snap.next["stage"] in ("invite_partner", "ready_to_plan"), f"after 2 taste questions, moves on: {snap.next['stage']}")
    srv.should_exit = True; await t
    print("FAILS:", ok.f)
asyncio.run(main_())
