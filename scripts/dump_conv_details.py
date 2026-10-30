import asyncio
import sys

sys.path.insert(0, ".")
sys.path.insert(0, "backend")

from backend.app.db import db

async def dump_conv():
    async for c in db.collection("conversations").stream():
        print(f"\n==================== CONVERSATION: {c.id} ====================")
        turns = []
        async for t in c.reference.collection("turns").order_by("ts").stream():
            td = t.to_dict()
            role = td.get('role')
            ts = td.get('ts')
            text = td.get('text') or td.get('content')
            print(f"[{ts}] {role}: {text}")

asyncio.run(dump_conv())
