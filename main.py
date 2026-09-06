import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        # গিটহাব অ্যাকশন্সের জন্য headless=True রাখতে হবে
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        # নেটওয়ার্ক রিকোয়েস্ট মনিটর করার জন্য
        page.on("request", lambda request: print(f">> Request: {request.url}") if ".m3u8" in request.url else None)

        print("Navigating to page...")
        await page.goto("https://dlive.sx/watch.php?id=450", timeout=60000)
        
        # ভিডিও লোড হওয়ার জন্য কিছু সময় অপেক্ষা করা
        await asyncio.sleep(10)
        await browser.close()

asyncio.run(run())
