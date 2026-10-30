import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath("."))
from backend.app.db import db

async def wipe_everything():
    print("Beginning 100% clean wipe of all demo, test, and showcase data...")

    # 1. Wipe all users & subcollections
    user_count = 0
    async for snap in db.collection("users").stream():
        uid = snap.id
        print(f"Cleaning user {uid}...")
        async for tsnap in db.collection(f"users/{uid}/tastes").stream():
            await db.document(f"users/{uid}/tastes/{tsnap.id}").delete()
        await db.document(f"users/{uid}").delete()
        user_count += 1
    print(f"Deleted {user_count} users and their tastes.")

    # 2. Wipe all conversations & turns
    conv_count = 0
    async for snap in db.collection("conversations").stream():
        cid = snap.id
        async for tsnap in db.collection(f"conversations/{cid}/turns").stream():
            await db.document(f"conversations/{cid}/turns/{tsnap.id}").delete()
        await db.document(f"conversations/{cid}").delete()
        conv_count += 1
    print(f"Deleted {conv_count} conversations and turns.")

    # 3. Wipe all spaces & plans
    space_count = 0
    async for snap in db.collection("spaces").stream():
        sid = snap.id
        async for psnap in db.collection(f"spaces/{sid}/plans").stream():
            await db.document(f"spaces/{sid}/plans/{psnap.id}").delete()
        await db.document(f"spaces/{sid}").delete()
        space_count += 1
    print(f"Deleted {space_count} spaces and plans.")

    # 4. Wipe all couples
    couple_count = 0
    async for snap in db.collection("couples").stream():
        await db.document(f"couples/{snap.id}").delete()
        couple_count += 1
    print(f"Deleted {couple_count} couples.")

    # 5. Wipe calendar_items
    cal_count = 0
    async for snap in db.collection("calendar_items").stream():
        await db.document(f"calendar_items/{snap.id}").delete()
        cal_count += 1
    print(f"Deleted {cal_count} calendar items.")

    # 6. Wipe surprises
    surp_count = 0
    async for snap in db.collection("surprises").stream():
        await db.document(f"surprises/{snap.id}").delete()
        surp_count += 1
    print(f"Deleted {surp_count} surprises.")

    # 7. Wipe notifications
    notif_count = 0
    async for snap in db.collection("notifications").stream():
        await db.document(f"notifications/{snap.id}").delete()
        notif_count += 1
    print(f"Deleted {notif_count} notifications.")

    print("\nDatabase is now 100% PRISTINE AND EMPTY. Ready for fresh live signup!")

if __name__ == "__main__":
    asyncio.run(wipe_everything())

