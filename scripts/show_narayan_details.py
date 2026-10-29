import asyncio
import sys

sys.path.insert(0, "backend")
from app.db import db

async def show():
    u = await db.document("users/narayan").get()
    if u.exists:
        print("USER NARAYAN:")
        for k, v in u.to_dict().items():
            print(f"  {k}: {v}")

    c = await db.document("couples/c_8c578b9cdf8e6d95").get()
    if c.exists:
        print("\nCOUPLE c_8c578b9cdf8e6d95:")
        for k, v in c.to_dict().items():
            print(f"  {k}: {v}")

    s = await db.document("spaces/s_8b4437164f0df241").get()
    if s.exists:
        print("\nSPACE s_8b4437164f0df241:")
        for k, v in s.to_dict().items():
            print(f"  {k}: {v}")

if __name__ == "__main__":
    asyncio.run(show())

