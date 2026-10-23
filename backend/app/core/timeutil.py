from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

from ..config import settings


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def local_now() -> datetime:
    return datetime.now(ZoneInfo(settings.APP_TZ))


def today() -> date:
    return local_now().date()


def valid_date(s) -> str | None:
    try:
        return date.fromisoformat(str(s)[:10]).isoformat()
    except (ValueError, TypeError):
        return None
