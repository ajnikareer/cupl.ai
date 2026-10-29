import asyncio
import sys

sys.path.insert(0, "backend")
from app.db import db

async def check_subcollections():
    for path in ["users/narayan", "couples/c_8c578b9cdf8e6d95", "spaces/s_8b4437164f0df241"]:
        doc_ref = db.document(path)
        subcols = [c.id async for c in doc_ref.collections()]
        print(f"Subcollections in {path}: {subcols}")
        for sc in subcols:
            count = 0
            async for sdoc in doc_ref.collection(sc).stream():
                count += 1
            print(f"  {sc} count: {count}")

if __name__ == "__main__":
    asyncio.run(check_subcollections())

