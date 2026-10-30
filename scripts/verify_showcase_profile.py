import os
import time
from playwright.sync_api import sync_playwright

ARTIFACT_DIR = r"C:\Users\admin\.gemini\antigravity\brain\6d8e9353-5c79-4cdf-92cf-1fafc99c77a9"

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        # 1. Login page
        print("Visiting /login...")
        page.goto("http://127.0.0.1:8080/login", wait_until="networkidle")
        page.screenshot(path=os.path.join(ARTIFACT_DIR, "preview_showcase_login.png"))
        print("Saved preview_showcase_login.png")

        # Set dev token
        page.evaluate("() => localStorage.setItem('ww_dev_token', 'dev-cupl_star_1')")

        # 2. Home page
        print("Visiting /app...")
        page.goto("http://127.0.0.1:8080/app", wait_until="networkidle")
        page.wait_for_timeout(1500)
        page.screenshot(path=os.path.join(ARTIFACT_DIR, "preview_showcase_home.png"))
        print("Saved preview_showcase_home.png")

        # 3. Chat page
        print("Visiting /app/chat...")
        page.goto("http://127.0.0.1:8080/app/chat", wait_until="networkidle")
        page.wait_for_timeout(2000)
        page.screenshot(path=os.path.join(ARTIFACT_DIR, "preview_showcase_chat.png"))
        print("Saved preview_showcase_chat.png")

        # 4. Space View (The Royal Wedding)
        print("Visiting /app/spaces/s_cupl_star_wedding...")
        page.goto("http://127.0.0.1:8080/app/spaces/s_cupl_star_wedding", wait_until="networkidle")
        page.wait_for_timeout(1500)
        page.screenshot(path=os.path.join(ARTIFACT_DIR, "preview_showcase_space.png"))
        print("Saved preview_showcase_space.png")

        # 5. Plans page
        print("Visiting /app/plans...")
        page.goto("http://127.0.0.1:8080/app/plans", wait_until="networkidle")
        page.wait_for_timeout(1500)
        page.screenshot(path=os.path.join(ARTIFACT_DIR, "preview_showcase_plans.png"))
        print("Saved preview_showcase_plans.png")

        # 6. Recommends page
        print("Visiting /app/recommends...")
        page.goto("http://127.0.0.1:8080/app/recommends", wait_until="networkidle")
        page.wait_for_timeout(1500)
        page.screenshot(path=os.path.join(ARTIFACT_DIR, "preview_showcase_recommends.png"))
        print("Saved preview_showcase_recommends.png")

        # 7. Taste DNA
        print("Visiting /app/dna...")
        page.goto("http://127.0.0.1:8080/app/dna", wait_until="networkidle")
        page.wait_for_timeout(1500)
        page.screenshot(path=os.path.join(ARTIFACT_DIR, "preview_showcase_dna.png"))
        print("Saved preview_showcase_dna.png")

        # 8. Surprises
        print("Visiting /app/surprises...")
        page.goto("http://127.0.0.1:8080/app/surprises", wait_until="networkidle")
        page.wait_for_timeout(1500)
        page.screenshot(path=os.path.join(ARTIFACT_DIR, "preview_showcase_surprises.png"))
        print("Saved preview_showcase_surprises.png")

        browser.close()
        print("All showcase previews captured successfully!")

if __name__ == "__main__":
    run()
