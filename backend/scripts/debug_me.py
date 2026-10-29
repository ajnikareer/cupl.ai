import asyncio
from playwright.async_api import async_playwright

async def debug_me():
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=True, channel="chrome")
        page = await b.new_page()
        page.on("console", lambda m: print("CONSOLE:", m.type, m.text))
        page.on("pageerror", lambda e: print("PAGE ERROR:", e))
        page.on("requestfailed", lambda r: print("FAILED REQ:", r.url, r.failure))
        page.on("response", lambda r: print("RESP:", r.status, r.url) if "api" in r.url else None)
        await page.goto("http://127.0.0.1:5173/login")
        await page.locator("button:has-text('Narayan')").click()
        await page.wait_for_url("**/app**")
        print("ON APP HOME. Navigating to /app/me...")
        await page.goto("http://127.0.0.1:5173/app/me")
        await page.wait_for_timeout(3000)
        await b.close()

if __name__ == "__main__":
    asyncio.run(debug_me())

