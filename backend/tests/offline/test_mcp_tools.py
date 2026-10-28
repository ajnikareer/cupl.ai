import asyncio, json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, "stubs")); sys.path.insert(0, os.path.join(HERE, "..", ".."))
os.environ.update(GCP_PROJECT="p", QLOO_API_KEY="k", MCP_INTERNAL_TOKEN="x"*32, PORT="8765", CRON_SECRET="c"*20)
from app import main
from app.services import qloo, taste_intel, dna, plan_engine, learning
from app.core import llm
from app.toolkit import tools as T
from google.cloud.firestore import STORE

CALLS = []
async def fake_get(path, params, ttl_h=None):
    CALLS.append((path, dict(params)))
    if path == "/search":
        q = params["query"]
        if q.lower() == "arijit singh":
            return {"results": [{"entity_id": "ART_ARIJIT", "name": "Arijit Singh", "types": ["urn:entity:artist"]},
                                {"entity_id": "ART_X", "name": "Arijit Singh & Friends", "types": ["urn:entity:artist"]}]}
        if q.lower() == "mercury":
            return {"results": [{"entity_id": "M1", "name": "Mercury", "types": ["urn:entity:artist"], "properties": {"release_year": 1990}},
                                {"entity_id": "M2", "name": "Mercury", "types": ["urn:entity:artist"], "properties": {"release_year": 2010}}]}
        if q.lower() == "zzz":
            return {"results": []}
        return {"results": [{"entity_id": "E_" + q.replace(" ", "_"), "name": q.title(), "types": (params.get("types") or "urn:entity:artist").split(",")[:1]}]}
    if path == "/v2/insights":
        t = params["filter.type"].split(":")[-1]
        return {"results": {"entities": [{"entity_id": f"{t}_{i}", "name": f"{t.title()} Pick {i}", "types": [params["filter.type"]],
                                          "query": {"affinity": 0.9 - i * 0.05}, "tags": [{"name": "romantic"}]} for i in range(8)]}}
    if path == "/v2/tags":
        if "sufi" in params["filter.query"].lower():
            return {"results": {"tags": [{"id": "urn:tag:genre:music:sufi", "name": "Sufi"}]}}
        return {"results": {"tags": []}}
    raise AssertionError(path)
qloo._get = fake_get

async def fake_json(prompt, schema, model=None, temperature=0.2, system=None, thinking=0):
    props = schema.get("properties", {})
    if "items" in props and "mention" in str(props):          # taste extraction
        items = []
        if "Arijit" in prompt.split('Text: """')[-1]:
            items.append({"mention": "Arijit Singh", "kind": "entity", "category": "music", "sentiment": 0.8, "about": "self", "confidence": 0.95, "context_hint": "singer"})
        if "Sufi" in prompt.split('Text: """')[-1]:
            items.append({"mention": "Sufi", "kind": "genre_or_style", "category": "music", "sentiment": 0.9, "about": "self", "confidence": 0.9})
        if "Mercury" in prompt.split('Text: """')[-1]:
            items.append({"mention": "Mercury", "kind": "entity", "category": "music", "sentiment": 0.7, "about": "self", "confidence": 0.9})
        return {"items": items}
    if "choice" in props:
        return {"choice": -1, "certainty": 0.3}
    if "vibe" in props:
        return {"vibe": "Soulful, royal", "description": "You two!", "palette": ["#8e2c48", "#c9973a", "#f6e3e8", "#fbf6f3"]}
    if "summary" in props and "items" in props:              # planner
        await asyncio.sleep(0.1)
        ids = re.findall(r"^(\S+) \| ", prompt, re.M)
        if ids:
            return {"summary": "Lovely", "items": [{"candidate_id": i, "title": "x", "description": "d", "why": ["w"], "est_cost": 1000} for i in ids[:4]] + [{"candidate_id": "INVENTED", "title": "Fake", "description": "", "why": []}]}
        return {"summary": "Ideas", "items": [{"title": "Idea 1", "description": "d", "why": ["w"]}]}
    if "decisions" in props:
        return {"decisions": [], "summary": "sum", "mentions_surprise": False, "profile": {"partner_name": "Karan"}}
    if "options" in props:
        return {"options": ["Biryani", "Chaat"]}
    if "ideas" in props:
        return {"ideas": [{"title": "Rooftop", "description": "d", "why": "w"}]}
    return {}
for m in (taste_intel, dna, plan_engine, learning, T, llm):
    m.gen_json = fake_json

import uvicorn
from app.agent.tool_client import ToolClient, declarations, to_genai_schema
from app.auth import verify_token

def ok(cond, msg):
    print(("PASS " if cond else "FAIL ") + msg)
    if not cond: ok.fails += 1
ok.fails = 0

async def main_():
    srv = uvicorn.Server(uvicorn.Config(main.app, port=8765, log_level="warning"))
    task = asyncio.create_task(srv.serve())
    while not srv.started: await asyncio.sleep(0.05)
    a = await verify_token("tok-priya")
    b = await verify_token("tok-karan")
    async with ToolClient(a["uid"]) as tc:
        ok(tc.transport == "mcp", f"agent connected via MCP (transport={tc.transport})")
        specs = await tc.list_tools()
        ok(len(specs) >= 28, f"MCP lists {len(specs)} tools")
        decls = declarations(specs)
        ok(len(decls[0].function_declarations) == len(specs), "converted to Gemini declarations")
        r = await tc.call("get_next_step", {})
        ok(r["mode"] == "guide" and r["next"]["stage"] == "welcome", f"guide/welcome: {r['next']['stage']}")
        r = await tc.call("show_taste_picker", {"category": "music", "title": "t"})
        ok(r["ok"] is False and "event" in r["error"], "picker gated in guide mode")
        r = await tc.call("build_plan", {})
        ok(r["ok"] is False, "build_plan gated in guide mode")
        r = await tc.call("create_event", {"type": "wedding", "city": "Udaipur", "budget": "25,00,000", "start_date": "15 Feb"})
        ok(r["ok"] and r["created"]["city"] == "Udaipur" and r["invalid"], f"create_event + validation errors returned: {r['invalid']}")
        ok(r["_next"]["mode"] == "setup", f"mode now setup, next={r['_next']['stage']}")
        r = await tc.call("update_event", {"start_date": "2027-02-15", "guests": 300, "ceremonies": ["Haldi", "Sangeet", "Wedding"]})
        ok(r["ok"] and not r["event"].get("missing_fields"), f"update_event completes details; missing={r['event'].get('missing_fields')}")
        ok(r["_next"]["mode"] == "planner", "mode planner")
        # ---- taste intelligence: the critical input point
        r = await tc.call("remember_tastes", {"text": "I like Arijit Singh and I'm a big Sufi fan"})
        saved = {s["name"]: s for s in r["saved"]}
        ok("Arijit Singh" in saved and saved["Arijit Singh"]["category"] == "music" and saved["Arijit Singh"]["grounded_in_qloo"], "Arijit -> music, grounded to QLOO artist")
        ok("Sufi" in saved and saved["Sufi"]["grounded_in_qloo"], "Sufi -> resolved as QLOO tag")
        facts = [d for p, d in STORE.items() if p.startswith(f"users/{a['uid']}/facts/")]
        ar = next(f for f in facts if f["text"] == "Arijit Singh")
        ok(ar["qloo_entity_id"] == "ART_ARIJIT" and ar["qloo_type"] == "urn:entity:artist", "fact stores exact entity id ART_ARIJIT")
        r = await tc.call("remember_tastes", {"text": "I love Mercury"})
        ok(r["needs_clarification"] and r["widgets"][0]["kind"] == "disambiguation" and len(r["widgets"][0]["options"]) == 2, "ambiguous name -> clarification card")
        r = await tc.call("show_taste_picker", {"category": "music", "title": "Singers"})
        ok(r["ok"] and r["suggested"], f"picker with live suggestions: {r['suggested'][:3]}")
        r = await tc.call("remember_tastes", {"text": "zzz"})
        ok(r["ok"], "no-taste text handled")
        r = await tc.call("invite_partner", {})
        code = r["link"].split("/")[-1]
    # partner joins
    from app.services import couple as cs
    await cs.join(b, code)
    async with ToolClient(b["uid"]) as tc2:
        r = await tc2.call("remember_tastes", {"text": "Arijit Singh forever"})
        ok(r["saved"][0]["name"] == "Arijit Singh", "partner saves same artist")
        r = await tc2.call("get_couple_dna", {})
        ok("Arijit Singh" in r["shared"], f"DNA shared loves: {r['shared']}")
    async with ToolClient(a["uid"]) as tc:
        r = await tc.call("partner_insight", {"question": "what does he like"})
        ok(any("Arijit" in x for x in r["loves"]), "partner insight shows shared tastes")
        r = await tc.call("build_plan", {})
        ok(r["status"] == "started", "plan build started in background")
        r2 = await tc.call("build_plan", {})
        ok(r2["status"] == "already_building", "duplicate build prevented")
        for _ in range(200):
            await asyncio.sleep(0.05)
            if not plan_engine.is_building(a["active_space_id"] if a.get("active_space_id") else STORE[f"users/{a['uid']}"]["active_space_id"]): break
        sid = STORE[f"users/{a['uid']}"]["active_space_id"]
        sp = STORE[f"spaces/{sid}"]
        ok(sp["state"] == "planned" and sp["active_plan_version"] == 1, f"plan built: state={sp['state']}")
        plan = STORE[f"spaces/{sid}/plans/v1"]
        all_items = [i for s in plan["sections"] for i in s["items"]]
        ok(all(i["title"] != "Fake" for i in all_items), "invented candidate was dropped (guardrail)")
        ven = next(s for s in plan["sections"] if s["key"] == "venue")
        ok(ven["items"] and ven["items"][0].get("maps_url"), "venue items have maps links")
        ins = [c for c in CALLS if c[0] == "/v2/insights" and c[1]["filter.type"] == "urn:entity:artist"]
        ok(any("ART_ARIJIT" in c[1].get("signal.interests.entities", "") for c in ins), "QLOO insights received grounded Arijit signal")
        ok(any("urn:tag:genre:music:sufi" in c[1].get("signal.interests.tags", "") for c in ins), "QLOO insights received Sufi tag signal")
        ok(any(c[1].get("filter.location.query") == "Udaipur" for c in CALLS if c[0] == "/v2/insights"), "place sections filtered by city")
        todos = [p for p in STORE if p.startswith(f"spaces/{sid}/todos/")]
        ok(len(todos) == 8, f"todos seeded ({len(todos)})")
        r = await tc.call("get_plan", {})
        ok(r["sections"][0]["key"] == "venue", "get_plan returns keys")
        r = await tc.call("show_plan_section", {"section_key": "sangeet"})
        ok(r["widget"]["kind"] == "recs" and r["widget"]["items"], "show_plan_section emits recs widget")
        r = await tc.call("revise_plan", {"instruction": "no loud DJs", "section_keys": ["sangeet"]})
        ok(r["status"] == "started", "revise started")
        for _ in range(200):
            await asyncio.sleep(0.05)
            if not plan_engine.is_building(sid): break
        ok(STORE[f"spaces/{sid}"]["active_plan_version"] == 2, "revision -> v2")
        r = await tc.call("create_surprise", {"occasion": "birthday"})
        ok(r["private"], "surprise created")
        r = await tc.call("update_event", {"budget": -5})
        ok(r["invalid"], f"negative budget rejected: {r['invalid']}")
        r = await tc.call("show_choices", {"title": "x", "options": ["a"]})
        ok(r["ok"] is False and "Invalid" in r["error"], "schema validation enforced (minItems)")
        r = await tc.call("nope", {})
        ok(r["ok"] is False, "unknown tool handled")
    # widget application
    from app.toolkit import widgets
    STORE[f"conversations/{a['uid']}/turns/m1"] = {"role": "agent", "text": "", "ts": "9", "widget": {"id": "w1", "kind": "taste_picker", "category": "film", "title": "Films", "sentiment": "like"}}
    t = await widgets.apply(a["uid"], {"widget_id": "w1", "kind": "taste_picker", "values": [{"name": "Dil Chahta Hai", "entity_id": None}, {"name": "Queen", "entity_id": "MOV_Q"}]})
    facts = [d for p, d in STORE.items() if p.startswith(f"users/{a['uid']}/facts/") and d["category"] == "film"]
    ok(len(facts) == 2 and all(f["qloo_entity_id"] for f in facts), f"picker custom text resolved with known category: {t}")
    ok(STORE[f"conversations/{a['uid']}/turns/m1"]["widget"]["done"], "widget marked done")
    # http via MCP with external firebase token
    import httpx
    async with httpx.AsyncClient() as c:
        r = await c.post("http://127.0.0.1:8765/mcp/", json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"}, headers={"accept": "application/json, text/event-stream"})
        ok(r.status_code == 401, f"MCP without auth -> 401 ({r.status_code})")
        h = (await c.get("http://127.0.0.1:8765/healthz")).json()
        ok(h["tools"] >= 28, f"healthz {h}")
    # privacy: private taste not visible to partner
    from app.services import tastes as ts
    await ts.save_fact(b["uid"], "food", "Secret Snack", visibility="private", source="manual")
    async with ToolClient(a["uid"]) as tc:
        r = await tc.call("partner_insight", {})
        ok(not any("Secret" in x for x in r["loves"]), "partner's private taste hidden")
    # schema conversion sanity
    gs = to_genai_schema(T.TOOLS if False else specs[0]["inputSchema"]) if False else to_genai_schema({"type": "object", "properties": {"a": {"type": "array", "items": {"type": "string"}, "minItems": 2}}, "required": ["a"], "additionalProperties": False})
    ok(gs == {"type": "OBJECT", "properties": {"a": {"type": "ARRAY", "items": {"type": "STRING"}, "min_items": 2}}, "required": ["a"]}, f"schema conversion {gs}")
    srv.should_exit = True
    await task
    print("FAILS:", ok.fails)

asyncio.run(main_())
