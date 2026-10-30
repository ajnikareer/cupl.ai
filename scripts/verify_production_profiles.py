import os
from playwright.sync_api import sync_playwright

BASE_URL = "http://127.0.0.1:8080"
ARTIFACT_DIR = r"C:\Users\admin\.gemini\antigravity\brain\6d8e9353-5c79-4cdf-92cf-1fafc99c77a9"

def verify_full_profiles():
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        print("1. Visiting login page...")
        page.goto(f"{BASE_URL}/login")
        page.wait_for_selector("text=quick switch profiles")
        page.screenshot(path=os.path.join(ARTIFACT_DIR, "verify_loaded_login.png"))

        print("2. Clicking 'Log in as Groom (Narayan)'...")
        page.click("text=Log in as Groom (Narayan)")
        page.wait_for_url("**/app**", timeout=15000)
        page.wait_for_timeout(2000)
        page.screenshot(path=os.path.join(ARTIFACT_DIR, "verify_narayan_home.png"))

        print("3. Checking Chat & Thread History...")
        page.click("a[href='/app/chat']")
        page.wait_for_url("**/app/chat**", timeout=15000)
        page.wait_for_timeout(3000)
        page.screenshot(path=os.path.join(ARTIFACT_DIR, "verify_narayan_chat_threads.png"))

        print("4. Checking Events List (All 5 Milestone Events)...")
        page.click("a[href='/app/spaces']")
        page.wait_for_url("**/app/spaces**", timeout=15000)
        page.wait_for_timeout(2000)
        page.screenshot(path=os.path.join(ARTIFACT_DIR, "verify_narayan_all_events.png"))

        print("5. Opening Royal Hyderabad Wedding Event Plan...")
        page.locator("a[href^='/app/spaces/s_wedding']").first.click()
        page.wait_for_url("**/app/spaces/s_wedding**", timeout=15000)
        page.wait_for_timeout(3000)
        page.screenshot(path=os.path.join(ARTIFACT_DIR, "verify_narayan_wedding_plan.png"))

        print("6. Checking Our Plans tab...")
        page.click("a[href='/app/plans']")
        page.wait_for_url("**/app/plans**", timeout=15000)
        page.wait_for_timeout(2000)
        page.screenshot(path=os.path.join(ARTIFACT_DIR, "verify_narayan_our_plans.png"))

        print("7. Checking Recommends & Private Surprises...")
        page.click("a[href='/app/recommends']")
        page.wait_for_url("**/app/recommends**", timeout=15000)
        page.wait_for_timeout(2000)
        page.screenshot(path=os.path.join(ARTIFACT_DIR, "verify_narayan_recommends.png"))

        print("8. Checking Tastes DNA...")
        page.click("a[href='/app/dna']")
        page.wait_for_url("**/app/dna**", timeout=15000)
        page.wait_for_timeout(2000)
        page.screenshot(path=os.path.join(ARTIFACT_DIR, "verify_narayan_dna.png"))

        browser.close()
        print("Verification completed successfully!")

if __name__ == "__main__":
    verify_full_profiles()

