from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(channel='msedge', headless=True)
    page = browser.new_page(viewport={'width': 1440, 'height': 900})
    page.goto('http://127.0.0.1:8080/login')
    page.evaluate("() => localStorage.setItem('ww_dev_token', 'dev-cupl_star_2')")
    page.goto('http://127.0.0.1:8080/app', wait_until='networkidle')
    page.wait_for_timeout(1000)
    page.screenshot(path=r'C:\Users\admin\.gemini\antigravity\brain\6d8e9353-5c79-4cdf-92cf-1fafc99c77a9\preview_showcase_amruta_home.png')
    browser.close()
    print('Amruta home preview saved!')
