import asyncio
import sys

sys.path.insert(0, ".")
sys.path.insert(0, "backend")

from backend.app.config import settings
settings.QLOO_API_KEY = "hack_2e9a0b569f352f79299887692053d2cae44c293c"

from backend.app.services import qloo
from backend.app.services.tastes import facts, signals
from backend.app.services.spaces import TEMPLATES

async def run_blend():
    fs = await facts("ajnikarnarayan")
    sig = signals(fs)
    print("SIGNALS COUNT:", len(sig["entities"]))
    tmpl = TEMPLATES["prewedding"]

    for sec in tmpl["sections"]:
        if sec["kind"] == "qloo":
            print(f"\n==================== {sec['title']} (qtype={sec['qtype']}) ====================")
            loc = "Hyderabad" if sec.get("location_field") == "city" else None
            res = await qloo.blend(sec["qtype"], {"ajnikarnarayan": sig}, loc, sec["take"])
            print(f"Candidates returned: {len(res)}")
            for c in res[:10]:
                print(f"  * {c.get('name')} | affinity: {round(c.get('affinity') or 0, 2)} | tags: {c.get('tags')[:4] if c.get('tags') else []}")

asyncio.run(run_blend())

