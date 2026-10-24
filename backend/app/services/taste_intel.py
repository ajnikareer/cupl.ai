"""Taste Intelligence: the single entry point that turns human words into QLOO-grounded tastes.

"I like Arijit Singh"  ->  extract (LLM, structured)  ->  {mention:"Arijit Singh", category:music, kind:entity}
                       ->  resolve (QLOO /search types=artist, fuzzy-name scoring, LLM disambiguation if close)
                       ->  {status: resolved, entity_id: ..., name: "Arijit Singh", type: urn:entity:artist}
Only RESOLVED entity/tag IDs are ever sent to QLOO as signals. Unresolved text is kept as context for the
LLM planner and retried later by the learning worker. Ambiguous matches are returned so the agent can ask.
"""
import difflib
import logging
import re
import unicodedata

from ..core.llm import gen_json
from . import qloo

log = logging.getLogger("taste_intel")

# category -> (QLOO entity types tried in order, human label)
CATEGORIES: dict[str, dict] = {
    "music":      {"types": [qloo.ARTIST], "label": "singers, bands & music"},
    "film":       {"types": [qloo.MOVIE], "label": "movies"},
    "tv":         {"types": [qloo.TV], "label": "TV & web series"},
    "book":       {"types": [qloo.BOOK], "label": "books"},
    "podcast":    {"types": [qloo.PODCAST], "label": "podcasts"},
    "fashion":    {"types": [qloo.BRAND], "label": "fashion designers & brands"},
    "travel":     {"types": [qloo.DEST], "label": "destinations"},
    "place":      {"types": [qloo.PLACE], "label": "restaurants, cafes, hotels & venues"},
    "celebrity":  {"types": [qloo.PERSON], "label": "celebrities & style icons"},
    "game":       {"types": [qloo.GAME], "label": "games"},
    "food":       {"types": [], "label": "cuisines & dishes"},
    "experience": {"types": [], "label": "experiences & activities"},
}
TYPE_TO_CATEGORY = {t: c for c, v in CATEGORIES.items() for t in v["types"]}
CATEGORY_NAMES = list(CATEGORIES)

EXTRACT_SCHEMA = {
    "type": "OBJECT",
    "properties": {"items": {"type": "ARRAY", "items": {"type": "OBJECT", "properties": {
        "mention": {"type": "STRING", "description": "The exact name or phrase, cleaned (e.g. 'Arijit Singh', 'Sufi', 'Goa')"},
        "kind": {"type": "STRING", "enum": ["entity", "genre_or_style", "preference"]},
        "category": {"type": "STRING", "enum": CATEGORY_NAMES},
        "sentiment": {"type": "NUMBER", "description": "-1 strong dislike .. +1 love"},
        "about": {"type": "STRING", "enum": ["self", "partner"]},
        "confidence": {"type": "NUMBER"},
        "context_hint": {"type": "STRING", "description": "words that help identify it, e.g. 'singer', '2001 film', 'designer'"},
    }, "required": ["mention", "kind", "category", "sentiment", "about", "confidence"]}}},
    "required": ["items"],
}

EXTRACT_PROMPT = """You extract TASTES from what a person said to their wedding/couple planner.
Return every distinct taste mentioned (likes AND dislikes). Do not invent anything not said.

Categories: {cats}
kind: "entity" = a specific named thing (artist, film, brand, destination, restaurant, book, show, person);
      "genre_or_style" = a genre/cuisine/style ("Sufi", "Italian food", "minimalist", "boho");
      "preference" = a general preference ("loud DJs", "crowded beaches", "early mornings").
about: "partner" if they describe their partner's taste ("Priya loves Sabyasachi"), else "self".
Infer the category from world knowledge: a singer/band/composer -> music; a designer/label -> fashion;
a city/country/beach region -> travel; a specific restaurant/cafe/hotel -> place; a dish/cuisine -> food.
If a name is a person who is BOTH (e.g. an actor-singer), choose the category implied by the sentence.

Examples:
"I like Arijit Singh" -> [{{mention:"Arijit Singh", kind:"entity", category:"music", sentiment:0.7, about:"self", confidence:0.95, context_hint:"singer"}}]
"big Sufi fan, but please no loud DJs" -> [{{mention:"Sufi", kind:"genre_or_style", category:"music", sentiment:0.8, ...}}, {{mention:"loud DJ music", kind:"preference", category:"music", sentiment:-0.8, ...}}]
"Karan is obsessed with Dil Chahta Hai" -> [{{mention:"Dil Chahta Hai", kind:"entity", category:"film", about:"partner", context_hint:"2001 Hindi film", ...}}]
"we both love Goa and Italian food" -> [{{mention:"Goa", kind:"entity", category:"travel", ...}}, {{mention:"Italian", kind:"genre_or_style", category:"food", ...}}]
"Sabyasachi for sure" (answering 'which designers do you love?') -> [{{mention:"Sabyasachi", kind:"entity", category:"fashion", ...}}]

{hint}
Speaker: {speaker}. Partner: {partner}.
Text: \"\"\"{text}\"\"\""""


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    s = re.sub(r"\b(the|a|an)\b", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def name_similarity(a: str, b: str) -> float:
    na, nb = _norm(a), _norm(b)
    if not na or not nb:
        return 0.0
    if na == nb:
        return 1.0
    ratio = difflib.SequenceMatcher(None, na, nb).ratio()
    ta, tb = set(na.split()), set(nb.split())
    contain = len(ta & tb) / max(1, len(ta))  # how much of what the user said is in the candidate
    if na in nb or nb in na:
        ratio = max(ratio, 0.86 if contain == 1 else 0.75)
    return round(max(ratio, 0.9 * contain if len(ta) > 1 else ratio), 3)


async def extract(text: str, speaker: str = "the user", partner: str = "their partner",
                  category_hint: str | None = None) -> list[dict]:
    hint = (f"The planner had just asked about: {category_hint} ({CATEGORIES.get(category_hint, {}).get('label', '')}). "
            "Short answers refer to that category.") if category_hint else ""
    data = await gen_json(EXTRACT_PROMPT.format(cats=", ".join(f"{k} ({v['label']})" for k, v in CATEGORIES.items()),
                                                hint=hint, speaker=speaker, partner=partner, text=text[:3000]),
                          EXTRACT_SCHEMA, temperature=0.0)
    out = []
    for it in data.get("items", [])[:15]:
        m = (it.get("mention") or "").strip()
        if not m or it.get("category") not in CATEGORIES:
            continue
        it["mention"] = m[:100]
        it["sentiment"] = max(-1.0, min(1.0, float(it.get("sentiment", 0.7))))
        it["confidence"] = max(0.0, min(1.0, float(it.get("confidence", 0.7))))
        out.append(it)
    return out


DISAMBIG_SCHEMA = {"type": "OBJECT", "properties": {
    "choice": {"type": "INTEGER", "description": "index of the matching candidate, or -1 if none / unsure"},
    "certainty": {"type": "NUMBER"}}, "required": ["choice", "certainty"]}


async def _llm_pick(mention: str, hint: str, category: str, cands: list[dict]) -> tuple[int, float]:
    lines = "\n".join(f"{i}. {c['name']} | types: {', '.join(t.split(':')[-1] for t in c['types'])} | "
                      f"{c.get('year') or ''} {c.get('disambiguation') or ''} {c.get('description', '')[:120]}"
                      for i, c in enumerate(cands))
    data = await gen_json(
        f"A person mentioned '{mention}' ({hint or category}) as a taste in the category '{category}'. "
        f"Which candidate is it? Prefer the most famous/likely one for an Indian couple unless context says otherwise. "
        f"Return -1 if none matches.\n{lines}", DISAMBIG_SCHEMA, temperature=0.0)
    return int(data.get("choice", -1)), float(data.get("certainty", 0))


def _pack(status, mention, category, cand=None, candidates=None, tag=None, reason=""):
    r = {"status": status, "mention": mention, "category": category, "reason": reason}
    if cand:
        r.update({"entity_id": cand["entity_id"], "name": cand["name"], "qloo_type": (cand["types"] or [None])[0],
                  "image": cand.get("image")})
        cat = TYPE_TO_CATEGORY.get(r["qloo_type"])
        if cat:
            r["category"] = cat
    if tag:
        r.update({"tag_id": tag["tag_id"], "name": tag["name"]})
    if candidates:
        r["candidates"] = [{"entity_id": c["entity_id"], "name": c["name"], "image": c.get("image"),
                            "label": f"{c['name']}" + (f" ({c['year']})" if c.get("year") else "") +
                                     (f" · {c['types'][0].split(':')[-1].replace('_', ' ')}" if c.get("types") else ""),
                            "qloo_type": (c["types"] or [None])[0]} for c in candidates[:4]]
    return r


async def resolve(mention: str, category: str, kind: str = "entity", hint: str = "") -> dict:
    """Map a mention to a QLOO entity (or tag). Never raises for QLOO outages: returns unresolved."""
    types = CATEGORIES.get(category, {}).get("types", [])
    try:
        if kind == "entity" and types:
            cands = await qloo.search(mention, types, take=6)
            if not cands:  # wrong category guess? search across all entity types
                cands = [c for c in await qloo.search(mention, None, take=6) if set(c["types"]) & set(qloo.ENTITY_TYPES)]
            scored = sorted(((name_similarity(mention, c["name"]), i, c) for i, c in enumerate(cands)),
                            key=lambda x: (-x[0], x[1]))
            if scored:
                best_s, _, best = scored[0]
                close = [c for s, _, c in scored if s >= best_s - 0.05 and s >= 0.75]
                same_name = len({_norm(c["name"]) for c in close}) < len(close)
                if best_s >= 0.92 and (len(close) == 1 or not same_name):
                    return _pack("resolved", mention, category, best, reason=f"name match {best_s}")
                if best_s >= 0.6:
                    pool = [c for s, _, c in scored if s >= 0.6][:5]
                    idx, cert = await _llm_pick(mention, hint, category, pool)
                    if 0 <= idx < len(pool) and cert >= 0.7:
                        return _pack("resolved", mention, category, pool[idx], reason=f"llm pick {cert}")
                    return _pack("ambiguous", mention, category, candidates=pool, reason="several close matches")
                if kind == "entity":
                    # nicknames / abbreviations ("DDLJ", "SRK", "Bhai"): QLOO search often still ranks the right one first
                    pool = cands[:3]
                    idx, cert = await _llm_pick(mention, hint + " (may be a nickname or abbreviation)", category, pool)
                    if 0 <= idx < len(pool) and cert >= 0.85:
                        return _pack("resolved", mention, category, pool[idx], reason=f"alias pick {cert}")
            # fall through: maybe it's a genre/style said as an entity
        if kind in ("genre_or_style", "entity") or category in ("food", "music", "fashion", "experience"):
            tags = await qloo.search_tags(mention, take=5)
            good = [t for t in tags if name_similarity(mention, t["name"]) >= 0.8]
            if good:
                return _pack("resolved", mention, category, tag=good[0], reason="tag match")
    except qloo.QlooError as e:
        log.warning("resolve '%s' failed: %s", mention, e)
        return _pack("unresolved", mention, category, reason="taste service unavailable; will retry")
    return _pack("unresolved", mention, category, reason="no QLOO match; kept as text")
