import asyncio, os, re, sys
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

