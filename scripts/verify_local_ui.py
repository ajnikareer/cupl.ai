import asyncio
import os
from playwright.async_api import async_playwright

BASE_URL = "http://127.0.0.1:8080"
ARTIFACT_DIR = r"C:\Users\admin\.gemini\antigravity\brain\6d8e9353-5c79-4cdf-92cf-1fafc99c77a9"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            channel="msedge",
            headless=True,
            args=["--use-fake-ui-for-media-stream", "--use-fake-device-for-media-stream"]
        )
        ctx = await browser.new_context(
            viewport={"width": 1440, "height": 920},
            permissions=["microphone"]
        )
        page = await ctx.new_page()

        # 1. Login with dev token
        print("Navigating to login...")
        await page.goto(f"{BASE_URL}/login")
        await page.evaluate("() => localStorage.setItem('ww_dev_token', 'dev-ajnikarnarayan')")

        # 2. Verify cupl AI Studio with new Avatar Medallion
        print("Verifying cupl AI Studio at /app/chat...")
        await page.goto(f"{BASE_URL}/app/chat")
        await page.wait_for_selector("text=Chat History", timeout=15000)
        await page.wait_for_timeout(1500)
        snap1 = os.path.join(ARTIFACT_DIR, "cupl_ai_studio_improved_avatar.png")
        await page.screenshot(path=snap1, full_page=False)
        print("Captured cupl_ai_studio_improved_avatar.png")

        # 3. Verify Home Page
        print("Verifying Home Page at /app...")
        await page.goto(f"{BASE_URL}/app")
        await page.wait_for_timeout(1500)
        snap2 = os.path.join(ARTIFACT_DIR, "cupl_home_improved_brand.png")
        await page.screenshot(path=snap2, full_page=False)
        print("Captured cupl_home_improved_brand.png")

        # 4. Verify My Profile
        print("Verifying My Profile at /app/me...")
        await page.goto(f"{BASE_URL}/app/me")
        await page.wait_for_selector("text=Cultural Roots & Heritage", timeout=15000)
        await page.wait_for_timeout(1500)
        snap3 = os.path.join(ARTIFACT_DIR, "cupl_profile_improved.png")
        await page.screenshot(path=snap3, full_page=False)
        print("Captured cupl_profile_improved.png")

        await browser.close()
        print("All local verification screenshots captured successfully!")

if __name__ == "__main__":
    asyncio.run(main())

