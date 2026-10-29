import asyncio
from playwright.async_api import async_playwright

ARTIFACT_DIR = r"C:\Users\admin\.gemini\antigravity\brain\6c42d254-95bb-4cb6-9604-5ce8ffacfc0c"

async def capture_plan():
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=True, channel="chrome")
        context = await b.new_context(viewport={"width": 1440, "height": 900})
        page = await context.new_page()

        print("Logging in...")
        await page.goto("http://127.0.0.1:5173/login")
        await page.locator("button:has-text('Narayan')").click()
        await page.wait_for_url("**/app**")

        # Go directly to wedding space
        print("Opening Wedding space...")
        await page.goto("http://127.0.0.1:5173/app/spaces/s_8b4437164f0df241")
        await page.wait_for_selector(".card", timeout=10000)
        await page.wait_for_timeout(2000)

        # We are already on Plan tab
        print("Waiting for Plan items to render...")
        await page.wait_for_timeout(2000)
        await page.screenshot(path=f"{ARTIFACT_DIR}/v2_13_synthesized_plan.png", full_page=True)
        print("Captured v2_13_synthesized_plan.png")

        # Click on Budget tab
        print("Clicking Budget tab...")
        await page.get_by_role("button", name="Budget", exact=True).click()
        await page.wait_for_timeout(2000)
        await page.screenshot(path=f"{ARTIFACT_DIR}/v2_14_smart_budget.png")
        print("Captured v2_14_smart_budget.png")

        # Click on To-dos tab
        print("Clicking To-dos tab...")
        await page.get_by_role("button", name="To-dos", exact=True).click()
        await page.wait_for_timeout(2000)
        await page.screenshot(path=f"{ARTIFACT_DIR}/v2_15_smart_todos.png")
        print("Captured v2_15_smart_todos.png")

        await b.close()
        print("Plan UI screenshots captured!")

if __name__ == "__main__":
    asyncio.run(capture_plan())
