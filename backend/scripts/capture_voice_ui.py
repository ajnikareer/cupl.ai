import asyncio
from playwright.async_api import async_playwright

ARTIFACT_DIR = r"C:\Users\admin\.gemini\antigravity\brain\6c42d254-95bb-4cb6-9604-5ce8ffacfc0c"

async def capture_voice():
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=True, channel="chrome")
        context = await b.new_context(viewport={"width": 1440, "height": 900}, permissions=["microphone"])
        page = await context.new_page()

        print("Logging in...")
        await page.goto("http://127.0.0.1:5173/login")
        await page.locator("button:has-text('Narayan')").click()
        await page.wait_for_url("**/app**")

        # Click "Talk to WeaveWed" on home page
        print("Clicking 'Talk to WeaveWed' button...")
        talk_btn = page.locator("button:has-text('Talk to WeaveWed')").first
        await talk_btn.click()
        await page.wait_for_timeout(2000)

        await page.screenshot(path=f"{ARTIFACT_DIR}/v2_16_voice_overlay.png")
        print("Captured v2_16_voice_overlay.png")

        await b.close()
        print("Voice UI captured successfully!")

if __name__ == "__main__":
    asyncio.run(capture_voice())

