import asyncio
import json
import os
import shutil
import sys
import time

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
from playwright.async_api import async_playwright

BASE_URL = "https://weavewed-v2-sem5hyzlrq-uc.a.run.app"
OUT_DIR = "automation_output"
RAW_VIDEO_DIR = os.path.join(OUT_DIR, "raw_video")

timeline = []

def format_srt_time(seconds: float) -> str:
    millis = int((seconds - int(seconds)) * 1000)
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hrs:02d}:{mins:02d}:{secs:02d},{millis:03d}"

async def inject_hud(page):
    js = """
    (() => {
      if (document.getElementById('ww-hud-caption')) return;
      const hud = document.createElement('div');
      hud.id = 'ww-hud-caption';
      hud.style.cssText = `
        position: fixed;
        bottom: 24px;
        left: 50%;
        transform: translateX(-50%);
        z-index: 9999999;
        background: rgba(36, 18, 25, 0.94);
        backdrop-filter: blur(14px);
        -webkit-backdrop-filter: blur(14px);
        color: #ffffff;
        padding: 12px 28px;
        border-radius: 9999px;
        border: 1px solid rgba(212, 160, 23, 0.55);
        box-shadow: 0 16px 45px rgba(0, 0, 0, 0.5);
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        text-align: center;
        max-width: 85%;
        pointer-events: none;
        transition: all 0.35s cubic-bezier(0.16, 1, 0.3, 1);
        opacity: 0;
      `;
      const tag = document.createElement('div');
      tag.id = 'ww-hud-tag';
      tag.style.cssText = `
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.14em;
        color: #eab308;
        font-weight: 700;
        margin-bottom: 3px;
      `;
      const title = document.createElement('div');
      title.id = 'ww-hud-title';
      title.style.cssText = `
        font-size: 16px;
        font-weight: 600;
        letter-spacing: 0.01em;
        line-height: 1.35;
        color: #fdfaf6;
      `;
      hud.appendChild(tag);
      hud.appendChild(title);
      document.body.appendChild(hud);
    })()
    """
    await page.evaluate(js)

async def set_hud(page, t0, tag, text, wait_sec=3.5, narration=""):
    await inject_hud(page)
    start_sec = time.perf_counter() - t0
    js_update = f"""
    (() => {{
      const hud = document.getElementById('ww-hud-caption');
      const tagEl = document.getElementById('ww-hud-tag');
      const titleEl = document.getElementById('ww-hud-title');
      if (hud && tagEl && titleEl) {{
        tagEl.innerText = {json.dumps(tag)};
        titleEl.innerText = {json.dumps(text)};
        hud.style.opacity = '1';
        hud.style.transform = 'translateX(-50%) translateY(0)';
      }}
    }})()
    """
    await page.evaluate(js_update)
    print(f"[{format_srt_time(start_sec)}] HUD: [{tag}] {text}", flush=True)
    await page.wait_for_timeout(int(wait_sec * 1000))
    end_sec = time.perf_counter() - t0
    timeline.append({
        "index": len(timeline) + 1,
        "start": start_sec,
        "end": end_sec,
        "tag": tag,
        "caption": text,
        "narration": narration or text
    })

async def type_slow(locator, text, delay_ms=25):
    await locator.press_sequentially(text, delay=delay_ms)

async def run_automation():
    # 1. Clean previous video files
    if os.path.exists(RAW_VIDEO_DIR):
        shutil.rmtree(RAW_VIDEO_DIR)
    os.makedirs(RAW_VIDEO_DIR, exist_ok=True)

    # 2. Complete database wipe first
    print("=== WIPING DATABASE FOR PRISTINE ONBOARDING ===", flush=True)
    sys.path.insert(0, ".")
    sys.path.insert(0, "backend")
    from scripts.wipe_personas import wipe
    await wipe()
    print("=== DATABASE WIPED CLEANLY ===", flush=True)

    print("=== LAUNCHING PLAYWRIGHT FULL HD RECORDING ===", flush=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, channel="chrome")
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            record_video_dir=RAW_VIDEO_DIR,
            record_video_size={"width": 1920, "height": 1080}
        )
        page = await context.new_page()
        page.set_default_timeout(25000)

        t0 = time.perf_counter()

        # -----------------------------------------------------------------
        # SCENE 1: Welcome & Landing Page
        # -----------------------------------------------------------------
        print("Navigating to landing page...", flush=True)
        await page.goto(BASE_URL, wait_until="networkidle")
        await set_hud(
            page, t0,
            "WELCOME TO WEAVEWED",
            "Your AI wedding companion powered by QLOO taste intelligence.",
            wait_sec=4.0,
            narration="Welcome to WeaveWed, the AI wedding companion powered by QLOO taste intelligence. Designed to personalize every chapter of love."
        )

        await page.evaluate("window.scrollBy({top: 450, behavior: 'smooth'})")
        await page.wait_for_timeout(1500)
        await page.evaluate("window.scrollTo({top: 0, behavior: 'smooth'})")
        await page.wait_for_timeout(1000)

        # -----------------------------------------------------------------
        # SCENE 2: Groom Authentic Account Creation
        # -----------------------------------------------------------------
        start_btn = page.locator("button:has-text('Start planning with AI')")
        if await start_btn.count() > 0:
            await start_btn.first.click()
        else:
            await page.goto(f"{BASE_URL}/login")
        await page.wait_for_url("**/login**", timeout=10000)
        await page.wait_for_timeout(1000)

        await set_hud(
            page, t0,
            "AUTHENTIC ONBOARDING",
            "Narayan creates an account as the groom to start wedding planning.",
            wait_sec=3.5,
            narration="Narayan creates his account as the groom with a clean slate. No shortcuts, an authentic onboarding flow."
        )

        # Toggle to "Create an account"
        create_toggle = page.locator("button:has-text('Create an account')").first
        if await create_toggle.count() > 0:
            await create_toggle.click()
            await page.wait_for_timeout(800)

        name_input = page.locator("input[placeholder*='first name']").first
        if await name_input.count() > 0:
            await type_slow(name_input, "Narayan", delay_ms=30)

        email_input = page.locator("input[type='email']").first
        await type_slow(email_input, "narayan@weavewed.ai", delay_ms=25)

        pw_input = page.locator("input[type='password']").first
        await type_slow(pw_input, "password123", delay_ms=25)

        submit_btn = page.locator("button.btn-primary:has-text('Create account'), button.btn-primary:has-text('Sign in')").first
        await submit_btn.click()
        await page.wait_for_url("**/app**", timeout=12000)
        await page.wait_for_timeout(2000)

        # -----------------------------------------------------------------
        # SCENE 3: Conversational Planning with WeaveWed AI
        # -----------------------------------------------------------------
        await set_hud(
            page, t0,
            "WEAVEWED AI CHAT",
            "Narayan tells WeaveWed AI about their dream royal wedding in Udaipur.",
            wait_sec=3.5,
            narration="Narayan tells WeaveWed AI about their vision: a 3-day royal wedding in Udaipur for 250 guests with a 40-lakh budget, lakeside palaces, and soulful Sufi music."
        )

        chat_link = page.locator("aside a[href='/app/chat']").first
        if await chat_link.count() > 0:
            await chat_link.click()
            await page.wait_for_timeout(1500)

        chat_input = page.locator("input[placeholder*='Message WeaveWed']").first
        await chat_input.wait_for(state="visible", timeout=10000)
        await chat_input.click()
        await type_slow(chat_input, "We're planning our royal wedding in Udaipur for February 2027! We'll have about 250 guests and a budget of 40 lakhs. We love Sufi music and lakeside heritage palaces.")
        await page.keyboard.press("Enter")
        await page.wait_for_timeout(7000)

        # -----------------------------------------------------------------
        # SCENE 4: Groom's Partner, Ceremonies & Tastes
        # -----------------------------------------------------------------
        await set_hud(
            page, t0,
            "CEREMONIES & TASTE CAPTURE",
            "Narayan introduces bride Amruta and specifies ceremonies & music tastes.",
            wait_sec=3.5,
            narration="Narayan introduces his bride Amruta, confirms all five ceremonies, and specifies his love for Arijit Singh and royal Mughlai dining."
        )

        await chat_input.click()
        await type_slow(chat_input, "My partner's name is Amruta! For our wedding, the date is 2027-02-01, and we want Haldi, Mehendi, Sangeet, Wedding, and Reception. I love Arijit Singh, traditional Mughlai food, and royal sherwanis. But please no loud EDM or neon lights.")
        await page.keyboard.press("Enter")
        await page.wait_for_timeout(8000)

        # Click any interactive chip if rendered
        chips = page.locator("button.chip")
        if await chips.count() > 0:
            await chips.first.click()
            await page.wait_for_timeout(1200)

        # -----------------------------------------------------------------
        # SCENE 5: Narayan Anchors Cultural Roots in Me
        # -----------------------------------------------------------------
        me_link = page.locator("aside a[href='/app/me']").first
        await me_link.click()
        await page.wait_for_timeout(1500)

        await set_hud(
            page, t0,
            "CULTURAL ROOTS & HERITAGE",
            "Narayan anchors his roots: Maharashtrian Heritage & Hindu Vedic Traditions.",
            wait_sec=4.0,
            narration="In his profile, Narayan selects his cultural roots: Maharashtrian heritage and Hindu wedding traditions from Pune, Maharashtra."
        )

        # Select Maharashtrian chip
        m_chip = page.locator("button:has-text('Maharashtrian')")
        if await m_chip.count() > 0:
            await m_chip.first.click()
            await page.wait_for_timeout(800)

        # Select Hindu tradition chip
        h_chip = page.locator("button:has-text('Hindu')")
        if await h_chip.count() > 0:
            await h_chip.first.click()
            await page.wait_for_timeout(800)

        # Region input
        reg_input = page.locator("input[placeholder*='Home state or city']").first
        if await reg_input.count() > 0:
            await reg_input.fill("Pune, Maharashtra")
            save_reg = page.locator("button:has-text('Save Region')").first
            if await save_reg.count() > 0:
                await save_reg.click()
                await page.wait_for_timeout(1000)

        # -----------------------------------------------------------------
        # SCENE 6: Generate Partner Invite Link
        # -----------------------------------------------------------------
        await set_hud(
            page, t0,
            "PARTNER COLLABORATION",
            "Generating a unique invite link so bride Amruta's tastes are woven together.",
            wait_sec=3.5,
            narration="WeaveWed is built for couples. Narayan creates a partner invite link so Amruta can join with her own account and tastes."
        )

        invite_btn = page.locator("button:has-text('Create invite link')").first
        if await invite_btn.count() > 0:
            await invite_btn.click()
            await page.wait_for_timeout(1500)

        # Retrieve the invite code from the UI
        invite_code = ""
        invite_span = page.locator("span:has-text('/join/')").first
        try:
            await invite_span.wait_for(state="visible", timeout=6000)
            val = await invite_span.inner_text()
            if "/join/" in val:
                invite_code = val.split("/join/")[-1].strip()
            else:
                invite_code = val.strip()
        except Exception as e:
            print(f"Waiting for invite span fallback: {e}", flush=True)

        print(f"Partner invite code created: {invite_code}", flush=True)

        # Sign out Narayan cleanly
        signout_btn = page.locator("button:has-text('Sign out')").first
        if await signout_btn.count() > 0:
            await signout_btn.click()
            await page.wait_for_timeout(1200)

        # -----------------------------------------------------------------
        # SCENE 7: Bride Amruta Accepts Invite & Onboards
        # -----------------------------------------------------------------
        join_url = f"{BASE_URL}/join/{invite_code}" if invite_code else f"{BASE_URL}/login"
        print(f"Navigating Amruta to join URL: {join_url}", flush=True)
        await page.goto(join_url, wait_until="networkidle")
        await page.wait_for_timeout(1500)

        await set_hud(
            page, t0,
            "BRIDE ONBOARDING",
            "Amruta accepts the wedding invitation to co-plan the celebration.",
            wait_sec=3.5,
            narration="Amruta opens the invitation link. She signs in to join Narayan's wedding space and contribute her unique aesthetic."
        )

        # Click "Sign in to join" on the Join page
        join_btn = page.locator("a:has-text('Sign in to join')").first
        if await join_btn.count() > 0:
            await join_btn.click()
            await page.wait_for_url("**/login**", timeout=8000)
            await page.wait_for_timeout(800)

        # On login page, switch to "Create an account"
        create_toggle_a = page.locator("button:has-text('Create an account')").first
        if await create_toggle_a.count() > 0:
            await create_toggle_a.click()
            await page.wait_for_timeout(800)

        name_input_a = page.locator("input[placeholder*='first name']").first
        if await name_input_a.count() > 0:
            await type_slow(name_input_a, "Amruta", delay_ms=30)

        email_input_a = page.locator("input[type='email']").first
        await type_slow(email_input_a, "amruta@weavewed.ai", delay_ms=25)

        pw_input_a = page.locator("input[type='password']").first
        await type_slow(pw_input_a, "password123", delay_ms=25)

        submit_btn_a = page.locator("button.btn-primary:has-text('Create account'), button.btn-primary:has-text('Sign in')").first
        await submit_btn_a.click()
        await page.wait_for_url("**/app**", timeout=12000)
        await page.wait_for_timeout(2000)

        # -----------------------------------------------------------------
        # SCENE 8: Bride Chats Aesthetic with WeaveWed AI
        # -----------------------------------------------------------------
        await set_hud(
            page, t0,
            "BRIDE'S TASTES (QLOO)",
            "Amruta shares her aesthetic: Indie acoustic, pastel florals & Sabyasachi.",
            wait_sec=3.5,
            narration="Amruta shares her aesthetic: indie acoustic music like Prateek Kuhad, soft pastel floral decor, Sabyasachi bridal wear, and vegan catering."
        )

        chat_link_a = page.locator("aside a[href='/app/chat']").first
        if await chat_link_a.count() > 0:
            await chat_link_a.click()
            await page.wait_for_timeout(1500)
        else:
            await page.goto(f"{BASE_URL}/app/chat", wait_until="networkidle")

        chat_input_a = page.locator("input[placeholder*='Message WeaveWed']").first
        await chat_input_a.wait_for(state="visible", timeout=10000)
        await chat_input_a.click()
        await type_slow(chat_input_a, "Hi WeaveWed! I'm Amruta. I love indie acoustic vibes like Prateek Kuhad, soft pastel floral decor, Sabyasachi lehengas, and vegan catering options for our friends.")
        await page.keyboard.press("Enter")
        await page.wait_for_timeout(7000)

        # -----------------------------------------------------------------
        # SCENE 9: Bride Sets Bengali Cultural Roots
        # -----------------------------------------------------------------
        me_link_a = page.locator("aside a[href='/app/me']").first
        await me_link_a.click()
        await page.wait_for_timeout(1500)

        await set_hud(
            page, t0,
            "BRIDE'S CULTURAL HERITAGE",
            "Amruta anchors her roots: Bengali Heritage from Kolkata, West Bengal.",
            wait_sec=3.5,
            narration="Amruta selects her cultural roots: Bengali heritage and Kolkata traditions. Now both partners' cultural backgrounds are fully known."
        )

        b_chip = page.locator("button:has-text('Bengali')").first
        if await b_chip.count() > 0:
            await b_chip.click()
            await page.wait_for_timeout(800)

        h_chip_a = page.locator("button:has-text('Hindu')").first
        if await h_chip_a.count() > 0:
            await h_chip_a.click()
            await page.wait_for_timeout(800)

        reg_input_a = page.locator("input[placeholder*='Home state or city']").first
        if await reg_input_a.count() > 0:
            await reg_input_a.fill("Kolkata, West Bengal")
            save_reg_a = page.locator("button:has-text('Save Region')").first
            if await save_reg_a.count() > 0:
                await save_reg_a.click()
                await page.wait_for_timeout(1000)

        # -----------------------------------------------------------------
        # SCENE 10: Couple Taste DNA & Cultural Harmony
        # -----------------------------------------------------------------
        dna_link = page.locator("aside a[href='/app/dna']").first
        await dna_link.click()
        await page.wait_for_timeout(2000)

        await set_hud(
            page, t0,
            "COUPLE TASTE DNA & CULTURAL HARMONY",
            "QLOO synthesizes their shared vibe & cross-cultural Maharashtrian-Bengali fusion.",
            wait_sec=4.5,
            narration="Under Couple Taste DNA, QLOO synthesizes where their two worlds meet: discovering shared passions, unique individual flavours, and tailored Maharashtrian-Bengali cultural harmony ideas."
        )

        await page.evaluate("window.scrollBy({top: 450, behavior: 'smooth'})")
        await page.wait_for_timeout(2500)
        await page.evaluate("window.scrollTo({top: 0, behavior: 'smooth'})")
        await page.wait_for_timeout(1000)

        # -----------------------------------------------------------------
        # SCENE 11: Masterplan & Event Spaces
        # -----------------------------------------------------------------
        spaces_link = page.locator("aside a[href='/app/spaces']").first
        await spaces_link.click()
        await page.wait_for_timeout(2000)

        await set_hud(
            page, t0,
            "EVENT SPACES & MASTERPLAN",
            "Exploring the complete wedding space across all 5 integrated tabs.",
            wait_sec=4.0,
            narration="In Event Spaces, Narayan and Amruta have a comprehensive command center for their Udaipur wedding across Plan, Details, Budget, To-dos, and Memories."
        )

        # Click into the active Wedding space
        wedding_card = page.locator(".card:has-text('Wedding'), .card:has-text('Udaipur')").first
        if await wedding_card.count() > 0:
            await wedding_card.click()
            await page.wait_for_timeout(2000)

        # Tab 1: Plan
        await set_hud(
            page, t0,
            "THE AI MASTERPLAN",
            "AI-curated venues, ceremonies, signature menu & designers with 'Why this?' insights.",
            wait_sec=4.0,
            narration="Every section is woven with QLOO intelligence and transparent reasoning — from Taj Lake Palace to a curated Mughlai and Vegan Bengali fusion banquet."
        )
        await page.evaluate("window.scrollBy({top: 550, behavior: 'smooth'})")
        await page.wait_for_timeout(2500)

        # Like a venue card
        like_btn = page.locator("button:has-text('Like'), button[title*='Like']").first
        if await like_btn.count() > 0:
            await like_btn.click()
            await page.wait_for_timeout(1200)

        # Tab 2: Details
        details_tab = page.locator("button:has-text('Details'), a:has-text('Details')").first
        if await details_tab.count() > 0:
            await details_tab.click()
            await set_hud(
                page, t0,
                "EVENT DETAILS",
                "Full event parameters: 250 guests, Rs. 40L budget, and confirmed ceremonies.",
                wait_sec=3.5,
                narration="The Details tab maintains live event parameters — Udaipur, 250 guests, 40 lakhs budget, and confirmed Haldi, Mehendi, Sangeet, and Reception."
            )
            await page.wait_for_timeout(2000)

        # Tab 3: Budget
        budget_tab = page.locator("button:has-text('Budget'), a:has-text('Budget')").first
        if await budget_tab.count() > 0:
            await budget_tab.click()
            await set_hud(
                page, t0,
                "SMART BUDGET ALLOCATION",
                "Automated Rs. 40,00,000 allocation across Venues, Catering, Decor & Outfits.",
                wait_sec=3.5,
                narration="The Budget tab dynamically allocates the 40 lakh budget across venue, catering, decor, and fashion according to couple priorities."
            )
            await page.wait_for_timeout(2000)

        # Tab 4: To-dos
        todos_tab = page.locator("button:has-text('To-dos'), a:has-text('To-dos')").first
        if await todos_tab.count() > 0:
            await todos_tab.click()
            await set_hud(
                page, t0,
                "COUNTDOWN TIMELINE & TO-DOS",
                "Intelligent milestone tracking leading up to the February 2027 celebration.",
                wait_sec=3.5,
                narration="To-dos keep both partners perfectly in sync with timed countdown milestones and collaborative task ownership."
            )
            await page.wait_for_timeout(2000)

        # Tab 5: Memories
        memories_tab = page.locator("button:has-text('Memories'), a:has-text('Memories')").first
        if await memories_tab.count() > 0:
            await memories_tab.click()
            await set_hud(
                page, t0,
                "TIME CAPSULE & MEMORIES",
                "Capturing photos, voice notes, and milestone moments beyond the wedding day.",
                wait_sec=3.5,
                narration="Memories turns the wedding journey into a lasting heirloom of audio notes, photos, and cherished reflections."
            )
            await page.wait_for_timeout(2000)

        # -----------------------------------------------------------------
        # SCENE 12: Final Celebration HUD
        # -----------------------------------------------------------------
        await page.goto(f"{BASE_URL}/app", wait_until="networkidle")
        await page.wait_for_timeout(1000)

        await set_hud(
            page, t0,
            "WEAVEWED — HAPPILY EVER AFTER",
            "Taste intelligence meets lifelong celebration. Woven together with QLOO & Gemini.",
            wait_sec=4.5,
            narration="WeaveWed: where taste intelligence meets lifelong love. Two worlds woven into one unforgettable celebration."
        )

        await page.wait_for_timeout(2000)
        await context.close()
        await browser.close()

    # Write timeline artifacts
    with open(os.path.join(OUT_DIR, "narration_script.json"), "w", encoding="utf-8") as f:
        json.dump(timeline, f, indent=2)

    srt_lines = []
    for item in timeline:
        srt_lines.append(f"{item['index']}")
        srt_lines.append(f"{format_srt_time(item['start'])} --> {format_srt_time(item['end'])}")
        srt_lines.append(f"[{item['tag']}] {item['caption']}\n")
    with open(os.path.join(OUT_DIR, "subtitles.srt"), "w", encoding="utf-8") as f:
        f.write("\n".join(srt_lines))

    # Identify recorded video
    raw_files = [os.path.join(RAW_VIDEO_DIR, f) for f in os.listdir(RAW_VIDEO_DIR) if f.endswith(".webm")]
    if raw_files:
        src = raw_files[0]
        dst = os.path.join(OUT_DIR, "weavewed_walkthrough.webm")
        if os.path.exists(dst):
            os.remove(dst)
        shutil.copy(src, dst)
        print(f"Recorded Full HD video saved to: {dst}", flush=True)

    print("=== UI AUTOMATION WALKTHROUGH RECORDING COMPLETE ===", flush=True)

if __name__ == "__main__":
    asyncio.run(run_automation())
