import time
from playwright.sync_api import sync_playwright

def capture_links():
    target_url = "https://dlive.sx/watch.php?id=450"
    captured_links = {}

    print("Launching stealth browser with visibility & ad-emulation...")
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-infobars',
                '--window-size=1920,1080',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--disable-blink-features=AutomationControlled',
                '--autoplay-policy=no-user-gesture-required'
            ]
        )
        
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            device_scale_factor=1,
            is_mobile=False,
            has_touch=False
        )
        
        page = context.new_page()

        # বোট এবং ভিজিবিলিটি চেক বাইপাস করার জন্য স্ক্রিপ্ট (যাতে সাইট মনে করে বিজ্ঞাপন ও প্লেয়ার সামনে দৃশ্যমান আছে)
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
            window.chrome = { runtime: {} };

            // ভিজিবিলিটি এমুলেশন যাতে ট্যাব সবসময় ফোকাসড এবং দৃশ্যমান থাকে (ডেমো টোকেন রোধ করতে)
            Object.defineProperty(document, 'hidden', { get: () => false, configurable: true });
            Object.defineProperty(document, 'visibilityState', { get: () => 'visible', configurable: true });
            window.dispatchEvent(new Event('visibilitychange'));
            window.dispatchEvent(new Event('focus'));
        """)

        def handle_request(request):
            url = request.url
            # আসল মাস্টার প্লেলিস্ট এবং প্রিমিয়াম টোকেনযুক্ত লিংক ফিল্টার করা
            if ".m3u8" in url or "playlist" in url or "manifest" in url:
                headers = request.headers
                referer = headers.get("referer", target_url)
                if url not in captured_links:
                    print(f"Captured Valid Token Link: {url}")
                    captured_links[url] = referer

        page.on("request", handle_request)

        try:
            print(f"Navigating to {target_url}...")
            page.goto(target_url, timeout=45000, wait_until="networkidle")
            
            print("Emulating human interaction, scrolling, and ad visibility...")
            time.sleep(5)

            # পেজ স্ক্রল করা যাতে বিজ্ঞাপন এবং প্লেয়ার রিয়েল ইউজার ভিউতে আসে
            page.mouse.wheel(0, 400)
            time.sleep(3)
            page.mouse.wheel(0, -400)
            time.sleep(2)

            # ভিডিও প্লেয়ার এবং বিজ্ঞাপনের ওপর রিয়েল ক্লিক সিমুলেশন
            try:
                page.mouse.click(960, 540) # স্ক্রিনের ঠিক মাঝখানে ক্লিক
                print("Clicked on video player / ad area to trigger real token.")
                time.sleep(10) # টোকেন জেনারেট হওয়ার জন্য পর্যাপ্ত সময় অপেক্ষা
            except Exception as e:
                print(f"Click interaction error: {e}")

        except Exception as e:
            print(f"Error during execution: {e}")
        
        finally:
            browser.close()

    print("Generating status.txt file...")
    file_content = "--- DLive Real Token Capture Status ---\n"
    file_content += f"Target URL: {target_url}\n"
    file_content += f"Capture Time: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
    file_content += f"Total Links Found: {len(captured_links)}\n\n"
    file_content += "--- Playable Streaming Links with Referer ---\n"

    if captured_links:
        for idx, (link, referer) in enumerate(captured_links.items(), 1):
            file_content += f"{idx}. {link}|Referer={referer}\n"
    else:
        file_content += "No valid streaming links captured.\n"

    with open("status.txt", "w", encoding="utf-8") as f:
        f.write(file_content)
    
    print("status.txt successfully created.")

if __name__ == "__main__":
    capture_links()
