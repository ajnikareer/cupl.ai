"""Calendar Service: manages couple events, milestones, masterplan to-dos, and custom recommend items."""
import logging
from datetime import date, datetime, timedelta, timezone
from ..core.timeutil import today, now_iso
from ..db import db, get_doc, list_col, new_id
from . import spaces as sp

log = logging.getLogger("calendar_svc")

async def get_couple_calendar(user: dict) -> dict:
    cid = user["couple_id"]
    uid = user["uid"]

    # 1. Load all spaces
    spaces = await sp.list_spaces(cid)

    # 2. Extract todos across spaces
    todos = []
    for s in spaces:
        sid = s["id"]
        async for tsnap in db.collection(f"spaces/{sid}/todos").stream():
            td = tsnap.to_dict()
            td["id"] = tsnap.id
            td["space_id"] = sid
            td["space_title"] = s["title"]
            td["space_type"] = s["type"]
            todos.append(td)

    # 3. Load custom calendar items (including added recommendations)
    custom_items = []
    async for csnap in db.collection("calendar_items").where("couple_id", "==", cid).stream():
        cd = csnap.to_dict()
        cd["id"] = csnap.id
        if cd.get("is_private") and cd.get("created_by") != uid:
            continue  # preserve privacy of surprises
        custom_items.append(cd)

    # 4. Check for conflicts
    conflicts = []
    dated_spaces = [s for s in spaces if s.get("start_date")]
    for i in range(len(dated_spaces)):
        for j in range(i + 1, len(dated_spaces)):
            s1 = dated_spaces[i]
            s2 = dated_spaces[j]
            try:
                st1 = date.fromisoformat(s1["start_date"][:10])
                et1 = date.fromisoformat(s1["end_date"][:10]) if s1.get("end_date") else st1
                st2 = date.fromisoformat(s2["start_date"][:10])
                et2 = date.fromisoformat(s2["end_date"][:10]) if s2.get("end_date") else st2
                if max(st1, st2) <= min(et1, et2):
                    conflicts.append({
                        "event1": {"id": s1["id"], "title": s1["title"], "type": s1["type"], "dates": f"{st1} to {et1}" if st1 != et1 else str(st1)},
                        "event2": {"id": s2["id"], "title": s2["title"], "type": s2["type"], "dates": f"{st2} to {et2}" if st2 != et2 else str(st2)},
                        "overlap_dates": f"{max(st1, st2)} to {min(et1, et2)}" if max(st1, st2) != min(et1, et2) else str(max(st1, st2))
                    })
            except Exception as e:
                pass

    # 5. Calculate countdowns
    countdowns = []
    t_today = today()
    for s in dated_spaces:
        try:
            s_date = date.fromisoformat(s["start_date"][:10])
            diff = (s_date - t_today).days
            countdowns.append({
                "space_id": s["id"],
                "title": s["title"],
                "type": s["type"],
                "date": s["start_date"],
                "days_left": diff
            })
        except Exception:
            pass
    countdowns.sort(key=lambda x: (x["days_left"] < 0, abs(x["days_left"])))

    # 6. Build unified chronological event list
    unified = []
    for s in dated_spaces:
        unified.append({
            "id": s["id"],
            "item_type": "space",
            "title": s["title"],
            "category": s["type"],
            "start_date": s["start_date"],
            "end_date": s.get("end_date") or s["start_date"],
            "city": s.get("city") or s.get("destination"),
            "state": s.get("state"),
            "budget": s.get("budget"),
            "guests": s.get("guests")
        })

    for t in todos:
        if t.get("due"):
            unified.append({
                "id": t["id"],
                "item_type": "todo",
                "title": t["title"],
                "category": "todo",
                "start_date": t["due"],
                "end_date": t["due"],
                "done": t.get("done", False),
                "space_id": t["space_id"],
                "space_title": t["space_title"]
            })

    for ci in custom_items:
        unified.append({
            "id": ci["id"],
            "item_type": "custom",
            "title": ci["title"],
            "category": ci.get("category", "dining"),
            "start_date": ci["date"],
            "end_date": ci["date"],
            "time": ci.get("time"),
            "description": ci.get("description"),
            "maps_url": ci.get("maps_url"),
            "image": ci.get("image"),
            "recommendation_id": ci.get("recommendation_id"),
            "is_private": ci.get("is_private", False)
        })

    unified.sort(key=lambda x: str(x.get("start_date", "")))

    return {
        "unified": unified,
        "spaces": spaces,
        "todos": todos,
        "custom_items": custom_items,
        "conflicts": conflicts,
        "countdowns": countdowns
    }

async def add_calendar_item(user: dict, data: dict) -> dict:
    cid = user["couple_id"]
    uid = user["uid"]
    item_id = new_id("cal")
    item = {
        "id": item_id,
        "couple_id": cid,
        "created_by": uid,
        "title": str(data["title"])[:120],
        "category": data.get("category", "dining"),
        "date": str(data["date"])[:10],
        "time": str(data.get("time") or "")[:20] or None,
        "description": str(data.get("description") or "")[:300] or None,
        "recommendation_id": data.get("recommendation_id"),
        "maps_url": data.get("maps_url"),
        "image": data.get("image"),
        "is_private": bool(data.get("is_private", False)),
        "created_at": now_iso()
    }
    await db.document(f"calendar_items/{item_id}").set(item)
    return item

async def delete_calendar_item(user: dict, item_id: str) -> bool:
    doc = await get_doc(f"calendar_items/{item_id}")
    if not doc or doc.get("couple_id") != user["couple_id"]:
        return False
    await db.document(f"calendar_items/{item_id}").delete()
    return True

async def toggle_recommendation_in_calendar(user: dict, rec_id: str, rec_data: dict) -> dict:
    cid = user["couple_id"]
    # Check if this recommendation is already on the calendar
    existing = None
    async for s in db.collection("calendar_items").where("couple_id", "==", cid).where("recommendation_id", "==", rec_id).limit(1).stream():
        existing = s.to_dict()
        existing["id"] = s.id

    if existing:
        # Remove it
        await db.document(f"calendar_items/{existing['id']}").delete()
        return {"added": False, "item_id": existing["id"], "recommendation_id": rec_id}
    else:
        # Add it
        rec_data["recommendation_id"] = rec_id
        item = await add_calendar_item(user, rec_data)
        return {"added": True, "item": item, "recommendation_id": rec_id}

async def get_added_rec_ids(user: dict) -> list[str]:
    cid = user["couple_id"]
    ids = []
    async for s in db.collection("calendar_items").where("couple_id", "==", cid).stream():
        d = s.to_dict()
        if d.get("recommendation_id"):
            ids.append(d["recommendation_id"])
    return ids

