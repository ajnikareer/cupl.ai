import asyncio
import sys

sys.path.insert(0, "backend")
from app.db import db

async def delete_doc_recursive(doc_ref):
    # delete all subcollections
    async for subcol in doc_ref.collections():
        async for subdoc in subcol.stream():
            await delete_doc_recursive(subdoc.reference)
    await doc_ref.delete()

async def wipe():
    print("=== STARTING PERSONA WIPE FOR NARAYAN & AMRUTA ===")
    uids = ["narayan", "amruta"]

    couple_ids = set()
    space_ids = set()

    # 1. Find all couples linked to narayan or amruta
    for u in uids:
        udoc = await db.document(f"users/{u}").get()
        if udoc.exists:
            cid = udoc.to_dict().get("couple_id")
            if cid:
                couple_ids.add(cid)

    async for c in db.collection("couples").stream():
        cd = c.to_dict()
        members = cd.get("members", [])
        if any(u in members for u in uids):
            couple_ids.add(c.id)

    print(f"Found couples to delete: {couple_ids}")

    # 2. Find all spaces linked to these couples or users
    async for s in db.collection("spaces").stream():
        sd = s.to_dict()
        if sd.get("couple_id") in couple_ids or sd.get("created_by") in uids:
            space_ids.add(s.id)

    print(f"Found spaces to delete: {space_ids}")

    # 3. Delete spaces and their subcollections (plans, todos)
    for sid in space_ids:
        print(f"Deleting space: spaces/{sid}...")
        await delete_doc_recursive(db.document(f"spaces/{sid}"))

    # 4. Delete couples and their subcollections (decisions)
    for cid in couple_ids:
        print(f"Deleting couple: couples/{cid}...")
        await delete_doc_recursive(db.document(f"couples/{cid}"))

    # 5. Delete users and their subcollections (facts)
    for u in uids:
        print(f"Deleting user: users/{u}...")
        await delete_doc_recursive(db.document(f"users/{u}"))

    # 6. Delete linked episodes, surprises, memories, notifications
    for col_name in ["episodes", "surprises", "memories", "notifications"]:
        async for doc in db.collection(col_name).stream():
            d = doc.to_dict()
            if d.get("user_id") in uids or d.get("couple_id") in couple_ids or d.get("space_id") in space_ids:
                print(f"Deleting {col_name}/{doc.id}...")
                await delete_doc_recursive(doc.reference)

    print("=== PERSONA WIPE COMPLETE! ===")

if __name__ == "__main__":
    asyncio.run(wipe())

