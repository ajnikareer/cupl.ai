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

        # 2. Go to Event Space (Wedding Plan)
        print("Verifying Event Plan with Filter Chips and Card Grid...")
        await page.goto(f"{BASE_URL}/app/spaces/s_7589d6245e7d9cbf")
        await page.wait_for_timeout(3000)

        # Ensure Plan tab is active
        snap1 = os.path.join(ARTIFACT_DIR, "preview_event_plan_card_grid.png")
        await page.screenshot(path=snap1, full_page=False)
        print("Captured preview_event_plan_card_grid.png")

        # 3. Click "Venue" chip
        print("Testing filter chip click...")
        venue_btn = page.locator("button:has-text('Venue')").first
        if await venue_btn.is_visible():
            await venue_btn.click()
            await page.wait_for_timeout(1000)
            snap2 = os.path.join(ARTIFACT_DIR, "preview_event_plan_venue_filter.png")
            await page.screenshot(path=snap2, full_page=False)
            print("Captured preview_event_plan_venue_filter.png")

        # 4. Click a card to open Details Modal
        print("Testing card modal click...")
        first_card = page.locator("h4").first
        if await first_card.is_visible():
            await first_card.click()
            await page.wait_for_timeout(1000)
            snap3 = os.path.join(ARTIFACT_DIR, "preview_event_item_modal.png")
            await page.screenshot(path=snap3, full_page=False)
            print("Captured preview_event_item_modal.png")
            # Close modal
            close_btn = page.locator("button[aria-label='Close']").first
            if await close_btn.is_visible():
                await close_btn.click()
                await page.wait_for_timeout(500)

        # 5. Go to Plans page
        print("Verifying /app/plans Card Grid...")
        await page.goto(f"{BASE_URL}/app/plans")
        await page.wait_for_timeout(2000)
        snap4 = os.path.join(ARTIFACT_DIR, "preview_plans_page_card_grid.png")
        await page.screenshot(path=snap4, full_page=False)
        print("Captured preview_plans_page_card_grid.png")

        # 6. Click a plan card to open Details Modal
        plan_card = page.locator("h4").first
        if await plan_card.is_visible():
            await plan_card.click()
            await page.wait_for_timeout(1000)
            snap5 = os.path.join(ARTIFACT_DIR, "preview_plans_modal.png")
            await page.screenshot(path=snap5, full_page=False)
            print("Captured preview_plans_modal.png")

        await browser.close()
        print("All UI verifications complete!")

if __name__ == "__main__":
    asyncio.run(main())

