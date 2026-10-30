import asyncio
import os
import sys

sys.path.insert(0, ".")
sys.path.insert(0, "backend")

from backend.app.db import db

async def dump():
    print("=== USERS ===")
    async for u in db.collection("users").stream():
        d = u.to_dict()
        print(f"User: {u.id} -> name={d.get('name')}, email={d.get('email')}, couple_id={d.get('couple_id')}, active_space={d.get('active_space')}")

    print("\n=== SPACES ===")
    async for s in db.collection("spaces").stream():
        d = s.to_dict()
        print(f"Space: {s.id} -> type={d.get('type')}, name={d.get('name')}, city={d.get('city')}, couple_id={d.get('couple_id')}")

    print("\n=== COUPLES ===")
    async for c in db.collection("couples").stream():
        d = c.to_dict()
        print(f"Couple: {c.id} -> uids={d.get('uids')}, names={d.get('names')}, invite_code={d.get('invite_code')}")

    # Inspect space s_ed4cb5ef34c5720e
    space_doc = await db.document("spaces/s_ed4cb5ef34c5720e").get()
    if space_doc.exists:
        print("\n=== SPACE s_ed4cb5ef34c5720e ===")
        print(space_doc.to_dict())

    # Inspect conversation for users
    print("\n=== CONVERSATIONS ===")
    async for c in db.collection("conversations").stream():
        print(f"Conv: {c.id}")
        async for t in c.reference.collection("turns").order_by("created_at").stream():
            td = t.to_dict()
            print(f"  [{td.get('role')}]: {td.get('content')}")

    # Inspect plan for s_ed4cb5ef34c5720e
    plan_doc = await db.document("spaces/s_ed4cb5ef34c5720e/plan/current").get()
    if plan_doc.exists:
        pd = plan_doc.to_dict()
        print("\n=== PLAN SECTIONS ===")
        for sec, val in pd.get("sections", {}).items():
            print(f"\n--- Section: {sec} ---")
            print("Summary:", val.get("summary"))
            items = val.get("items", [])
            for it in items[:4]:
                print(f"  * {it.get('title')}: {it.get('description')} (why: {it.get('why')})")

asyncio.run(dump())

