import asyncio
import sys

sys.path.insert(0, "backend")
from app.db import db

async def inspect():
    uids = ["narayan", "amruta"]
    print("=== USERS ===")
    couple_ids = set()
    for u in uids:
        doc = await db.document(f"users/{u}").get()
        if doc.exists:
            d = doc.to_dict()
            cid = d.get("couple_id")
            if cid:
                couple_ids.add(cid)
            print(f"User {u}: name={d.get('name')}, couple_id={cid}, active_space={d.get('active_space_id')}")
        else:
            print(f"User {u} does not exist.")

    print("\n=== COUPLES ===")
    async for c in db.collection("couples").stream():
        cd = c.to_dict()
        members = cd.get("members", [])
        if any(u in members for u in uids) or c.id in couple_ids:
            couple_ids.add(c.id)
            print(f"Couple {c.id}: members={members}, invite_code={cd.get('invite_code')}")

    print(f"\nTarget Couple IDs: {couple_ids}")

    print("\n=== SPACES ===")
    space_ids = set()
    async for s in db.collection("spaces").stream():
        sd = s.to_dict()
        cid = sd.get("couple_id")
        if cid in couple_ids:
            space_ids.add(s.id)
            print(f"Space {s.id}: title={sd.get('title')}, couple_id={cid}")

    print(f"\nTarget Space IDs: {space_ids}")

    print("\n=== EPISODES ===")
    ep_count = 0
    async for ep in db.collection("episodes").stream():
        epd = ep.to_dict()
        if epd.get("couple_id") in couple_ids or epd.get("user_id") in uids:
            ep_count += 1
    print(f"Episodes linked: {ep_count}")

    print("\n=== SURPRISES ===")
    sur_count = 0
    async for sur in db.collection("surprises").stream():
        surd = sur.to_dict()
        if surd.get("user_id") in uids or surd.get("couple_id") in couple_ids:
            sur_count += 1
    print(f"Surprises linked: {sur_count}")

    print("\n=== MEMORIES ===")
    mem_count = 0
    async for mem in db.collection("memories").stream():
        memd = mem.to_dict()
        if memd.get("couple_id") in couple_ids or memd.get("space_id") in space_ids:
            mem_count += 1
    print(f"Memories linked: {mem_count}")

    print("\n=== TODOS ===")
    todo_count = 0
    async for td in db.collection("todos").stream():
        tdd = td.to_dict()
        if tdd.get("space_id") in space_ids:
            todo_count += 1
    print(f"Todos linked: {todo_count}")

if __name__ == "__main__":
    asyncio.run(inspect())

