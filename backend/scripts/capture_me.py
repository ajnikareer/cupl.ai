import asyncio
from playwright.async_api import async_playwright

async def check():
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=True, channel="chrome")
        context = await b.new_context(viewport={"width": 1440, "height": 900})
        page = await context.new_page()
        await page.goto("http://127.0.0.1:5173/login")
        await page.locator("button:has-text('Narayan')").click()
        await page.wait_for_url("**/app**")
        await page.goto("http://127.0.0.1:5173/app/me")
        await page.wait_for_selector(".card", timeout=8000)
        await page.screenshot(path=r"C:\Users\admin\.gemini\antigravity\brain\6c42d254-95bb-4cb6-9604-5ce8ffacfc0c\v2_06_me.png")
        print("Captured v2_06_me.png successfully!")
        await b.close()

if __name__ == "__main__":
    asyncio.run(check())

