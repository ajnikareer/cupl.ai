import asyncio
from playwright.async_api import async_playwright

async def verify_live():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            channel="msedge",
            headless=True
        )
        page = await browser.new_page(viewport={'width': 1440, 'height': 900})
        await page.goto('https://weavewed-v2-633286673637.us-central1.run.app/login')
        await page.evaluate("() => localStorage.setItem('ww_dev_token', 'dev-ajnikarnarayan')")
        await page.goto('https://weavewed-v2-633286673637.us-central1.run.app/app/spaces/s_7589d6245e7d9cbf')
        await page.wait_for_timeout(3500)
        
        # Check filter chips presence
        all_chip = await page.locator("button:has-text('All')").first.is_visible()
        venue_chip = await page.locator("button:has-text('Venue')").first.is_visible()
        print('Live filter chips visible:', all_chip, venue_chip)
        
        # Check that old input is gone
        old_input = await page.locator("input[placeholder*='Ask for a change']").count()
        print('Old search input count (should be 0):', old_input)
        
        # Check card grid
        cards_count = await page.locator("h4").count()
        print('Live card titles count:', cards_count)
        
        await page.screenshot(path=r'C:\Users\admin\.gemini\antigravity\brain\6d8e9353-5c79-4cdf-92cf-1fafc99c77a9\preview_live_cloudrun_verified.png')
        await browser.close()
        print('Live Cloud Run verification screenshot saved!')

if __name__ == "__main__":
    asyncio.run(verify_live())

