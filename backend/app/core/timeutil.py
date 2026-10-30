import re
from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

from ..config import settings

MONTHS = {
    'jan': 1, 'january': 1, 'feb': 2, 'february': 2, 'mar': 3, 'march': 3,
    'apr': 4, 'april': 4, 'may': 5, 'jun': 6, 'june': 6, 'jul': 7, 'july': 7,
    'aug': 8, 'august': 8, 'sep': 9, 'september': 9, 'oct': 10, 'october': 10,
    'nov': 11, 'november': 11, 'dec': 12, 'december': 12
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def local_now() -> datetime:
    return datetime.now(ZoneInfo(settings.APP_TZ))


def today() -> date:
    return local_now().date()


def valid_date(s) -> str | None:
    if not s:
        return None
    raw = str(s).strip()
    try:
        return date.fromisoformat(raw[:10]).isoformat()
    except (ValueError, TypeError):
        pass

    clean = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', raw.lower())
    clean = re.sub(r'[^a-z0-9\s/-]', ' ', clean).strip()

    # Match DD-MM-YYYY or DD/MM/YYYY
    m = re.match(r'^(\d{1,2})[/-](\d{1,2})[/-](\d{4})$', clean)
    if m:
        try:
            return date(int(m.group(3)), int(m.group(2)), int(m.group(1))).isoformat()
        except ValueError:
            pass

    # Match words: e.g. "15 november 2026", "november 15 2026", "15 november"
    parts = clean.split()
    day, month, cur_year = None, None, today().year
    year = cur_year
    for p in parts:
        if p in MONTHS:
            month = MONTHS[p]
        elif p.isdigit():
            val = int(p)
            if 1900 < val < 2100:
                year = val
            elif 1 <= val <= 31 and day is None:
                day = val

    if month:
        day = day or 1
        try:
            target = date(year, month, day)
            if target < today() and year == cur_year:
                target = date(year + 1, month, day)
            return target.isoformat()
        except ValueError:
            return None
    return None

