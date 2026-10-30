import asyncio
from playwright.async_api import async_playwright

BASE_URL = "http://127.0.0.1:8080"
SNAP_PATH = r"C:\Users\admin\.gemini\antigravity\brain\6d8e9353-5c79-4cdf-92cf-1fafc99c77a9\laptop_14inch_fitted_view.png"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(channel="msedge", headless=True)
        # 14-inch laptop typical viewport with 125%/150% scaling: 1280 x 680
        ctx = await browser.new_context(viewport={"width": 1280, "height": 680})
        page = await ctx.new_page()

        await page.goto(f"{BASE_URL}/login")
        await page.evaluate("() => localStorage.setItem('ww_dev_token', 'dev-ajnikarnarayan')")

        await page.goto(f"{BASE_URL}/app/chat")
        await page.wait_for_selector("text=Chat History", timeout=12000)
        await page.wait_for_timeout(1500)

        await page.screenshot(path=SNAP_PATH, full_page=False)
        print(f"Captured 14-inch laptop screenshot: {SNAP_PATH}")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
