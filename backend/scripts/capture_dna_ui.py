import asyncio
import urllib.request
import json
from playwright.async_api import async_playwright

ARTIFACT_DIR = r"C:\Users\admin\.gemini\antigravity\brain\6c42d254-95bb-4cb6-9604-5ce8ffacfc0c"

# Refresh DNA via API
req = urllib.request.Request("http://127.0.0.1:8080/api/dna/refresh", headers={"Authorization": "Bearer dev-narayan"}, method="POST")
try:
    with urllib.request.urlopen(req) as resp:
        print("DNA refresh:", json.loads(resp.read().decode()))
except Exception as e:
    print("DNA error:", e)

async def capture_dna():
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=True, channel="chrome")
        context = await b.new_context(viewport={"width": 1440, "height": 900})
        page = await context.new_page()

        await page.goto("http://127.0.0.1:5173/login")
        await page.locator("button:has-text('Narayan')").click()
        await page.wait_for_url("**/app**")

        await page.goto("http://127.0.0.1:5173/app/dna")
        await page.wait_for_timeout(2500)
        await page.screenshot(path=f"{ARTIFACT_DIR}/v2_17_couple_dna.png", full_page=True)
        print("Captured v2_17_couple_dna.png")
        await b.close()

if __name__ == "__main__":
    asyncio.run(capture_dna())

