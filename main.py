import time
from playwright.sync_api import sync_playwright

def capture_links():
    target_url = "https://dlive.sx/watch.php?id=450"
    captured_links = {}

    print("Initializing ultra-stealth human browser context...")
    with sync_playwright() as p:
        # রিয়েল ব্রাউজারের মতো লঞ্চ করার জন্য বিভিন্ন ফ্ল্যাগ ব্যবহার
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
                '--disable-features=IsolateOrigins,site-per-process',
                '--lang=en-US,en'
            ]
        )
        
        # রিয়েল উইন্ডোজ ক্রোম ব্রাউজারের ফিঙ্গারপ্রিন্ট সেটআপ
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            device_scale_factor=1,
            is_mobile=False,
            has_touch=False,
            locale="en-US",
            timezone_id="Asia/Dhaka",
            permissions=["geolocation"],
            color_scheme="dark"
        )
        
        page = context.new_page()

        # বোট ধরা পড়ার সমস্ত আলামত (webdriver, plugins, languages) চিরতরে রিমুভ ও ওভাররাইড করা
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
            window.chrome = { runtime: {} };
            
            // লোকাল স্টোরেজ এবং সেশন স্টোরেজ সচল রাখা
            const storageMock = {
                getItem: (key) => storageMock[key] || null,
                setItem: (key, value) => storageMock[key] = value.toString(),
                removeItem: (key) => delete storageMock[key],
                clear: () => {}
            };
            Object.defineProperty(window, 'localStorage', { value: storageMock });
            Object.defineProperty(window, 'sessionStorage', { value: storageMock });
        """)

        # নেটওয়ার্ক রিকোয়েস্ট ইন্টারসেপ্ট করে নিখুঁত মেইনফেস্ট ও টোকেনযুক্ত লিংক ফিল্টার করা
        def handle_request(request):
            url = request.url
            if ".m3u8" in url or "playlist" in url or "manifest" in url:
                headers = request.headers
                referer = headers.get("referer", target_url)
                if url not in captured_links:
                    print(f"Captured Valid Stream: {url}")
                    captured_links[url] = referer

        page.on("request", handle_request)

        try:
            print(f"Navigating to {target_url} with human-like stealth...")
            # প্রথমে সাইটের মেইন ডোমেইনে গিয়ে লোকাল কুকিজ ও স্টোরেজ তৈরি করা
            page.goto("https://dlive.sx/", timeout=30000, wait_until="domcontentloaded")
            time.sleep(3)

            # এবার আসল টার্গেটে যাওয়া
            page.goto(target_url, timeout=40000, wait_until="networkidle")
            
            print("Waiting for player initialization and secure token generation...")
            time.sleep(12)

            # হিউম্যান বিহেভিওরের মতো মাউস মুভমেন্ট এবং ভিডিও প্লেয়ারে ক্লিক সিমুলেট করা
            try:
                page.mouse.move(300, 300)
                page.mouse.down()
                page.mouse.up()
                page.mouse.click(640, 360)
                print("Simulated human click on video player.")
                time.sleep(8) # টোকেন সহ রিকোয়েস্ট আসার জন্য পর্যাপ্ত সময় অপেক্ষা
            except Exception as e:
                print(f"Interaction skipped: {e}")

        except Exception as e:
            print(f"Error during browser execution: {e}")
        
        finally:
            browser.close()

    print("Saving captured data to status.txt...")
    file_content = "--- DLive Stream Capture Status (Stealth Mode) ---\n"
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
    
    print("status.txt successfully created in root directory.")

if __name__ == "__main__":
    capture_links()
    
