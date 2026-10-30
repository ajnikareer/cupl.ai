import asyncio
import sys

sys.path.insert(0, ".")
sys.path.insert(0, "backend")

from backend.app.db import db
from backend.app.services.tastes import facts, signals

async def check():
    fs = await facts("ajnikarnarayan")
    print(f"Facts for ajnikarnarayan: {len(fs)}")
    for f in fs:
        print(f"  * [{f.get('category')}] '{f.get('text')}' (sentiment={f.get('sentiment')}, entity_id={f.get('entity_id')}, tag_id={f.get('tag_id')}, resolution={f.get('resolution')})")
    sig = signals(fs)
    print("Signals:", sig)

asyncio.run(check())

