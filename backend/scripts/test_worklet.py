import asyncio
from playwright.async_api import async_playwright

async def test_worklet():
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=True, channel='chrome')
        page = await b.new_page()
        page.on('console', lambda m: print('CONSOLE:', m.type, m.text))
        page.on('pageerror', lambda e: print('PAGE ERROR:', e))
        await page.goto('http://127.0.0.1:5173')
        js_code = """
        async () => {
            try {
                const ctx = new AudioContext();
                const code = "class Rec extends AudioWorkletProcessor { process(){ return true; } } registerProcessor('ww-rec', Rec);";
                const url = URL.createObjectURL(new Blob([code], { type: 'application/javascript' }));
                await ctx.audioWorklet.addModule(url);
                return 'SUCCESS';
            } catch (err) {
                return 'ERROR: ' + err.toString();
            }
        }
        """
        res = await page.evaluate(js_code)
        print('RESULT:', res)
        await b.close()

if __name__ == '__main__':
    asyncio.run(test_worklet())
