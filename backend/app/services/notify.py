from ..db import db, new_id, now_iso


async def notify(uid: str, text: str, link: str | None = None, kind: str = "info"):
    await db.document(f"notifications/{new_id('n')}").set(
        {"uid": uid, "text": text, "link": link, "kind": kind, "read": False, "created_at": now_iso()})


async def notify_many(uids: list[str], text: str, link: str | None = None, kind: str = "info"):
    for u in uids:
        await notify(u, text, link, kind)
