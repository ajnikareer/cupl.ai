import asyncio
import sys
import os

sys.path.insert(0, "backend")

from app.db import get_doc, db
from app.services import spaces, plan_engine

async def main():
    u = await get_doc("users/ajnikarnarayan")
    cid = u["couple_id"]
    sid = "s_7589d6245e7d9cbf"
    print(f"Updating Wedding space {sid} for couple {cid}...")

    fields = {
        "title": "Narayan & Amruta's Royal Wedding",
        "city": "Hyderabad",
        "start_date": "2026-12-18",
        "end_date": "2026-12-20",
        "budget": 2500000.0,
        "guests": 350,
        "ceremonies": ["Haldi", "Mehendi", "Sangeet", "Wedding", "Reception"],
        "priorities": "Dual heritage Maharashtrian & North fusion with grand multi-generational Sangeet music, zero food waste, and clash-free royal aesthetics"
    }

    sp, errs = await spaces.update_space(sid, cid, fields)
    print("Space updated. State:", sp["state"], "Errors:", errs)

    # Set as active space for Narayan so it reflects on active view
    await db.document(f"users/{u['uid']}").update({"active_space_id": sid})
    print(f"Set active_space_id to {sid} for {u['uid']}")

    print("\n--- Starting Plan Engine Build for Wedding Space ---")
    plan = await plan_engine.build(sid, by_uid=u["uid"])
    print(f"Plan Version: {plan.get('version')} | Status: {plan.get('status')}")

    for sec in plan.get("sections", []):
        print(f"\n==========================================")
        print(f"SECTION: {sec.get('title')} ({sec.get('key')}) - {len(sec.get('items', []))} items")
        print(f"Summary: {sec.get('summary')}")
        print(f"==========================================")
        for idx, it in enumerate(sec.get("items", []), 1):
            print(f"[{idx}] {it.get('title')}")
            if it.get("act"):
                print(f"    🎶 Act: {it['act']} | Tempo: {it.get('tempo_bpm')} | Vibe: {it.get('vibe_tag')}")
            if it.get("artist_name"):
                print(f"    🎤 QLOO Artist: {it['artist_name']} | QLOO Match: {round((it.get('affinity') or 0)*100)}%")
            if it.get("cue_note"):
                print(f"    🎬 Cue: {it['cue_note']}")
            if it.get("course_type"):
                print(f"    🍽️ Course: {it['course_type']} | Heritage: {it.get('heritage_origin')}")
            if it.get("portion_math"):
                print(f"    🍃 Anti-Waste Math: {it['portion_math']}")
            if it.get("hex_colors"):
                print(f"    🎨 Hex Palette: {it['hex_colors']}")
            if it.get("bride_groom_pairing"):
                print(f"    👫 Styling: {it['bride_groom_pairing']}")
            if it.get("anti_clash_check"):
                print(f"    🛡️ Clash Check: {it['anti_clash_check']}")
            if it.get("lighting_spec"):
                print(f"    💡 Lighting: {it['lighting_spec']}")
            if it.get("capacity_check"):
                print(f"    👥 Capacity: {it['capacity_check']}")
            if it.get("budget_breakdown"):
                print(f"    💰 Budget Breakdown: {it['budget_breakdown']}")
            if it.get("est_cost"):
                print(f"    💵 Est Cost: ₹{it['est_cost']:,.0f}")
            if it.get("why"):
                print(f"    💡 Why: {it['why'][0] if it['why'] else ''}")

if __name__ == "__main__":
    asyncio.run(main())

