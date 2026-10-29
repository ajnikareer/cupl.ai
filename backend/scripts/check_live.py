"""Live smoke test against REAL QLOO + Gemini + Firestore (no app server needed).

    cd backend && python -m scripts.check_live            # uses backend/.env

Verifies the critical input path ("I like Arijit Singh" -> music -> exact QLOO artist), QLOO recommendations,
tag search, the planner/extraction models, embeddings, and that the Live voice model accepts our config."""
import asyncio
import sys
import time

from app.config import settings
from app.core import llm
from app.services import qloo, taste_intel

SENTENCES = [
    ("I like Arijit Singh", None),
    ("big Sufi fan, but please no loud DJs", None),
    ("Karan is obsessed with Dil Chahta Hai", None),
    ("we both love Goa and Italian food", None),
    ("Sabyasachi for sure", "fashion"),
    ("DDLJ is my comfort movie", None),
]
ok_all = True


def show(name, ok, detail="", ms=None):
    global ok_all
    ok_all &= ok
    print(f"{'✅' if ok else '❌'} {name:<38} {f'{ms:>5.0f}ms ' if ms is not None else ''}{detail}")


async def timed(coro):
    t0 = time.perf_counter()
    r = await coro
    return r, (time.perf_counter() - t0) * 1000


async def main():
    if sys.stdout.encoding and sys.stdout.encoding.lower().startswith('cp'):
        sys.stdout.reconfigure(encoding='utf-8')
    if sys.stderr.encoding and sys.stderr.encoding.lower().startswith('cp'):
        sys.stderr.reconfigure(encoding='utf-8')
    print(f"QLOO {settings.QLOO_BASE_URL} | Vertex {settings.GCP_PROJECT}/{settings.VERTEX_LOCATION}\n")
    try:
        r, ms = await timed(qloo.search("Arijit Singh", [qloo.ARTIST], 5))
        show("QLOO /search (artist)", bool(r), ", ".join(x["name"] for x in r[:3]), ms)
        ids = [r[0]["entity_id"]] if r else []
        for t in (qloo.ARTIST, qloo.DEST, qloo.BRAND, qloo.MOVIE):
            r2, ms = await timed(qloo.insights(t, ids, take=5))
            show(f"QLOO /v2/insights {t.split(':')[-1]}", bool(r2), ", ".join(x["name"] for x in r2[:3]), ms)
        r3, ms = await timed(qloo.insights(qloo.PLACE, ids, location="Udaipur", take=5))
        show("QLOO /v2/insights place@Udaipur", bool(r3), ", ".join(x["name"] for x in r3[:3]), ms)
        try:
            r4, ms = await timed(qloo.search_tags("Sufi"))
            show("QLOO /v2/tags (optional)", True, ", ".join(f"{x['name']}={x['tag_id']}" for x in r4[:2]) or "no tags (ok: kept as text)", ms)
        except Exception as e:  # noqa
            show("QLOO /v2/tags (optional)", True, f"not available ({e}); genres stay as text")
    except Exception as e:  # noqa
        show("QLOO", False, str(e))

    print("\n— Taste intelligence (extract → resolve) —")
    for text, hint in SENTENCES:
        await asyncio.sleep(0.8)
        try:
            items, ms = await timed(taste_intel.extract(text, "Priya", "Karan", hint))
            res = await asyncio.gather(*[taste_intel.resolve(i["mention"], i["category"], i["kind"], i.get("context_hint") or "") for i in items])
            desc = "; ".join(f"{i['mention']}→{r['category']}/{r['status']}" + (f"={r.get('name')}" if r.get("name") else "") +
                             (" (partner)" if i["about"] == "partner" else "") + (" ✗" if i["sentiment"] < 0 else "") for i, r in zip(items, res))
            show(f"“{text[:34]}”", bool(items), desc, ms)
        except Exception as e:  # noqa
            show(f"“{text[:34]}”", False, str(e))

    print("\n— Gemini —")
    try:
        r, ms = await timed(llm.gen_json("Say ok", {"type": "OBJECT", "properties": {"ok": {"type": "BOOLEAN"}}, "required": ["ok"]},
                                         model=settings.GEMINI_PLANNER_MODEL, thinking=None))
        show(f"planner {settings.GEMINI_PLANNER_MODEL}", r.get("ok") is True, "", ms)
        v, ms = await timed(llm.embed("sunset dinner in Goa"))
        show(f"embeddings {settings.GEMINI_EMBED_MODEL}", len(v) == settings.EMBED_DIM, f"dim={len(v)}", ms)
    except Exception as e:  # noqa
        show("Gemini", False, str(e))
    try:
        from google.genai import types
        from app.agent.live import _config
        t0 = time.perf_counter()
        cfg = _config("You are a friendly test voice. Reply with one word.", None, None, set())
        async with llm.client.aio.live.connect(model=settings.GEMINI_LIVE_MODEL, config=cfg) as s:
            await s.send_client_content(turns=types.Content(role="user", parts=[types.Part(text="Say hello")]), turn_complete=True)
            got = 0
            async for resp in s.receive():
                if resp.server_content and resp.server_content.model_turn:
                    got += 1
                if resp.server_content and resp.server_content.turn_complete:
                    break
        show(f"Live voice {settings.GEMINI_LIVE_MODEL}", got > 0, "affective+proactive+VAD config accepted",
             (time.perf_counter() - t0) * 1000)
    except Exception as e:  # noqa
        show(f"Live voice {settings.GEMINI_LIVE_MODEL}", False,
             f"{e} — app will auto-drop optional features; if the model name is wrong, fix GEMINI_LIVE_MODEL")
    print("\nALL GOOD ✅" if ok_all else "\nSome checks failed ❌ — fix before demo")
    await qloo.http().aclose()
    sys.exit(0 if ok_all else 1)


if __name__ == "__main__":
    asyncio.run(main())
