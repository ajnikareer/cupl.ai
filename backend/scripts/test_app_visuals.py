import asyncio
from playwright.async_api import async_playwright

ARTIFACT_DIR = r"C:\Users\admin\.gemini\antigravity\brain\6c42d254-95bb-4cb6-9604-5ce8ffacfc0c"

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, channel="chrome")
        context = await browser.new_context(viewport={"width": 1440, "height": 900})
        page = await context.new_page()

        print("Navigating to http://127.0.0.1:5173/login...")
        await page.goto("http://127.0.0.1:5173/login", wait_until="networkidle")
        await page.screenshot(path=f"{ARTIFACT_DIR}/v2_01_login.png")
        print("Captured v2_01_login.png")

        # Click Narayan (Groom) 1-click login button
        print("Clicking Narayan login button...")
        groom_btn = page.locator("button:has-text('Narayan')")
        await groom_btn.wait_for(state="visible", timeout=5000)
        await groom_btn.click()
        await page.wait_for_url("**/app**", timeout=10000)
        await page.wait_for_timeout(3000)
        await page.screenshot(path=f"{ARTIFACT_DIR}/v2_02_home.png")
        print("Captured v2_02_home.png")

        # Navigate to Chat
        print("Navigating to /app/chat...")
        await page.goto("http://127.0.0.1:5173/app/chat", wait_until="networkidle")
        await page.wait_for_timeout(1500)
        await page.screenshot(path=f"{ARTIFACT_DIR}/v2_03_chat.png")
        print("Captured v2_03_chat.png")

        # Navigate to Spaces
        print("Navigating to /app/spaces...")
        await page.goto("http://127.0.0.1:5173/app/spaces", wait_until="networkidle")
        await page.wait_for_timeout(1500)
        await page.screenshot(path=f"{ARTIFACT_DIR}/v2_04_spaces.png")
        print("Captured v2_04_spaces.png")

        # Navigate to Couple DNA
        print("Navigating to /app/dna...")
        await page.goto("http://127.0.0.1:5173/app/dna", wait_until="networkidle")
        await page.wait_for_timeout(1500)
        await page.screenshot(path=f"{ARTIFACT_DIR}/v2_05_dna.png")
        print("Captured v2_05_dna.png")

        # Navigate to Me (Tastes & Profile)
        print("Navigating to /app/me...")
        await page.goto("http://127.0.0.1:5173/app/me", wait_until="networkidle")
        await page.wait_for_timeout(1500)
        await page.screenshot(path=f"{ARTIFACT_DIR}/v2_06_me.png")
        print("Captured v2_06_me.png")

        await browser.close()
        print("All visual checks completed successfully!")

if __name__ == "__main__":
    asyncio.run(run())
