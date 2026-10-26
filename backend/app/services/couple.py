import secrets
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException

from ..config import settings
from ..db import db, get_doc, list_col


async def get_couple(cid: str) -> dict:
    c = await get_doc(f"couples/{cid}")
    if not c:
        raise HTTPException(404, "Couple not found")
    return c


def partner_uid(couple: dict, uid: str) -> str | None:
    others = [m for m in (couple or {}).get("members", []) if m != uid]
    return others[0] if others else None


async def create_invite(user: dict) -> dict:
    couple = await get_couple(user["couple_id"])
    if len(couple["members"]) >= 2:
        raise HTTPException(400, "Your partner has already joined.")
    code = couple.get("invite_code")
    exp = couple.get("invite_expires") or ""
    if not code or exp < datetime.now(timezone.utc).isoformat():
        code = secrets.token_urlsafe(8)[:10]
        exp = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
        await db.document(f"couples/{couple['id']}").update({"invite_code": code, "invite_expires": exp})
    return {"code": code, "link": f"{settings.APP_PUBLIC_URL.rstrip('/')}/join/{code}", "expires_at": exp}


async def join(user: dict, code: str) -> dict:
    target = None
    async for s in db.collection("couples").where("invite_code", "==", code).limit(1).stream():
        target = s.to_dict()
        target["id"] = s.id
    if not target:
        raise HTTPException(404, "Invite not found or already used")
    if user["uid"] in target["members"]:
        return target
    if target.get("invite_expires", "") < datetime.now(timezone.utc).isoformat():
        raise HTTPException(400, "Invite expired — ask your partner for a new link")
    if len(target["members"]) >= 2:
        raise HTTPException(400, "This couple already has two members")
    old_cid = user["couple_id"]
    async for s in db.collection("spaces").where("couple_id", "==", old_cid).stream():
        await s.reference.update({"couple_id": target["id"]})
    async for s in db.collection("episodes").where("couple_id", "==", old_cid).stream():
        await s.reference.update({"couple_id": target["id"]})
    members = target["members"] + [user["uid"]]
    await db.document(f"couples/{target['id']}").update({"members": members, "invite_code": None, "invite_expires": None})
    upd = {"couple_id": target["id"]}
    if True:
        # give the joining partner the couple's current event so they land right in it
        inviter = await get_doc(f"users/{target['members'][0]}") or {}
        if inviter.get("active_space_id"):
            upd["active_space_id"] = inviter["active_space_id"]
            user["active_space_id"] = inviter["active_space_id"]
    await db.document(f"users/{user['uid']}").update(upd)
    if old_cid != target["id"]:
        await db.document(f"couples/{old_cid}").delete()
    user["couple_id"] = target["id"]
    target["members"] = members
    return target


async def decisions(cid: str, limit: int = 30) -> list[dict]:
    items = await list_col(db.collection(f"couples/{cid}/decisions"), limit=200)
    items.sort(key=lambda x: x.get("at", ""), reverse=True)
    return items[:limit]
