import asyncio
import json
import os
import sys
import httpx

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

sys.path.insert(0, os.path.abspath("backend"))
sys.path.insert(0, os.path.abspath("."))
from scripts.wipe_personas import wipe

BASE_URL = "https://weavewed-v2-sem5hyzlrq-uc.a.run.app"

async def sse_chat(client: httpx.AsyncClient, token: str, text: str):
    headers = {"Authorization": f"Bearer {token}", "Accept": "text/event-stream"}
    body = {"text": text}
    print(f"\n---> [{token.upper()}] SENDS: {text}")
    print(f"<--- [{token.upper()}] WEAVEWED REPLIES: ", end="", flush=True)

    accumulated_text = ""
    tools_called = []
    widgets_shown = []

    async with client.stream("POST", f"{BASE_URL}/api/chat", json=body, headers=headers, timeout=30.0) as resp:
        if resp.status_code != 200:
            err = await resp.aread()
            print(f"HTTP ERROR {resp.status_code}: {err.decode()}", flush=True)
            return {"error": err.decode()}

        async for line in resp.aiter_lines():
            if not line or not line.startswith("data: "):
                continue
            data_str = line[6:].strip()
            try:
                ev = json.loads(data_str)
                ev_type = ev.get("type")
                if ev_type in ("delta", "token"):
                    t = ev.get("text") or ev.get("token") or ""
                    accumulated_text += t
                    print(t, end="", flush=True)
                elif ev_type == "status":
                    st = ev.get("text", "")
                    print(f" [{st}] ", end="", flush=True)
                elif ev_type == "widget":
                    w = ev.get("widget", {})
                    widgets_shown.append(w)
                    print(f"\n     [WIDGET]: {w.get('kind')} - {w.get('data', {}).get('title', '')}", flush=True)
                elif ev_type == "done":
                    break
            except Exception:
                pass

    print("\n", flush=True)
    if tools_called:
        print(f"     [Tools executed]: {tools_called}", flush=True)
    if widgets_shown:
        print(f"     [Widgets displayed]: {[w.get('kind') for w in widgets_shown]}", flush=True)

    return {
        "text": accumulated_text,
        "tools": tools_called,
        "widgets": widgets_shown
    }

async def run_backend_verification():
    print("=" * 70)
    print("WEAVEWED AGENT & BACKEND COMPREHENSIVE VERIFICATION")
    print(f"Target URL: {BASE_URL}")
    print("=" * 70)

    # 1. Wipe database first
    await wipe()
    print("Database wiped cleanly.\n")

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Check health
        h = await client.get(f"{BASE_URL}/health")
        print(f"Health Status: {h.status_code} {h.json()}\n")

        # -------------------------------------------------------------
        # STEP 1: Narayan initiates chat & creates wedding
        # -------------------------------------------------------------
        print("STEP 1: Narayan creates Udaipur Wedding in Chat...")
        r1 = await sse_chat(
            client, "dev-narayan",
            "We're planning our royal wedding in Udaipur for February 2027! We'll have about 250 guests and a budget of 40 lakhs. We love Sufi music and lakeside heritage palaces."
        )

        # Check Narayan's profile & active space
        me_n = (await client.get(f"{BASE_URL}/api/me", headers={"Authorization": "Bearer dev-narayan"})).json()
        active_space = me_n.get("active_space")
        print(f"Narayan Active Space: {active_space.get('title') if active_space else 'NONE'}")
        if active_space:
            print(f"  City: {active_space.get('city')}, Budget: Rs. {active_space.get('budget'):,.0f}, Guests: {active_space.get('guests')}")
            print(f"  Start Date: {active_space.get('start_date')}, Missing Fields: {active_space.get('missing_fields')}")

        # -------------------------------------------------------------
        # STEP 2: Narayan shares partner name, ceremonies & tastes
        # -------------------------------------------------------------
        print("\nSTEP 2: Narayan shares partner name, ceremonies & tastes...")
        r2 = await sse_chat(
            client, "dev-narayan",
            "My partner's name is Amruta! For our wedding, the date is 2027-02-01, and we want Haldi, Mehendi, Sangeet, Wedding, and Reception. I love Arijit Singh, traditional Mughlai food, and royal sherwanis. But please no loud EDM or neon lights."
        )

        # -------------------------------------------------------------
        # STEP 3: Narayan sets cultural heritage via /api/me
        # -------------------------------------------------------------
        print("\nSTEP 3: Narayan sets Maharashtrian Hindu roots...")
        patch_n = await client.patch(
            f"{BASE_URL}/api/me",
            json={"heritage": "Maharashtrian", "tradition": "Hindu", "state": "Pune, Maharashtra"},
            headers={"Authorization": "Bearer dev-narayan"}
        )
        print("Narayan Cultural Roots Saved:", patch_n.json())

        # -------------------------------------------------------------
        # STEP 4: Generate partner invite
        # -------------------------------------------------------------
        print("\nSTEP 4: Narayan creates partner invite link...")
        inv_resp = await client.post(
            f"{BASE_URL}/api/couple/invite",
            headers={"Authorization": "Bearer dev-narayan"}
        )
        inv = inv_resp.json()
        print(f"Invite Created: Code={inv.get('code')}, Link={inv.get('link')}")
        code = inv.get("code")

        # -------------------------------------------------------------
        # STEP 5: Amruta accepts invite and joins couple
        # -------------------------------------------------------------
        print(f"\nSTEP 5: Amruta joins via invite code '{code}'...")
        join_resp = await client.post(
            f"{BASE_URL}/api/couple/join",
            json={"code": code},
            headers={"Authorization": "Bearer dev-amruta"}
        )
        print("Amruta Join Result:", join_resp.status_code)

        # Verify Amruta's active space
        me_a = (await client.get(f"{BASE_URL}/api/me", headers={"Authorization": "Bearer dev-amruta"})).json()
        a_space = me_a.get("active_space")
        print(f"Amruta Active Space: {a_space.get('title') if a_space else 'NONE'}")
        print(f"Amruta Partner: {me_a.get('partner', {}).get('name')}")
        assert a_space is not None, "Amruta active space should not be None!"
        assert me_a.get("partner", {}).get("name") == "Narayan", "Partner should be Narayan!"

        # -------------------------------------------------------------
        # STEP 6: Amruta chats her aesthetic
        # -------------------------------------------------------------
        print("\nSTEP 6: Amruta chats her aesthetic with WeaveWed AI...")
        r3 = await sse_chat(
            client, "dev-amruta",
            "Hi WeaveWed! I'm Amruta. I love indie acoustic vibes like Prateek Kuhad, soft pastel floral decor, Sabyasachi lehengas, and vegan catering options for our friends."
        )

        # -------------------------------------------------------------
        # STEP 7: Amruta sets cultural heritage via /api/me
        # -------------------------------------------------------------
        print("\nSTEP 7: Amruta sets Bengali Hindu roots...")
        patch_a = await client.patch(
            f"{BASE_URL}/api/me",
            json={"heritage": "Bengali", "tradition": "Hindu", "state": "Kolkata, West Bengal"},
            headers={"Authorization": "Bearer dev-amruta"}
        )
        print("Amruta Cultural Roots Saved:", patch_a.json())

        # -------------------------------------------------------------
        # STEP 8: Couple DNA Synthesis
        # -------------------------------------------------------------
        print("\nSTEP 8: Refreshing and inspecting Couple DNA...")
        dna_resp = await client.post(
            f"{BASE_URL}/api/dna/refresh",
            headers={"Authorization": "Bearer dev-narayan"}
        )
        dna = (await client.get(f"{BASE_URL}/api/dna", headers={"Authorization": "Bearer dev-narayan"})).json().get("dna", {})

        print(f"\nCOUPLE VIBE: {dna.get('vibe')}")
        print(f"DESCRIPTION: {dna.get('description')}")
        ch = dna.get("cultural_harmony")
        if ch:
            print(f"\n🏛️ CULTURAL HARMONY: {ch.get('title')}")
            print(f"   Summary: {ch.get('summary')}")
            for idea in ch.get("ideas", []):
                print(f"   * [{idea.get('category')}]: {idea.get('title')} -> {idea.get('description')[:80]}...")
        else:
            print("   (No cultural harmony block found)")

        # -------------------------------------------------------------
        # STEP 9: Build Masterplan
        # -------------------------------------------------------------
        me_n = (await client.get(f"{BASE_URL}/api/me", headers={"Authorization": "Bearer dev-narayan"})).json()
        active_space = me_n.get("active_space")
        sid = active_space["id"]
        # Ensure all required fields are satisfied
        sp_info = (await client.get(f"{BASE_URL}/api/spaces/{sid}", headers={"Authorization": "Bearer dev-narayan"})).json()
        if sp_info.get("missing_fields"):
            print(f"Completing required space fields: {sp_info.get('missing_fields')}...")
            await client.patch(
                f"{BASE_URL}/api/spaces/{sid}",
                json={"fields": {"start_date": "2027-02-01", "ceremonies": ["Haldi", "Mehendi", "Sangeet", "Wedding", "Reception"]}},
                headers={"Authorization": "Bearer dev-narayan"}
            )

        print(f"\nSTEP 9: Triggering Masterplan generation for space '{sid}'...")
        build_resp = await client.post(
            f"{BASE_URL}/api/spaces/{sid}/plan",
            json={},
            headers={"Authorization": "Bearer dev-narayan"}
        )
        print("Build Plan Initiated:", build_resp.status_code, build_resp.json() if build_resp.status_code == 200 else build_resp.text)

        # Poll until plan is ready (max 60 seconds)
        print("Waiting for plan sections to finish weaving...")
        for attempt in range(12):
            await asyncio.sleep(5)
            p_resp = await client.get(f"{BASE_URL}/api/spaces/{sid}/plan", headers={"Authorization": "Bearer dev-narayan"})
            if p_resp.status_code != 200:
                print(f"  Attempt {attempt+1}: Plan status {p_resp.status_code}")
                continue
            p_data = p_resp.json() or {}
            sections = p_data.get("sections", [])
            print(f"  Attempt {attempt+1}: {len(sections)} sections generated...")
            if len(sections) >= 4 and all(s.get("status") == "done" for s in sections):
                print("\nALL SECTIONS READY!")
                for s in sections:
                    print(f"\n  Section: {s.get('title')} ({len(s.get('items', []))} items)")
                    if s.get("error"):
                        print(f"    ERROR: {s.get('error')}")
                    for item in s.get("items", [])[:2]:
                        print(f"    - {item.get('title')}: {item.get('description')[:70]}...")
                        if item.get("why"):
                            print(f"      Why: {item['why'][0]}")
                break

    print("\n" + "=" * 70)
    print("BACKEND AGENTIC VERIFICATION COMPLETE!")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(run_backend_verification())
