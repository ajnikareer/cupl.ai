import asyncio
from playwright.async_api import async_playwright

ARTIFACT_DIR = r"C:\Users\admin\.gemini\antigravity\brain\6c42d254-95bb-4cb6-9604-5ce8ffacfc0c"

async def test_chat():
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=True, channel="chrome")
        context = await b.new_context(viewport={"width": 1440, "height": 900})
        page = await context.new_page()

        page.on("console", lambda m: print("CONSOLE:", m.type, m.text))
        page.on("pageerror", lambda e: print("PAGE ERROR:", e))

        # 1. Login
        print("Logging in as Narayan...")
        await page.goto("http://127.0.0.1:5173/login")
        await page.locator("button:has-text('Narayan')").click()
        await page.wait_for_url("**/app**")

        # 2. Go to Chat
        print("Navigating to Chat...")
        await page.goto("http://127.0.0.1:5173/app/chat")
        await page.wait_for_selector("input[aria-label='Message']", timeout=5000)

        # 3. Send message to Director
        msg = "We're planning our royal wedding in Udaipur for next February! We'll have about 250 guests and a budget of 40 lakhs. We love Sufi music and lakeside heritage palaces."
        print(f"Sending message: {msg}")
        await page.fill("input[aria-label='Message']", msg)
        await page.keyboard.press("Enter")

        # 4. Wait for response
        print("Waiting for AI Director response (Gemini 2.5 Flash)...")
        # Wait until agent bubble appears
        await page.wait_for_selector(".rise:has-text('Udaipur'), .rise:has-text('wedding'), .rise:has-text('palace'), .rise:has-text('WeaveWed')", timeout=30000)
        await page.wait_for_timeout(4000)

        await page.screenshot(path=f"{ARTIFACT_DIR}/v2_07_chat_conversation.png")
        print("Captured v2_07_chat_conversation.png")

        # Check spaces page now
        await page.goto("http://127.0.0.1:5173/app/spaces")
        await page.wait_for_timeout(2000)
        await page.screenshot(path=f"{ARTIFACT_DIR}/v2_08_spaces_after_chat.png")
        print("Captured v2_08_spaces_after_chat.png")

        # Check home page now
        await page.goto("http://127.0.0.1:5173/app")
        await page.wait_for_timeout(2000)
        await page.screenshot(path=f"{ARTIFACT_DIR}/v2_09_home_with_event.png")
        print("Captured v2_09_home_with_event.png")

        await b.close()
        print("Chat conversation flow test finished!")

if __name__ == "__main__":
    asyncio.run(test_chat())

