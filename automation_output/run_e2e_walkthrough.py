import asyncio
import json
import os
import shutil
import time
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
    if os.path.exists(RAW_VIDEO_DIR):
        shutil.rmtree(RAW_VIDEO_DIR)
    os.makedirs(RAW_VIDEO_DIR, exist_ok=True)

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
        # SCENE 2: Groom 1-Click Sign-In
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
            "GROOM ONBOARDING",
            "Narayan signs in as the groom to start planning with a fresh slate.",
            wait_sec=3.5,
            narration="Narayan signs in as the groom for the very first time. His dashboard is completely clean, ready to weave their celebration from scratch."
        )

        groom_btn = page.locator("button:has-text('Narayan')")
        await groom_btn.first.click()
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

        chat_link = page.locator("aside a[href='/app/chat']")
        if await chat_link.count() > 0:
            await chat_link.first.click()
            await page.wait_for_timeout(1500)

        chat_input = page.locator("input[placeholder*='Message WeaveWed']").first
        await chat_input.wait_for(state="visible", timeout=10000)
        await chat_input.first.click()
        await type_slow(chat_input, "We're planning our royal wedding in Udaipur for February 2027! We'll have about 250 guests and a budget of 40 lakhs. We love Sufi music and lakeside heritage palaces.")
        await page.keyboard.press("Enter")
        await page.wait_for_timeout(5000)

        # -----------------------------------------------------------------
        # SCENE 4: Groom's Tastes & Live Chip Picker
        # -----------------------------------------------------------------
        await set_hud(
            page, t0,
            "TASTE INTELLIGENCE (QLOO)",
            "WeaveWed captures Narayan's music and cuisine tastes — respecting dislikes.",
            wait_sec=3.5,
            narration="Narayan shares his preferences: loving Arijit Singh and traditional Mughlai dining, while strictly avoiding loud EDM and neon lighting."
        )

        await chat_input.first.click()
        await type_slow(chat_input, "I love Arijit Singh and royal Mughlai food, but please no loud EDM or neon lights.")
        await page.keyboard.press("Enter")
        await page.wait_for_timeout(5000)

        # Click any interactive chip if rendered
        chips = page.locator("button.chip")
        if await chips.count() > 0:
            await chips.first.click()
            await page.wait_for_timeout(1200)

        # -----------------------------------------------------------------
        # SCENE 5: Narayan Anchors Cultural Roots in Me
        # -----------------------------------------------------------------
        me_link = page.locator("aside a[href='/app/me']")
        await me_link.first.click()
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
        reg_input = page.locator("input[placeholder*='Home state or city']")
        if await reg_input.count() > 0:
            await reg_input.fill("Pune, Maharashtra")
            save_reg = page.locator("button:has-text('Save Region')")
            if await save_reg.count() > 0:
                await save_reg.first.click()
                await page.wait_for_timeout(1000)

        # -----------------------------------------------------------------
        # SCENE 6: Generate Partner Invite Link
        # -----------------------------------------------------------------
        await set_hud(
            page, t0,
            "PARTNER INVITATION",
            "A wedding is woven for two — Narayan creates a private invite for his fiancée Amruta.",
            wait_sec=3.5,
            narration="A wedding is woven for two. Narayan creates a private invite link for his fiancée Amruta and copies it to share."
        )

        invite_btn = page.locator("button:has-text('Create invite link')")
        if await invite_btn.count() > 0:
            await invite_btn.first.click()
            await page.wait_for_timeout(2000)

        copy_btn = page.locator("button:has-text('Copy link')")
        if await copy_btn.count() == 0:
            copy_btn = page.locator("button svg.lucide-copy").locator("..")

        invite_url = ""
        break_all = page.locator("span.break-all")
        if await break_all.count() > 0:
            invite_url = (await break_all.first.inner_text()).strip()
        print("Captured invite URL:", invite_url, flush=True)

        if await copy_btn.count() > 0:
            await copy_btn.first.click()
            await page.wait_for_timeout(1200)

        # -----------------------------------------------------------------
        # SCENE 7: Perspective Switch — Amruta Joins
        # -----------------------------------------------------------------
        await set_hud(
            page, t0,
            "PERSPECTIVE SWITCH",
            "📱 Switching to Amruta's device — opening Narayan's wedding invite.",
            wait_sec=3.5,
            narration="Switching to Amruta's perspective. She opens the invite link and signs in with her own account."
        )

        # Clear Narayan's token to simulate bride on her own device
        await page.evaluate("localStorage.clear()")
        if invite_url and "join/" in invite_url:
            await page.goto(invite_url, wait_until="networkidle")
        else:
            await page.goto(f"{BASE_URL}/login")

        await page.wait_for_timeout(1500)
        sign_in_join = page.locator("a:has-text('Sign in to join')")
        if await sign_in_join.count() > 0:
            await sign_in_join.first.click()
            await page.wait_for_url("**/login**", timeout=10000)

        bride_btn = page.locator("button:has-text('Amruta')")
        await bride_btn.first.click()
        await page.wait_for_url("**/app**", timeout=12000)
        await page.wait_for_timeout(2000)

        # -----------------------------------------------------------------
        # SCENE 8: Amruta Adds Her Aesthetic in Chat
        # -----------------------------------------------------------------
        await set_hud(
            page, t0,
            "BRIDE'S AESTHETIC",
            "Amruta chats with WeaveWed: indie acoustic music, pastel florals, vegan dining.",
            wait_sec=3.5,
            narration="Amruta chats with WeaveWed AI, sharing her love for Prateek Kuhad, soft pastel floral decor, Sabyasachi lehengas, and vegan catering options."
        )

        chat_link = page.locator("aside a[href='/app/chat']")
        if await chat_link.count() > 0:
            await chat_link.first.click()
            await page.wait_for_timeout(1500)

        chat_input = page.locator("input[placeholder*='Message WeaveWed']").first
        await chat_input.first.click()
        await type_slow(chat_input, "Hi WeaveWed! I'm Amruta. I adore indie acoustic music like Prateek Kuhad, soft pastel decor, Sabyasachi lehengas, and vegan options for our friends.")
        await page.keyboard.press("Enter")
        await page.wait_for_timeout(5000)

        # -----------------------------------------------------------------
        # SCENE 9: Amruta Anchors Her Cultural Roots in Me
        # -----------------------------------------------------------------
        me_link = page.locator("aside a[href='/app/me']")
        await me_link.first.click()
        await page.wait_for_timeout(1500)

        await set_hud(
            page, t0,
            "BRIDE'S CULTURAL HERITAGE",
            "Amruta adds her cultural roots: Bengali Heritage & Kolkata traditions.",
            wait_sec=3.5,
            narration="In her profile, Amruta adds her cultural roots: Bengali heritage and traditions from Kolkata."
        )

        b_chip = page.locator("button:has-text('Bengali')")
        if await b_chip.count() > 0:
            await b_chip.first.click()
            await page.wait_for_timeout(800)

        h_chip = page.locator("button:has-text('Hindu')")
        if await h_chip.count() > 0:
            await h_chip.first.click()
            await page.wait_for_timeout(800)

        reg_input = page.locator("input[placeholder*='Home state or city']")
        if await reg_input.count() > 0:
            await reg_input.fill("Kolkata, West Bengal")
            save_reg = page.locator("button:has-text('Save Region')")
            if await save_reg.count() > 0:
                await save_reg.first.click()
                await page.wait_for_timeout(1000)

        # -----------------------------------------------------------------
        # SCENE 10: Couple Taste DNA Revelation (Cultural Harmony)
        # -----------------------------------------------------------------
        dna_link = page.locator("aside a[href='/app/dna']")
        await dna_link.first.click()
        await page.wait_for_timeout(2000)

        await set_hud(
            page, t0,
            "COUPLE TASTE DNA · CULTURAL HARMONY",
            "QLOO synthesizes both worlds: Bridging Maharashtrian & Bengali Traditions.",
            wait_sec=5.0,
            narration="Opening Couple DNA reveals the power of QLOO taste intelligence: synthesizing their compatibility score, shared loves, and weaving Maharashtrian and Bengali heritages into harmonious ceremony, cuisine, and music fusions."
        )

        await page.evaluate("window.scrollBy({top: 400, behavior: 'smooth'})")
        await page.wait_for_timeout(2000)
        await page.evaluate("window.scrollBy({top: 400, behavior: 'smooth'})")
        await page.wait_for_timeout(2000)
        await page.evaluate("window.scrollTo({top: 0, behavior: 'smooth'})")
        await page.wait_for_timeout(1000)

        # -----------------------------------------------------------------
        # SCENE 11: Event Space Hub — All 5 Tabs
        # -----------------------------------------------------------------
        spaces_link = page.locator("aside a[href='/app/spaces']")
        await spaces_link.first.click()
        await page.wait_for_timeout(1500)

        # Click Wedding space card
        wedding_card = page.locator("a[href^='/app/spaces/']").first
        if await wedding_card.count() > 0:
            await wedding_card.first.click()
            await page.wait_for_timeout(2000)

        # Tab 1: Plan
        await set_hud(
            page, t0,
            "TAB 1: PLAN (QLOO MASTERPLAN)",
            "Weaving the 3-day royal masterplan from synthesized couple tastes.",
            wait_sec=4.5,
            narration="Under the Plan tab, WeaveWed weaves a complete multi-day itinerary: Lake Pichola venues, ceremony rituals, fusion Sangeet playlists, and royal dining."
        )

        build_btn = page.locator("button:has-text('Build our plan')")
        if await build_btn.count() > 0:
            await build_btn.first.click()
            await page.wait_for_timeout(6000)

        # Scroll through plan recommendations
        await page.evaluate("window.scrollBy({top: 500, behavior: 'smooth'})")
        await page.wait_for_timeout(1500)

        # Expand 'Why this?' if visible
        why_btn = page.locator("button:has-text('Why this?')").first
        if await why_btn.count() > 0:
            await why_btn.first.click()
            await page.wait_for_timeout(1500)

        # Click Love it chip
        love_btn = page.locator("button[aria-label='Love it']").first
        if await love_btn.count() > 0:
            await love_btn.first.click()
            await page.wait_for_timeout(1000)

        # Test prompt adjustment
        plan_input = page.locator("input[placeholder*='no loud DJs']")
        if await plan_input.count() > 0:
            await plan_input.fill("more Sufi & acoustic, no loud DJs")
            update_btn = page.locator("button:has-text('Update plan')")
            if await update_btn.count() > 0:
                await update_btn.first.click()
                await page.wait_for_timeout(2000)

        # Tab 2: Details
        details_tab = page.locator("button:text-is('Details')")
        if await details_tab.count() > 0:
            await details_tab.first.click()
            await set_hud(
                page, t0,
                "TAB 2: DETAILS",
                "Event parameters: Udaipur, February 2027, 250 guests, ₹40L budget.",
                wait_sec=3.5,
                narration="The Details tab manages live parameters: wedding dates, Udaipur venue location, guest count of 250, and their 40-lakh budget."
            )
            save_det = page.locator("button:has-text('Save details')")
            if await save_det.count() > 0:
                await save_det.first.click()
                await page.wait_for_timeout(1000)

        # Tab 3: Budget
        budget_tab = page.locator("button:text-is('Budget')")
        if await budget_tab.count() > 0:
            await budget_tab.first.click()
            await set_hud(
                page, t0,
                "TAB 3: BUDGET",
                "Smart Budget Split: ₹40 Lakhs dynamically distributed across key categories.",
                wait_sec=3.5,
                narration="The Budget tab visualizes a smart breakdown: allocating funds across venues, royal catering, decor, and photography."
            )
            adj_btn = page.locator("button:has-text('Adjust split')")
            if await adj_btn.count() > 0:
                await adj_btn.first.click()
                await page.wait_for_timeout(1200)

        # Tab 4: To-dos
        todos_tab = page.locator("button:text-is('To-dos')")
        if await todos_tab.count() > 0:
            await todos_tab.first.click()
            await set_hud(
                page, t0,
                "TAB 4: TO-DOS",
                "Milestone Checklist: automated milestone tracking from venue booking to pheras.",
                wait_sec=3.5,
                narration="The To-dos tab tracks key milestones. Tasks can be checked off or added seamlessly."
            )
            checkboxes = page.locator("input[type='checkbox']")
            if await checkboxes.count() > 0:
                await checkboxes.first.click()
                await page.wait_for_timeout(800)

            todo_input = page.locator("input[placeholder*='Add a to-do']")
            if await todo_input.count() > 0:
                await todo_input.fill("Book Sangeet choreographer")
                add_todo = page.locator("button:has-text('Add')")
                if await add_todo.count() > 0:
                    await add_todo.first.click()
                    await page.wait_for_timeout(1000)

        # Tab 5: Memories
        mem_tab = page.locator("button:text-is('Memories')")
        if await mem_tab.count() > 0:
            await mem_tab.first.click()
            await set_hud(
                page, t0,
                "TAB 5: MEMORIES",
                "Episodic Memory: reflections and ratings that teach WeaveWed for future plans.",
                wait_sec=3.5,
                narration="Under Memories, couples log ratings and reflections that feed the agent's long-term memory for anniversaries and future trips."
            )
            star5 = page.locator("button[aria-label='5 stars']")
            if await star5.count() > 0:
                await star5.first.click()
                await page.wait_for_timeout(600)

            mem_textarea = page.locator("textarea[placeholder*='What did you love']")
            if await mem_textarea.count() > 0:
                await mem_textarea.fill("Loved our venue tasting session in Udaipur! The lakeside sunset view was breathtaking.")
                save_mem = page.locator("button:has-text('Save memory')")
                if await save_mem.count() > 0:
                    await save_mem.first.click()
                    await page.wait_for_timeout(1200)

        # -----------------------------------------------------------------
        # SCENE 12: Secret Surprises (Privacy Guarantee)
        # -----------------------------------------------------------------
        await set_hud(
            page, t0,
            "SECRET SURPRISES",
            "Narayan plans a secret lakeside surprise — guaranteed 100% invisible to Amruta.",
            wait_sec=4.0,
            narration="Narayan secretly plans a sunset violin boat ride on Lake Pichola. WeaveWed guarantees zero leaks on Amruta's account."
        )

        surprises_link = page.locator("aside a[href='/app/surprises']")
        await surprises_link.first.click()
        await page.wait_for_timeout(2000)

        # -----------------------------------------------------------------
        # SCENE 13: Gemini Live Voice UI Feature Showcase
        # -----------------------------------------------------------------
        await set_hud(
            page, t0,
            "GEMINI LIVE VOICE UI",
            "Hands-free planning on the go with Gemini 2.5 Live multi-modal voice.",
            wait_sec=4.0,
            narration="For hands-free planning on the go, couples can converse naturally with Gemini 2.5 Live voice."
        )

        voice_btn = page.locator("button:has-text('Talk to WeaveWed')")
        if await voice_btn.count() == 0:
            voice_btn = page.locator("button:has-text('Talk')")

        if await voice_btn.count() > 0:
            await voice_btn.first.click()
            await page.wait_for_timeout(4500)
            close_voice = page.locator("button[aria-label='Close voice']")
            if await close_voice.count() == 0:
                close_voice = page.locator("div.fixed button svg.lucide-x").locator("..")
            if await close_voice.count() > 0:
                await close_voice.first.click()
                await page.wait_for_timeout(1000)

        # -----------------------------------------------------------------
        # SCENE 14: Grand Finale
        # -----------------------------------------------------------------
        home_link = page.locator("aside a[href='/app']")
        await home_link.first.click()
        await page.wait_for_timeout(1500)

        await set_hud(
            page, t0,
            "WEAVEWED · HAPPILY EVER AFTER",
            "Two distinct worlds, woven into one unforgettable celebration.",
            wait_sec=4.5,
            narration="Two distinct worlds, woven into one unforgettable celebration. WeaveWed — not just events, a lifetime of beautiful memories."
        )
        await page.wait_for_timeout(2000)

        # Close page & browser to flush video
        print("Closing page and saving video...", flush=True)
        await page.close()
        await context.close()
        await browser.close()

    # -----------------------------------------------------------------
    # Process Outputs: Video, SRT, JSON, Markdown
    # -----------------------------------------------------------------
    video_files = [f for f in os.listdir(RAW_VIDEO_DIR) if f.endswith(".webm")]
    if video_files:
        src_video = os.path.join(RAW_VIDEO_DIR, video_files[0])
        final_video = os.path.join(OUT_DIR, "weavewed_walkthrough.webm")
        shutil.copy2(src_video, final_video)
        print(f"Final video generated: {final_video}", flush=True)

    # Generate SRT Subtitle file
    srt_path = os.path.join(OUT_DIR, "subtitles.srt")
    with open(srt_path, "w", encoding="utf-8") as f:
        for t in timeline:
            f.write(f"{t['index']}\n")
            f.write(f"{format_srt_time(t['start'])} --> {format_srt_time(t['end'])}\n")
            f.write(f"[{t['tag']}] {t['caption']}\n\n")
    print(f"Subtitles generated: {srt_path}", flush=True)

    # Generate JSON Narration Timeline
    json_path = os.path.join(OUT_DIR, "narration_script.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(timeline, f, indent=2)
    print(f"JSON Narration generated: {json_path}", flush=True)

    # Generate VOICEOVER_SCRIPT.md
    md_path = os.path.join(OUT_DIR, "VOICEOVER_SCRIPT.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# WeaveWed End-to-End Walkthrough — Voiceover & Narration Script\n\n")
        f.write("> **Total Scenes**: " + str(len(timeline)) + "\n")
        f.write("> **Resolution**: 1920x1080 Full HD\n")
        f.write("> **Video File**: `automation_output/weavewed_walkthrough.webm`\n\n---\n\n")
        for t in timeline:
            f.write(f"### Scene {t['index']}: {t['tag']}\n")
            f.write(f"- **Timestamp**: `{format_srt_time(t['start'])}` to `{format_srt_time(t['end'])}` (Duration: {round(t['end'] - t['start'], 1)}s)\n")
            f.write(f"- **On-Screen Caption HUD**: *\"{t['caption']}\"*\n")
            f.write(f"- **Voiceover Audio Script**:\n")
            f.write(f"  > \"{t['narration']}\"\n\n")
    print(f"Markdown Voiceover script generated: {md_path}", flush=True)

    print("=== AUTOMATION RUN COMPLETED SUCCESSFULLY! ===", flush=True)

if __name__ == "__main__":
    asyncio.run(run_automation())
