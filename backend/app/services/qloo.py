"""QLOO Insights API client. Live only: errors surface, nothing is faked.

Endpoints used (QLOO Insights API v2):
  GET /search?query=&types=&take=             entity search (name -> entity_id)
  GET /v2/insights?filter.type=...&signal...   recommendations
  GET /v2/tags?filter.query=&take=             tag search (genres, cuisines, styles)
"""
import asyncio
import hashlib
import json
import logging
import time
from collections import OrderedDict
from datetime import datetime, timedelta, timezone

import httpx

from ..config import settings
from ..db import db

log = logging.getLogger("qloo")
_sem = asyncio.Semaphore(8)
_mem: "OrderedDict[str, tuple[float, dict]]" = OrderedDict()
_client: httpx.AsyncClient | None = None


class QlooError(Exception):
    pass


ARTIST, MOVIE, TV, BOOK, PODCAST, BRAND, DEST, PLACE, PERSON, GAME = (
    "urn:entity:artist", "urn:entity:movie", "urn:entity:tv_show", "urn:entity:book", "urn:entity:podcast",
    "urn:entity:brand", "urn:entity:destination", "urn:entity:place", "urn:entity:person", "urn:entity:videogame")
ENTITY_TYPES = [ARTIST, MOVIE, TV, BOOK, PODCAST, BRAND, DEST, PLACE, PERSON, GAME]


def http() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(timeout=settings.QLOO_TIMEOUT_S,
                                    limits=httpx.Limits(max_connections=20, max_keepalive_connections=10))
    return _client


def _image(props: dict):
    img = props.get("image")
    if isinstance(img, dict):
        return img.get("url")
    if isinstance(img, str):
        return img
    imgs = props.get("images")
    if isinstance(imgs, list) and imgs:
        first = imgs[0]
        return first.get("url") if isinstance(first, dict) else first
    return None


def norm_entity(e: dict) -> dict:
    props = e.get("properties") or {}
    q = e.get("query") if isinstance(e.get("query"), dict) else {}
    types_ = e.get("types") or ([e["type"]] if e.get("type") else [])
    desc = props.get("short_description") or props.get("description") or ""
    if isinstance(desc, list):
        desc = " ".join(str(x) for x in desc)
    year = props.get("release_year") or props.get("publication_year") or props.get("year")
    return {
        "entity_id": e.get("entity_id") or e.get("id"),
        "name": e.get("name"),
        "types": [t for t in types_ if isinstance(t, str)],
        "image": _image(props),
        "affinity": q.get("affinity"),
        "popularity": e.get("popularity"),
        "description": str(desc)[:240],
        "year": year,
        "address": props.get("address"),
        "price_level": props.get("price_level"),
        "tags": [t.get("name") for t in (e.get("tags") or [])[:8] if isinstance(t, dict) and t.get("name")],
        "disambiguation": e.get("disambiguation"),
    }


async def _get(path: str, params: dict, ttl_h: float | None = None) -> dict:
    ttl_h = ttl_h or settings.QLOO_CACHE_TTL_H
    key = hashlib.sha256((path + json.dumps(params, sort_keys=True)).encode()).hexdigest()
    now = time.time()
    if key in _mem and _mem[key][0] > now:
        _mem.move_to_end(key)
        return _mem[key][1]
    ref = db.document(f"qloo_cache/{key}")
    try:
        snap = await ref.get()
        if snap.exists:
            d = snap.to_dict()
            if d.get("expires_at", "") > datetime.now(timezone.utc).isoformat():
                data = json.loads(d["body"])
                _remember(key, data, ttl_h)
                return data
    except Exception as e:  # noqa  (cache must never break a call)
        log.warning("cache read failed: %s", e)
    url = settings.QLOO_BASE_URL.rstrip("/") + path
    headers = {"X-Api-Key": settings.QLOO_API_KEY, "accept": "application/json"}
    last = None
    t0 = time.perf_counter()
    async with _sem:
        for attempt in range(3):
            try:
                r = await http().get(url, params=params, headers=headers)
                if r.status_code in (429, 500, 502, 503, 504):
                    last = f"HTTP {r.status_code}"
                    await asyncio.sleep(0.5 * (2 ** attempt))
                    continue
                if r.status_code >= 400:
                    raise QlooError(f"QLOO {path} HTTP {r.status_code}: {r.text[:300]}")
                data = r.json()
                log.info("qloo %s %.0fms", path, (time.perf_counter() - t0) * 1000)
                _remember(key, data, ttl_h)
                body = json.dumps(data)
                if len(body) < 900_000:
                    try:
                        await ref.set({"body": body, "path": path, "expires_at": (
                            datetime.now(timezone.utc) + timedelta(hours=ttl_h)).isoformat()})
                    except Exception as e:  # noqa
                        log.warning("cache write failed: %s", e)
                return data
            except httpx.HTTPError as e:
                last = str(e) or e.__class__.__name__
                await asyncio.sleep(0.5 * (2 ** attempt))
    raise QlooError(f"QLOO unavailable: {last}")


def _remember(key, data, ttl_h):
    _mem[key] = (time.time() + min(ttl_h, 6) * 3600, data)
    while len(_mem) > 2000:
        _mem.popitem(last=False)


def _results(data) -> list:
    if isinstance(data, list):
        return data
    if not isinstance(data, dict):
        return []
    res = data.get("results")
    if isinstance(res, dict):
        return res.get("entities") or res.get("tags") or []
    return res or data.get("entities") or data.get("tags") or []


async def search(query: str, types: list[str] | None = None, take: int = 8) -> list[dict]:
    params = {"query": query.strip()[:100], "take": take}
    if types:
        params["types"] = ",".join(types)
    data = await _get("/search", params, ttl_h=24 * 7)
    return [norm_entity(e) for e in _results(data) if isinstance(e, dict) and e.get("name")]


async def search_tags(query: str, take: int = 6) -> list[dict]:
    data = await _get("/v2/tags", {"filter.query": query.strip()[:60], "take": take}, ttl_h=24 * 7)
    out = []
    for t in _results(data):
        if isinstance(t, dict) and (t.get("id") or t.get("tag_id")) and t.get("name"):
            out.append({"tag_id": t.get("id") or t.get("tag_id"), "name": t["name"], "type": t.get("type") or t.get("subtype")})
    return out


async def insights(qtype: str, entity_ids: list[str] | None = None, tag_ids: list[str] | None = None,
                   location: str | None = None, take: int = 20, age: str | None = None) -> list[dict]:
    params: dict = {"filter.type": qtype, "take": take}
    ids = [i for i in dict.fromkeys(entity_ids or []) if i][:25]
    tags = [t for t in dict.fromkeys(tag_ids or []) if t][:10]
    if ids:
        params["signal.interests.entities"] = ",".join(ids)
    if tags:
        params["signal.interests.tags"] = ",".join(tags)
    if location and qtype == PLACE:
        params["filter.location.query"] = location
    elif not ids and not tags:
        params["signal.location.query"] = location or settings.DEFAULT_REGION
    if age:
        params["signal.demographics.age"] = age
    data = await _get("/v2/insights", params)
    return [norm_entity(e) for e in _results(data) if isinstance(e, dict) and e.get("name")]


async def blend(qtype: str, partner_signals: dict[str, dict], location: str | None = None, take: int = 25,
                exclude: set | None = None) -> list[dict]:
    """Couple blending.
    partner_signals = {uid: {"entities": [...], "tags": [...]}}
    score = 0.5*joint + 0.25*each partner list; +0.15 if in both partners' lists ("loved by both")."""
    exclude = exclude or set()
    uids = [u for u, s in partner_signals.items() if s.get("entities") or s.get("tags")]
    all_e = [i for s in partner_signals.values() for i in s.get("entities", [])]
    all_t = [i for s in partner_signals.values() for i in s.get("tags", [])]
    calls = [insights(qtype, all_e, all_t, location, take)]
    if len(uids) == 2:
        calls += [insights(qtype, partner_signals[u].get("entities"), partner_signals[u].get("tags"), location, take)
                  for u in uids]
    results = await asyncio.gather(*calls, return_exceptions=True)
    if isinstance(results[0], Exception):
        raise results[0]
    joint, indiv = results[0], [r if not isinstance(r, Exception) else [] for r in results[1:]]
    scores: dict[str, dict] = {}
    for e in joint:
        if not e["entity_id"] or e["entity_id"] in exclude:
            continue
        scores[e["entity_id"]] = {**e, "score": 0.5 * (e.get("affinity") or 0.5), "matched": []}
    for idx, lst in enumerate(indiv):
        for e in lst:
            eid = e["entity_id"]
            if not eid or eid in exclude:
                continue
            if eid not in scores:
                scores[eid] = {**e, "score": 0.0, "matched": []}
            scores[eid]["score"] += 0.25 * (e.get("affinity") or 0.5)
            scores[eid]["matched"].append(uids[idx])
    out = list(scores.values())
    for e in out:
        e["loved_by_both"] = len(set(e["matched"])) >= 2
        if e["loved_by_both"]:
            e["score"] += 0.15
    out.sort(key=lambda x: x["score"], reverse=True)
    return out[:take]
