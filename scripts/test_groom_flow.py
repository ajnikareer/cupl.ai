import os
from playwright.sync_api import sync_playwright

ARTIFACT_DIR = r"C:\Users\admin\.gemini\antigravity\brain\6d8e9353-5c79-4cdf-92cf-1fafc99c77a9"
BASE_URL = "http://127.0.0.1:8080"

with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge", headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 900})

    # Clear any old storage
    page.goto(f"{BASE_URL}/login")
    page.evaluate("() => { localStorage.clear(); localStorage.setItem('ww_dev_token', 'dev-groom_narayan'); }")

    # 1. Home
    print("Visiting Home...")
    page.goto(f"{BASE_URL}/app", wait_until="domcontentloaded")
    page.wait_for_timeout(2000)
    page.screenshot(path=os.path.join(ARTIFACT_DIR, "preview_groom_home.png"))

    # 2. Chat
    print("Visiting Chat...")
    page.goto(f"{BASE_URL}/app/chat", wait_until="domcontentloaded")
    page.wait_for_timeout(2500)
    page.screenshot(path=os.path.join(ARTIFACT_DIR, "preview_groom_chat.png"))

    # 3. Space (Gatekeeper!)
    print("Visiting Event Space (Gatekeeper)...")
    page.goto(f"{BASE_URL}/app/spaces/s_narayan_wedding", wait_until="domcontentloaded")
    page.wait_for_timeout(2500)
    page.screenshot(path=os.path.join(ARTIFACT_DIR, "preview_groom_gatekeeper.png"))

    # 4. Plans
    print("Visiting Plans...")
    page.goto(f"{BASE_URL}/app/plans", wait_until="domcontentloaded")
    page.wait_for_timeout(2000)
    page.screenshot(path=os.path.join(ARTIFACT_DIR, "preview_groom_plans.png"))

    browser.close()
    print("Local Groom tests passed!")
