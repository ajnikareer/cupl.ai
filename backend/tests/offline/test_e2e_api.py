import asyncio, json, os, sys, types as pt
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, "stubs")); sys.path.insert(0, os.path.join(HERE, "..", "..")); sys.path.insert(0, HERE)
os.environ.update(GCP_PROJECT="p", QLOO_API_KEY="k", MCP_INTERNAL_TOKEN="x"*32, PORT="8768", CRON_SECRET="c"*20)
import fakes  # noqa  (fake QLOO + Gemini JSON)
from app import main
from app.core import llm
from app.services import plan_engine
from google.cloud.firestore import STORE
import uvicorn, httpx

def chunk(t): return pt.SimpleNamespace(candidates=[pt.SimpleNamespace(content=pt.SimpleNamespace(parts=[pt.SimpleNamespace(text=t, function_call=None, thought=False)]))])
class FM:
    async def generate_content_stream(self, **k):
        async def g():
            yield chunk("Hello "); yield chunk("there!")
        return g()
    async def generate_content(self, **k):
        return pt.SimpleNamespace(text='{"ok": true}')
llm.client.aio.models = FM()
async def fake_embed(t): return [0.1] * 4
from app.services import memory; memory.embed = fake_embed

def ok(c, m): print(("PASS " if c else "FAIL ") + m); ok.f += 0 if c else 1
ok.f = 0
async def main_():
    srv = uvicorn.Server(uvicorn.Config(main.app, port=8768, log_level="warning")); t = asyncio.create_task(srv.serve())
    while not srv.started: await asyncio.sleep(0.05)
    B = "http://127.0.0.1:8768"
    H = {"Authorization": "Bearer tok-priya"}; H2 = {"Authorization": "Bearer tok-karan"}
    async with httpx.AsyncClient(base_url=B, headers=H, timeout=20) as c:
        r = await c.get("/api/me"); me = r.json()
        ok(r.status_code == 200 and me["mode"] == "guide" and "wedding" in me["space_types"] and me["categories"]["music"], "GET /api/me")
        ok((await c.get("/api/me", headers={"Authorization": "Bearer bad"})).status_code == 401, "bad token 401")
        r = await c.post("/api/spaces", json={"type": "wedding", "fields": {"city": "Udaipur", "start_date": "2027-02-15", "guests": "300", "budget": "2500000", "ceremonies": ["Sangeet"]}})
        s = r.json(); sid = s["id"]
        ok(r.status_code == 200 and s["state"] == "ready" and not s["missing_fields"], f"create space ready ({s['state']})")
        ok((await c.post("/api/spaces", json={"type": "nope"})).status_code == 400, "bad type 400")
        r = await c.patch(f"/api/spaces/{sid}", json={"fields": {"end_date": "2027-01-01"}})
        ok(r.status_code == 400, "end before start rejected")
        r = await c.post("/api/tastes", json={"category": "music", "name": "Arijit Singh"})
        ok(r.json().get("qloo_entity_id") == "ART_ARIJIT", "manual taste resolved via taste_intel")
        r = await c.post("/api/tastes", json={"category": "music", "name": "Mercury"})
        ok(r.json().get("ambiguous") and len(r.json()["candidates"]) == 2, "manual ambiguous returns candidates")
        r = await c.get("/api/qloo/search", params={"q": "Arijit Singh", "category": "music"})
        ok(r.json()["results"][0]["entity_id"] == "ART_ARIJIT", "qloo search proxy")
        r = await c.post(f"/api/spaces/{sid}/plan", json={})
        ok(r.json()["status"] == "building", "build via API")
        r = await c.get(f"/api/spaces/{sid}/plan"); p = r.json()
        sp_ = (await c.get(f"/api/spaces/{sid}")).json(); ok(sp_["state"] == "building", "space shows building immediately after POST")
        for _ in range(200):
            await asyncio.sleep(0.05)
            if not plan_engine.is_building(sid): break
        p = (await c.get(f"/api/spaces/{sid}/plan")).json()
        ok(p["status"] == "done" and all(s_["status"] == "done" for s_ in p["sections"]), "plan done")
        item = next(i for s_ in p["sections"] for i in s_["items"] if i.get("entity_id"))
        r = await c.patch(f"/api/spaces/{sid}/items/{item['id']}", json={"status": "skipped"})
        ok(r.status_code == 200 and item["entity_id"] in STORE[f"spaces/{sid}"]["excluded_ids"], "skip -> excluded next time")
        r = await c.patch(f"/api/spaces/{sid}/items/{item['id']}", json={"status": "liked"})
        ok(r.status_code == 200, "like")
        r = await c.put(f"/api/spaces/{sid}/budget", json={"allocations": [{"category": "Venue", "pct": 60}, {"category": "Food", "pct": 40}]})
        ok(r.json()["budget"][0]["amount"] == 1500000, "budget split")
        ok((await c.put(f"/api/spaces/{sid}/budget", json={"allocations": [{"category": "V", "pct": 0}]})).status_code == 400, "zero budget rejected")
        todos = (await c.get(f"/api/spaces/{sid}/todos")).json()["todos"]
        ok(len(todos) == 8, "todos seeded")
        r = await c.patch(f"/api/spaces/{sid}/todos/{todos[0]['id']}", json={"done": True}); ok(r.status_code == 200, "todo done")
        r = await c.post(f"/api/spaces/{sid}/memories", json={"text": "Loved the sunset dinner", "rating": 5}); ok(r.status_code == 200, "memory saved")
        ok(len((await c.get(f"/api/spaces/{sid}/memories")).json()["memories"]) == 1, "memories listed")
        r = await c.post("/api/dna/refresh"); ok(r.status_code == 200 and r.json()["dna"]["version"] >= 1, "dna refresh")
        inv = (await c.post("/api/couple/invite")).json()
        inv2 = (await c.post("/api/couple/invite")).json()
        ok(inv["code"] == inv2["code"], "invite code reused while valid")
        # chat SSE
        evs = []
        async with c.stream("POST", "/api/chat", json={"text": "hi"}) as resp:
            async for line in resp.aiter_lines():
                if line.startswith("data: "): evs.append(json.loads(line[6:]))
        ok([e["text"] for e in evs if e["type"] == "delta"] == ["Hello ", "there!"] and evs[-1]["type"] == "done", "SSE chat streams")
        h = (await c.get("/api/chat/history")).json()["turns"]
        ok([x["text"] for x in h][-2:] == ["hi", "Hello there!"], "history persisted")
        ok((await c.get("/api/notifications")).json()["notifications"], "notifications created by plan")
        ok((await c.post("/api/notifications/read")).status_code == 200, "read all")
        ok("episodes" in (await c.get("/api/memory")).json(), "memory endpoint")
        ok((await c.post("/internal/cron/run")).status_code == 403, "cron requires secret")
        STORE[f"spaces/{sid}"]["end_date"] = None; STORE[f"spaces/{sid}"]["start_date"] = "2020-01-01"; STORE[f"spaces/{sid}"]["state"] = "planned"
        r = await c.post("/internal/cron/run", headers={"X-Cron-Secret": "c" * 20})
        ok(r.json()["checkins"] == 1 and STORE[f"spaces/{sid}"]["state"] == "completed", "cron: post-event check-in")
        STORE[f"spaces/{sid}"]["state"] = "building"; STORE[f"spaces/{sid}"]["building_started_at"] = "2020-01-01T00:00:00+00:00"
        ok((await c.get(f"/api/spaces/{sid}")).json()["state"] != "building", "stuck 'building' state self-heals")
        ok((await c.get("/api/surprises")).status_code == 200, "surprises")
        h = (await c.get("/healthz", params={"deep": "true"})).json()
        ok(all(v["ok"] for v in h["checks"].values()) and h["checks"]["mcp"]["detail"]["transport"] == "mcp" and h["checks"]["taste_intel"]["detail"]["name"] == "Arijit Singh", f"deep health: {[(k, v['ok']) for k, v in h['checks'].items()]}")
        # partner join via API lands in the event
        r = await c.post("/api/couple/join", json={"code": inv["code"]}, headers=H2)
        me2 = (await c.get("/api/me", headers=H2)).json()
        ok(r.status_code == 200 and me2["active_space"] and me2["active_space"]["id"] == sid and me2["partner"]["name"] == "Priya", "partner joins via link and lands in the event")
        r = await c.delete(f"/api/spaces/{sid}"); ok(r.status_code == 200 and f"spaces/{sid}" not in STORE, "delete space")
    srv.should_exit = True; await t
    print("FAILS:", ok.f)
asyncio.run(main_())
