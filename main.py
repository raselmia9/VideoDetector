import time
from playwright.sync_api import sync_playwright

def capture_all_links():
    target_url = "https://dlive.sx/watch.php?id=450"
    # একাধিক লিংক ট্র্যাক করার জন্য পাইথন সেট (Set) ব্যবহার করা হলো যাতে ডুপ্লিকেট না হয়
    captured_links = set()
    link_details = {}

    print("Launching advanced stealth browser with ad-viewability emulation...")
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

        # অ্যাড ব্লক ডিটেকশন ও ভিজিবিলিটি চেক বাইপাস করার স্ক্রিপ্ট
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
            window.chrome = { runtime: {} };

            // অ্যাড এবং প্লেয়ার সবসময় দৃশ্যমান আছে বলে সাইটকে বিশ্বাস করানো
            Object.defineProperty(document, 'hidden', { get: () => false, configurable: true });
            Object.defineProperty(document, 'visibilityState', { get: () => 'visible', configurable: true });
            window.dispatchEvent(new Event('visibilitychange'));
            window.dispatchEvent(new Event('focus'));
        """)

        # নেটওয়ার্কের সমস্ত রিকোয়েস্ট মনিটর করে যতগুলো স্ট্রিম লিংক পাওয়া যায় ক্যাপচার করা
        def handle_request(request):
            url = request.url
            if ".m3u8" in url or "playlist" in url or "manifest" in url or "index.m3u8" in url:
                headers = request.headers
                referer = headers.get("referer", target_url)
                if url not in captured_links:
                    captured_links.add(url)
                    link_details[url] = referer
                    print(f"Captured Stream Link: {url}")

        page.on("request", handle_request)

        try:
            print(f"Navigating to {target_url}...")
            page.goto(target_url, timeout=50000, wait_until="networkidle")
            
            print("Emulating human interaction to trigger ads and real tokens...")
            time.sleep(6)

            # পেজ স্ক্রল করা যাতে অ্যাড ও প্লেয়ার রিয়েল ইউজার ভিউতে আসে
            page.mouse.wheel(0, 500)
            time.sleep(3)
            page.mouse.wheel(0, -500)
            time.sleep(2)

            # প্লেয়ার এবং বিজ্ঞাপনের ওপর একাধিকবার ক্লিক সিমুলেশন করা যাতে সাইট রিয়েল টোকেন দেয়
            try:
                page.mouse.click(960, 540)
                print("Clicked on player/ad area.")
                time.sleep(8)
                
                # আরও কিছু সেকেন্ড অপেক্ষা করা যাতে পরবর্তী সিকোয়েন্সের লিংকগুলোও রিসিভ হয়
                page.mouse.click(500, 300)
                time.sleep(6)
            except Exception as e:
                print(f"Interaction error: {e}")

        except Exception as e:
            print(f"Error during execution: {e}")
        
        finally:
            browser.close()

    print(f"Total unique streaming links captured: {len(link_details)}")
    
    # রুট ডিরেক্টরিতে status.txt ফাইল তৈরি করা
    file_content = "--- DLive Multi-Link Real Token Capture Status ---\n"
    file_content += f"Target URL: {target_url}\n"
    file_content += f"Capture Time: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
    file_content += f"Total Links Found: {len(link_details)}\n\n"
    file_content += "--- All Playable Streaming Links with Referer ---\n"

    if link_details:
        for idx, (link, referer) in enumerate(link_details.items(), 1):
            file_content += f"{idx}. {link}|Referer={referer}\n"
    else:
        file_content += "No valid streaming links captured.\n"

    with open("status.txt", "w", encoding="utf-8") as f:
        f.write(file_content)
    
    print("status.txt successfully generated in root directory.")

if __name__ == "__main__":
    capture_all_links()
