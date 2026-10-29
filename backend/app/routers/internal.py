import hmac
from datetime import datetime, timezone

from fastapi import APIRouter, Header, HTTPException

from ..config import settings
from ..core.timeutil import today
from ..db import db
from ..services.notify import notify, notify_many

router = APIRouter(prefix="/internal")


@router.post("/cron/run")
async def cron(x_cron_secret: str | None = Header(None)):
    if not settings.CRON_SECRET or not x_cron_secret or not hmac.compare_digest(x_cron_secret, settings.CRON_SECRET):
        raise HTTPException(403, "forbidden")
    now = datetime.now(timezone.utc)
    sent = 0
    async for s in db.collection("reminders").where("sent", "==", False).stream():
        r = s.to_dict()
        try:
            due = datetime.fromisoformat(r.get("at", "").replace("Z", "+00:00"))
            if due.tzinfo is None:
                due = due.replace(tzinfo=timezone.utc)
        except ValueError:
            await s.reference.update({"sent": True, "error": "bad date"})
            continue
        if due <= now:
            await notify(r["uid"], f"⏰ {r['text']}", None, "reminder")
            await s.reference.update({"sent": True})
            sent += 1
    checkins, t = 0, today().isoformat()
    async for s in db.collection("spaces").where("state", "in", ["planned", "stale", "ready"]).stream():
        d = s.to_dict()
        end = d.get("end_date") or d.get("start_date")
        if end and end < t:
            await s.reference.update({"state": "completed"})
            c = (await db.document(f"couples/{d['couple_id']}").get()).to_dict() or {}
            await notify_many(c.get("members", []), f"💛 How was your {d.get('title')}? Tell me the highlights — "
                              "I'll remember them for next time.", "/app/chat", "checkin")
            checkins += 1
    return {"reminders_sent": sent, "checkins": checkins}
