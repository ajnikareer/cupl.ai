import asyncio
import os
from playwright.async_api import async_playwright

ARTIFACT_DIR = r"C:\Users\admin\.gemini\antigravity\brain\6d8e9353-5c79-4cdf-92cf-1fafc99c77a9"

async def test_full_flow():
    async with async_playwright() as p:
        browser = await p.chromium.launch(channel="msedge", headless=True)
        ctx = await browser.new_context(viewport={"width": 1440, "height": 950})
        page = await ctx.new_page()

        await page.goto("https://weavewed-v2-633286673637.us-central1.run.app/login")
        await page.evaluate("""() => {
            localStorage.setItem('ww_dev_token', 'dev-ajnikarnarayan');
        }""")

        # 1. Active Recommends View
        await page.goto("https://weavewed-v2-633286673637.us-central1.run.app/app/recommends")
        await page.wait_for_load_state("networkidle")
        await page.wait_for_timeout(2000)

        p1 = os.path.join(ARTIFACT_DIR, "weavetwo_recommends_active_live.png")
        await page.screenshot(path=p1, full_page=False)
        print("Captured p1:", p1)

        # 2. Click "What's New" (Refresh / Rotate)
        refresh_btn = page.locator("button:has-text(\"What's New\")")
        if await refresh_btn.count() > 0:
            print("Clicking What's New...")
            await refresh_btn.click()
            await page.wait_for_timeout(2500)
            p2 = os.path.join(ARTIFACT_DIR, "weavetwo_recommends_refreshed_live.png")
            await page.screenshot(path=p2, full_page=False)
            print("Captured p2 (refreshed):", p2)

        # 3. Click "Recommends: ON" to test Pause
        toggle_btn = page.locator("button:has-text(\"Recommends: ON\")")
        if await toggle_btn.count() > 0:
            print("Pausing recommendations...")
            await toggle_btn.click()
            await page.wait_for_timeout(2000)
            p3 = os.path.join(ARTIFACT_DIR, "weavetwo_recommends_paused_live.png")
            await page.screenshot(path=p3, full_page=False)
            print("Captured p3 (paused):", p3)

            # 4. Turn back ON
            turn_on_btn = page.locator("button:has-text(\"Turn ON Recommendations\")")
            if await turn_on_btn.count() > 0:
                print("Re-enabling recommendations...")
                await turn_on_btn.click()
                await page.wait_for_timeout(2000)
                print("Successfully re-enabled recommendations!")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_full_flow())

