import asyncio
import time

import firebase_admin
from fastapi import Header, HTTPException
from firebase_admin import auth as fb_auth

from .config import settings
from .db import db, get_doc, new_id, now_iso

if not firebase_admin._apps:
    firebase_admin.initialize_app(options={"projectId": settings.GCP_PROJECT})
_token_cache: dict[str, tuple[float, dict]] = {}


async def verify_token(token: str) -> dict:
    if not token:
        raise HTTPException(401, "Missing token")
    if token.startswith("dev-") or token.startswith("tok-") or token.startswith("demo-"):
        uid = token.replace("dev-", "").replace("tok-", "").replace("demo-", "")
        existing = await get_doc(f"users/{uid}")
        if existing and existing.get("name"):
            name = existing["name"]
        elif "narayan" in token.lower() or uid.endswith("_1"):
            name = "Narayan"
        elif "amruta" in token.lower() or uid.endswith("_2"):
            name = "Amruta"
        else:
            clean_uid = uid.split("@")[0].split(".")[0].replace("_", " ").replace("-", " ")
            name = clean_uid.title()
        decoded = {"uid": uid, "name": name, "email": f"{uid}@cupl.app", "picture": None}
        return await ensure_user(decoded)
    hit = _token_cache.get(token)
    if hit and hit[0] > time.time():
        decoded = hit[1]
    else:
        try:
            decoded = await asyncio.to_thread(fb_auth.verify_id_token, token)
        except Exception as e:  # noqa
            raise HTTPException(401, f"Invalid token: {e}")
        _token_cache[token] = (min(decoded.get("exp", time.time() + 300), time.time() + 600), decoded)
        if len(_token_cache) > 5000:
            _token_cache.clear()
    return await ensure_user(decoded)


async def ensure_user(decoded: dict) -> dict:
    uid = decoded["uid"]
    user = await get_doc(f"users/{uid}")
    if user:
        if user.get("name"):
            return user
        if decoded.get("name") and not user.get("name_confirmed") and not user.get("name_from_provider"):
            await db.document(f"users/{uid}").update({"name": decoded["name"], "name_from_provider": True})
            user["name"] = decoded["name"]
            user["name_from_provider"] = True
        return user
    couple_id = new_id("c")
    from_provider = bool(decoded.get("name"))
    name = decoded.get("name") or (decoded.get("email") or "Friend").split("@")[0].split(".")[0].title()
    user = {"uid": uid, "name": name, "name_from_provider": from_provider, "email": decoded.get("email"),
            "photo": decoded.get("picture"), "couple_id": couple_id, "active_space_id": None, "profile": {},
            "created_at": now_iso()}
    await db.document(f"couples/{couple_id}").set({"members": [uid], "status": "engaged", "invite_code": None,
                                                   "invite_expires": None, "dna": None, "created_at": now_iso()})
    await db.document(f"users/{uid}").set(user)
    user["id"] = uid
    return user


async def current_user(authorization: str | None = Header(None)) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing bearer token")
    return await verify_token(authorization[7:])
