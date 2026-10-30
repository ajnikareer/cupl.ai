import asyncio
import json
import time
from datetime import datetime, timezone
from collections import defaultdict, deque

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from ..agent.orchestrator import run_turn
from ..auth import current_user
from ..db import db, get_doc, list_col, new_id, now_iso
from ..services import couple as couple_svc
from ..services import dna as dna_svc
from ..services import plan_engine, qloo, state, taste_intel, calendar_svc, recommends_svc
from ..services import spaces as sp
from ..services import tastes
from ..services.memory import list_episodes, recent_turns, save_episode

router = APIRouter(prefix="/api")
_hits: dict[str, deque] = defaultdict(deque)


def rate_limit(uid: str, key: str, per_min: int):
    q, now = _hits[f"{uid}:{key}"], time.time()
    while q and q[0] < now - 60:
        q.popleft()
    if len(q) >= per_min:
        raise HTTPException(429, "Slow down a little 🙂 — too many requests, try again in a moment.")
    q.append(now)


# ---------------- me / couple ----------------
@router.get("/me")
async def me(user=Depends(current_user)):
    snap = await state.load(user["uid"], with_episodes=False)
    unread = 0
    async for _ in db.collection("notifications").where("uid", "==", user["uid"]).where("read", "==", False).limit(50).stream():
        unread += 1
    return {"user": snap.user, "couple": {"id": snap.couple.get("id"), "status": snap.couple.get("status"),
                                          "members": len(snap.couple.get("members", []))},
            "partner": {"name": snap.partner.get("name"), "photo": snap.partner.get("photo")} if snap.partner else None,
            "mode": snap.mode, "active_space": snap.space, "unread": unread, "next": snap.next,
            "space_types": {k: {"label": v["label"], "fields": sp.field_specs(k)} for k, v in sp.TEMPLATES.items()},
            "categories": {k: v["label"] for k, v in taste_intel.CATEGORIES.items()}}


class ProfileUpdateBody(BaseModel):
    name: str | None = None
    heritage: str | None = None
    tradition: str | None = None
    state: str | None = None
    country: str | None = None


@router.patch("/me")
async def update_me(body: ProfileUpdateBody, user=Depends(current_user)):
    upd: dict = {}
    if body.name is not None:
        name = body.name.strip()[:40]
        if not name:
            raise HTTPException(400, "Name can't be empty")
        upd["name"] = name
        upd["name_confirmed"] = True

    prof_upd = {}
    for k in ["heritage", "tradition", "state", "country"]:
        val = getattr(body, k, None)
        if val is not None:
            prof_upd[k] = val.strip()[:60]

    if prof_upd:
        for k, v in prof_upd.items():
            upd[f"profile.{k}"] = v

    if upd:
        await db.document(f"users/{user['uid']}").update(upd)
        if user.get("couple_id"):
            try:
                await dna_svc.compute(user["couple_id"])
            except Exception as e:
                log.warning("DNA recompute failed: %s", e)

    return {"ok": True, "profile": prof_upd}


@router.post("/couple/invite")
async def invite(user=Depends(current_user)):
    return await couple_svc.create_invite(user)


class JoinBody(BaseModel):
    code: str


@router.post("/couple/join")
async def join(body: JoinBody, user=Depends(current_user)):
    c = await couple_svc.join(user, body.code.strip())
    try:
        await dna_svc.compute(c["id"])
    except Exception:  # noqa
        pass
    return {"ok": True}


class StatusBody(BaseModel):
    status: str


@router.patch("/couple")
async def couple_status(body: StatusBody, user=Depends(current_user)):
    if body.status not in ("dating", "engaged", "married", "parents"):
        raise HTTPException(400, "bad status")
    await db.document(f"couples/{user['couple_id']}").update({"status": body.status})
    return {"ok": True}


# ---------------- spaces ----------------
class SpaceBody(BaseModel):
    type: str | None = None
    fields: dict = {}


@router.get("/spaces")
async def spaces(user=Depends(current_user)):
    return {"spaces": await sp.list_spaces(user["couple_id"]), "active_space_id": user.get("active_space_id")}


@router.post("/spaces")
async def create_space(body: SpaceBody, user=Depends(current_user)):
    s, errors = await sp.create_space(user, body.type or "", body.fields)
    return {**s, "invalid": errors}



class SaveProposalBody(BaseModel):
    title: str
    type: str = "trip"
    city: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    budget: float | None = None
    highlights: list[str] = []
    space_id: str | None = None


@router.post("/spaces/save-proposal")
async def save_proposal(body: SaveProposalBody, user=Depends(current_user)):
    if body.space_id:
        s = await sp.get_space(body.space_id, user["couple_id"])
        if s:
            await db.document(f"spaces/{s['id']}").set({"confirmed": True}, merge=True)
            return {"ok": True, "space": s}
    s, err = await sp.create_space(user, body.type, body.model_dump())
    return {"ok": True, "space": s}


@router.get("/spaces/{sid}")
async def get_space(sid: str, user=Depends(current_user)):
    s = await sp.get_space(sid, user["couple_id"])
    started = s.get("building_started_at") or ""
    stale = not started or (datetime.now(timezone.utc) - datetime.fromisoformat(started)).total_seconds() > 600
    if s.get("state") == "building" and not plan_engine.is_building(sid) and stale:
        s["state"] = sp.compute_state({**s, "state": None})   # self-heal a stuck state (e.g. instance restart)
        await db.document(f"spaces/{sid}").update({"state": s["state"]})
    s["field_specs"] = sp.field_specs(s["type"])
    s.pop("excluded_ids", None)
    return s


@router.patch("/spaces/{sid}")
async def patch_space(sid: str, body: SpaceBody, user=Depends(current_user)):
    s, errors = await sp.update_space(sid, user["couple_id"], body.fields)
    if errors:
        raise HTTPException(400, "; ".join(errors))
    return s


@router.delete("/spaces/{sid}")
async def delete_space(sid: str, user=Depends(current_user)):
    await sp.get_space(sid, user["couple_id"])
    for sub in ("plans", "todos"):
        async for s in db.collection(f"spaces/{sid}/{sub}").stream():
            await s.reference.delete()
    await db.document(f"spaces/{sid}").delete()
    if user.get("active_space_id") == sid:
        await db.document(f"users/{user['uid']}").update({"active_space_id": None})
    return {"ok": True}


@router.post("/spaces/{sid}/activate")
async def activate(sid: str, user=Depends(current_user)):
    await sp.get_space(sid, user["couple_id"])
    await db.document(f"users/{user['uid']}").update({"active_space_id": sid})
    return {"ok": True}


class PlanBody(BaseModel):
    section_keys: list[str] | None = None
    instruction: str | None = None


@router.post("/spaces/{sid}/plan")
async def build_plan(sid: str, body: PlanBody, user=Depends(current_user)):
    rate_limit(user["uid"], "plan", 6)
    s = await sp.get_space(sid, user["couple_id"])
    if s["missing_fields"]:
        raise HTTPException(400, f"Add these details first: {', '.join(s['missing_fields'])}")
    if body.instruction:
        await db.document(f"couples/{user['couple_id']}/decisions/{new_id('d')}").set(
            {"summary": body.instruction[:300], "by_uid": user["uid"], "space_id": sid, "at": now_iso()})
    started = await plan_engine.start_build(sid, body.section_keys, (body.instruction or None), user["uid"])
    return {"status": "building" if started else "already_building"}


@router.get("/spaces/{sid}/plan")
async def get_plan(sid: str, version: int | None = None, user=Depends(current_user)):
    s = await sp.get_space(sid, user["couple_id"])
    if version:
        return await get_doc(f"spaces/{sid}/plans/v{version}")
    return await plan_engine.latest_plan(s, include_building=True)


class ItemBody(BaseModel):
    status: str


@router.patch("/spaces/{sid}/items/{item_id}")
async def item_status(sid: str, item_id: str, body: ItemBody, user=Depends(current_user)):
    if body.status not in ("suggested", "liked", "skipped", "done"):
        raise HTTPException(400, "bad status")
    s = await sp.get_space(sid, user["couple_id"])
    if not s.get("active_plan_version"):
        raise HTTPException(404, "No plan")
    ref = db.document(f"spaces/{sid}/plans/v{s['active_plan_version']}")
    plan = await get_doc(ref.path)
    found = None
    for sec in plan["sections"]:
        for it in sec.get("items", []):
            if it["id"] == item_id:
                it["status"] = body.status
                found = (sec, it)
    if not found:
        raise HTTPException(404, "Item not found")
    await ref.update({"sections": plan["sections"]})
    sec, it = found
    spec = next((x for x in sp.TEMPLATES[s["type"]]["sections"] if x["key"] == sec["key"]), None)
    cat = taste_intel.TYPE_TO_CATEGORY.get((spec or {}).get("qtype") or "")
    if body.status == "liked" and it.get("entity_id") and cat:
        await tastes.save_fact(user["uid"], cat, it["title"], entity_id=it["entity_id"], qloo_type=spec["qtype"],
                               image=it.get("image"), sentiment=0.6, confidence=0.6, source="feedback")
    if body.status == "skipped" and it.get("entity_id"):
        ex = list(set((s.get("excluded_ids") or []) + [it["entity_id"]]))
        await db.document(f"spaces/{sid}").update({"excluded_ids": ex})
    return {"ok": True}


class BudgetBody(BaseModel):
    allocations: list[dict]


@router.put("/spaces/{sid}/budget")
async def budget(sid: str, body: BudgetBody, user=Depends(current_user)):
    s = await sp.get_space(sid, user["couple_id"])
    try:
        return await plan_engine.set_budget(s, body.allocations)
    except ValueError as e:
        raise HTTPException(400, str(e))


# ---------------- todos / memories ----------------
class TodoBody(BaseModel):
    title: str | None = None
    due: str | None = None
    done: bool | None = None


@router.get("/spaces/{sid}/todos")
async def todos(sid: str, user=Depends(current_user)):
    await sp.get_space(sid, user["couple_id"])
    t = await list_col(db.collection(f"spaces/{sid}/todos"))
    t.sort(key=lambda x: (x.get("done", False), x.get("due") or "9999"))
    return {"todos": t}


@router.post("/spaces/{sid}/todos")
async def add_todo(sid: str, body: TodoBody, user=Depends(current_user)):
    await sp.get_space(sid, user["couple_id"])
    if not (body.title or "").strip():
        raise HTTPException(400, "title required")
    tid = new_id("t")
    await db.document(f"spaces/{sid}/todos/{tid}").set({"title": body.title.strip()[:200], "due": body.due or None, "done": False,
                                                        "assignee": None, "source": "user", "created_at": now_iso()})
    return {"id": tid}


@router.patch("/spaces/{sid}/todos/{tid}")
async def patch_todo(sid: str, tid: str, body: TodoBody, user=Depends(current_user)):
    await sp.get_space(sid, user["couple_id"])
    upd = {k: v for k, v in body.model_dump().items() if v is not None}
    if upd:
        await db.document(f"spaces/{sid}/todos/{tid}").update(upd)
    return {"ok": True}


@router.delete("/spaces/{sid}/todos/{tid}")
async def del_todo(sid: str, tid: str, user=Depends(current_user)):
    await sp.get_space(sid, user["couple_id"])
    await db.document(f"spaces/{sid}/todos/{tid}").delete()
    return {"ok": True}


class MemoryBody(BaseModel):
    text: str
    rating: float | None = None


@router.get("/spaces/{sid}/memories")
async def memories(sid: str, user=Depends(current_user)):
    await sp.get_space(sid, user["couple_id"])
    return {"memories": [e for e in await list_episodes(user["couple_id"]) if e.get("space_id") == sid]}


@router.post("/spaces/{sid}/memories")
async def add_memory(sid: str, body: MemoryBody, user=Depends(current_user)):
    await sp.get_space(sid, user["couple_id"])
    if not body.text.strip():
        raise HTTPException(400, "text required")
    return await save_episode(user["couple_id"], body.text.strip(), sid, body.rating, by_uid=user["uid"])


# ---------------- tastes / dna / memory ----------------
@router.get("/tastes")
async def my_tastes(user=Depends(current_user)):
    f = await tastes.facts(user["uid"])
    f.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
    return {"facts": f}


class TasteBody(BaseModel):
    category: str
    name: str
    entity_id: str | None = None
    image: str | None = None
    sentiment: float = 0.85
    visibility: str = "shared"


@router.post("/tastes")
async def add_taste(body: TasteBody, user=Depends(current_user)):
    rate_limit(user["uid"], "taste", 40)
    if body.category not in taste_intel.CATEGORIES:
        raise HTTPException(400, "unknown category")
    vis = "private" if body.visibility == "private" else "shared"
    if body.entity_id:
        return await tastes.save_fact(user["uid"], body.category, body.name, entity_id=body.entity_id,
                                      qloo_type=(taste_intel.CATEGORIES[body.category]["types"] or [None])[0],
                                      image=body.image, sentiment=body.sentiment, confidence=0.95, visibility=vis, source="manual")
    res = await taste_intel.resolve(body.name.strip(), body.category, "entity")
    if res["status"] == "ambiguous":
        return {"ambiguous": True, "candidates": res["candidates"], "mention": body.name}
    return await tastes.save_resolution(user["uid"], res, body.sentiment, 0.95, "manual", vis)


class TastePatch(BaseModel):
    visibility: str | None = None
    sentiment: float | None = None
    confirm: bool | None = None


@router.patch("/tastes/{fid}")
async def patch_taste(fid: str, body: TastePatch, user=Depends(current_user)):
    upd = {}
    if body.visibility in ("shared", "private"):
        upd["visibility"] = body.visibility
    if body.sentiment is not None:
        upd["sentiment"] = max(-1.0, min(1.0, body.sentiment))
    if body.confirm:
        upd.update({"source": "manual", "confidence": 0.9, "visibility": "shared"})
    if upd:
        await db.document(f"users/{user['uid']}/facts/{fid}").update(upd)
    return {"ok": True}


@router.delete("/tastes/{fid}")
async def del_taste(fid: str, user=Depends(current_user)):
    await db.document(f"users/{user['uid']}/facts/{fid}").delete()
    return {"ok": True}


@router.get("/dna")
async def get_dna(user=Depends(current_user)):
    c = await couple_svc.get_couple(user["couple_id"])
    return {"dna": c.get("dna")}


@router.post("/dna/refresh")
async def refresh_dna(user=Depends(current_user)):
    rate_limit(user["uid"], "dna", 6)
    return {"dna": await dna_svc.compute(user["couple_id"])}


@router.get("/qloo/search")
async def qloo_search(q: str = Query(..., min_length=1, max_length=100), category: str = "music", user=Depends(current_user)):
    rate_limit(user["uid"], "search", 90)
    types = taste_intel.CATEGORIES.get(category, {}).get("types")
    if not types:
        return {"results": []}
    try:
        res = await qloo.search(q, types, take=8)
    except qloo.QlooError as e:
        raise HTTPException(503, str(e))
    return {"results": [{"name": r["name"], "entity_id": r["entity_id"], "image": r.get("image"),
                         "sub": " · ".join(x for x in [str(r.get("year") or ""), (r.get("disambiguation") or "")] if x)}
                        for r in res if r.get("name")]}


@router.get("/memory")
async def memory(user=Depends(current_user)):
    eps = await list_episodes(user["couple_id"])
    decs = [d for d in await couple_svc.decisions(user["couple_id"], 50)
            if not d.get("private_to") or d.get("private_to") == user["uid"]]
    conv = await get_doc(f"conversations/{user['uid']}") or {}
    return {"episodes": eps, "decisions": decs, "summary": conv.get("summary"), "profile": user.get("profile") or {}}


@router.delete("/memory/episodes/{eid}")
async def del_episode(eid: str, user=Depends(current_user)):
    e = await get_doc(f"episodes/{eid}")
    if not e or e.get("couple_id") != user["couple_id"]:
        raise HTTPException(404, "not found")
    await db.document(f"episodes/{eid}").delete()
    return {"ok": True}


@router.delete("/memory/decisions/{did}")
async def del_decision(did: str, user=Depends(current_user)):
    await db.document(f"couples/{user['couple_id']}/decisions/{did}").delete()
    return {"ok": True}


# ---------------- surprises / notifications ----------------
@router.get("/surprises")
async def surprises(user=Depends(current_user)):
    out = []
    async for s in db.collection("surprises").where("owner_uid", "==", user["uid"]).stream():
        d = s.to_dict()
        d["id"] = s.id
        out.append(d)
    out.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return {"surprises": out}


@router.delete("/surprises/{sid}")
async def del_surprise(sid: str, user=Depends(current_user)):
    d = await get_doc(f"surprises/{sid}")
    if not d or d.get("owner_uid") != user["uid"]:
        raise HTTPException(404, "not found")
    await db.document(f"surprises/{sid}").delete()
    return {"ok": True}


# ---------------- calendar / lifestyle recommends ----------------
@router.get("/calendar")
async def get_calendar(user=Depends(current_user)):
    return await calendar_svc.get_couple_calendar(user)


class CalendarItemBody(BaseModel):
    title: str
    category: str = "dining"
    date: str
    time: str | None = None
    description: str | None = None
    recommendation_id: str | None = None
    maps_url: str | None = None
    image: str | None = None
    is_private: bool = False


@router.post("/calendar/items")
async def add_cal_item(body: CalendarItemBody, user=Depends(current_user)):
    return await calendar_svc.add_calendar_item(user, body.model_dump())


@router.delete("/calendar/items/{item_id}")
async def del_cal_item(item_id: str, user=Depends(current_user)):
    ok = await calendar_svc.delete_calendar_item(user, item_id)
    if not ok:
        raise HTTPException(404, "item not found")
    return {"ok": True}


class ToggleRecBody(BaseModel):
    recommendation_id: str
    title: str
    category: str = "dining"
    date: str
    time: str | None = None
    description: str | None = None
    maps_url: str | None = None
    image: str | None = None
    is_private: bool = False


@router.post("/calendar/toggle-rec")
async def toggle_rec_calendar(body: ToggleRecBody, user=Depends(current_user)):
    return await calendar_svc.toggle_recommendation_in_calendar(user, body.recommendation_id, body.model_dump())


@router.get("/recommends")
async def get_recommends(user=Depends(current_user)):
    return await recommends_svc.get_lifestyle_recommendations(user)


class ToggleRecommendsBody(BaseModel):
    enabled: bool


@router.post("/recommends/toggle")
async def toggle_recommends(body: ToggleRecommendsBody, user=Depends(current_user)):
    return await recommends_svc.toggle_recommends_enabled(user, body.enabled)


@router.post("/recommends/refresh")
async def refresh_recommends(user=Depends(current_user)):
    return await recommends_svc.refresh_recommendations(user)


@router.get("/notifications")
async def notifications(user=Depends(current_user)):
    out = []
    async for s in db.collection("notifications").where("uid", "==", user["uid"]).limit(300).stream():
        d = s.to_dict()
        d["id"] = s.id
        out.append(d)
    out.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return {"notifications": out[:50]}


@router.post("/notifications/read")
async def read_all(user=Depends(current_user)):
    async for s in db.collection("notifications").where("uid", "==", user["uid"]).where("read", "==", False).stream():
        await s.reference.update({"read": True})
    return {"ok": True}


# ---------------- chat ----------------
class ChatBody(BaseModel):
    text: str | None = None
    widget_response: dict | None = None


@router.get("/chat/history")
async def history(user=Depends(current_user)):
    turns = await recent_turns(user["uid"], 80)
    return {"turns": [t for t in turns if t.get("role") != "system"]}


@router.post("/chat")
async def chat(body: ChatBody, user=Depends(current_user)):
    rate_limit(user["uid"], "chat", 30)
    queue: asyncio.Queue = asyncio.Queue()

    async def emit(ev):
        await queue.put(ev)

    task = asyncio.create_task(run_turn(user["uid"], body.text, body.widget_response, emit))

    async def stream():
        while True:
            try:
                ev = await asyncio.wait_for(queue.get(), timeout=15)
            except asyncio.TimeoutError:
                yield ": keepalive\n\n"
                if task.done() and queue.empty():
                    break
                continue
            yield f"data: {json.dumps(ev, default=str)}\n\n"
            if ev.get("type") == "done":
                break

    return StreamingResponse(stream(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


# ---------------- intelligence telemetry & audit (hackathon judge) ----------------
from ..services import intelligence_audit

@router.get("/intelligence/runs")
async def get_intelligence_runs():
    return {"runs": await intelligence_audit.list_audit_runs()}

@router.get("/intelligence/runs/{run_id}")
async def get_intelligence_run(run_id: str):
    run = await intelligence_audit.get_audit_run(run_id)
    if not run:
        raise HTTPException(404, "Audit run not found")
    return run

@router.get("/intelligence/latest")
async def get_latest_intelligence():
    run = await intelligence_audit.get_latest_audit_run()
    if not run:
        return {"run": None}
    return run
