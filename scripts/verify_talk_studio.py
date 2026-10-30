import asyncio
import os
from playwright.async_api import async_playwright

BASE_URL = "https://weavewed-v2-633286673637.us-central1.run.app"
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

        # 1. Set dev token on root domain then go to /app
        await page.goto(f"{BASE_URL}/login")
        await page.evaluate("() => localStorage.setItem('ww_dev_token', 'dev-ajnikarnarayan')")
        await page.goto(f"{BASE_URL}/app")

        # Wait for the user profile & partner to resolve in header
        await page.wait_for_selector("text=Planning together with", timeout=12000)
        await page.wait_for_timeout(500)
        snap1 = os.path.join(ARTIFACT_DIR, "cupl_home_live.png")
        await page.screenshot(path=snap1, full_page=False)
        print("Captured cupl_home_live.png")

        # 2. Navigate to cupl Suggests
        await page.goto(f"{BASE_URL}/app/recommends")
        await page.wait_for_selector("text=cupl Suggests", timeout=10000)
        await page.wait_for_timeout(500)
        snap2 = os.path.join(ARTIFACT_DIR, "cupl_suggests_live.png")
        await page.screenshot(path=snap2, full_page=False)
        print("Captured cupl_suggests_live.png")

        # 3. Navigate to Talk Studio
        await page.goto(f"{BASE_URL}/app/chat")
        await page.wait_for_selector("text=cupl AI Concierge", timeout=10000)
        await page.wait_for_timeout(500)
        snap3 = os.path.join(ARTIFACT_DIR, "cupl_talk_studio_live.png")
        await page.screenshot(path=snap3, full_page=False)
        print("Captured cupl_talk_studio_live.png")

        await browser.close()
        print("All verification screenshots captured successfully!")

if __name__ == "__main__":
    asyncio.run(main())
