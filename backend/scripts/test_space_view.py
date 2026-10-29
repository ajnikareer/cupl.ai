import asyncio
from playwright.async_api import async_playwright

ARTIFACT_DIR = r"C:\Users\admin\.gemini\antigravity\brain\6c42d254-95bb-4cb6-9604-5ce8ffacfc0c"

async def test_space():
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=True, channel="chrome")
        context = await b.new_context(viewport={"width": 1440, "height": 900})
        page = await context.new_page()

        print("Logging in as Narayan...")
        await page.goto("http://127.0.0.1:5173/login")
        await page.locator("button:has-text('Narayan')").click()
        await page.wait_for_url("**/app**")

        # Click on the Wedding card
        print("Clicking on Wedding card...")
        await page.locator("text='Wedding'").first.click()
        await page.wait_for_url("**/app/spaces/**")
        await page.wait_for_timeout(2000)

        await page.screenshot(path=f"{ARTIFACT_DIR}/v2_10_space_view_details.png")
        print("Captured v2_10_space_view_details.png")

        # Fill in missing ceremonies in Details tab
        print("Filling ceremonies in Details tab...")
        # Check ceremonies buttons or inputs if available
        # Click on Plan tab
        await page.locator("button:has-text('Plan')").click()
        await page.wait_for_timeout(1500)
        await page.screenshot(path=f"{ARTIFACT_DIR}/v2_11_space_view_plan.png")
        print("Captured v2_11_space_view_plan.png")

        # Click on Budget tab
        await page.locator("button:has-text('Budget')").click()
        await page.wait_for_timeout(1500)
        await page.screenshot(path=f"{ARTIFACT_DIR}/v2_12_space_view_budget.png")
        print("Captured v2_12_space_view_budget.png")

        await b.close()
        print("Space view testing done!")

if __name__ == "__main__":
    asyncio.run(test_space())

