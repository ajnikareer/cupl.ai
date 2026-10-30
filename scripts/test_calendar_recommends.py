import asyncio
import sys
import os

sys.path.insert(0, "backend")

from app.db import get_doc
from app.services import calendar_svc, recommends_svc

async def test():
    u = await get_doc("users/ajnikarnarayan")
    print("Testing Calendar for ajnikarnarayan...")
    cal = await calendar_svc.get_couple_calendar(u)
    print("Calendar unified events count:", len(cal.get("unified", [])))
    print("Countdowns:", [f"{x['title']}: {x['days_left']}d" for x in cal.get("countdowns", [])])
    print("Conflicts:", len(cal.get("conflicts", [])))
    for c in cal.get("conflicts", []):
        print("  CONFLICT:", c["event1"]["title"], "overlaps with", c["event2"]["title"], "on", c["overlap_dates"])

    print("\nTesting Recommends for ajnikarnarayan...")
    rec = await recommends_svc.get_lifestyle_recommendations(u)
    print("Couple recs count:", len(rec.get("couple_recs", [])))
    for r in rec.get("couple_recs", []):
        print(" -", r["title"], "| added?", r["added_to_calendar"])
    print("Private recs count:", len(rec.get("private_recs", [])))

    print("\nTesting Calendar Toggle for recommendation rec_dining_saturday...")
    r_item = rec["couple_recs"][1]
    res_toggle = await calendar_svc.toggle_recommendation_in_calendar(u, r_item["id"], {
        "title": r_item["title"],
        "category": r_item["category"],
        "date": r_item["suggested_date"],
        "description": r_item["description"],
        "maps_url": r_item.get("maps_url")
    })
    print("Toggle result 1 (Added):", res_toggle)

    cal2 = await calendar_svc.get_couple_calendar(u)
    print("Calendar unified after toggle:", len(cal2["unified"]))

    res_toggle2 = await calendar_svc.toggle_recommendation_in_calendar(u, r_item["id"], {})
    print("Toggle result 2 (Removed):", res_toggle2)

if __name__ == "__main__":
    asyncio.run(test())
