import time
from playwright.sync_api import sync_playwright

def capture_all_links():
    target_url = "https://dlive.sx/watch.php?id=450"
    captured_links = set()
    link_details = {}

    print("Launching advanced browser with auto-play & media emulation...")
    with sync_playwright() as p:
        # রিয়েল ব্রাউজার হিসেবে রান করার জন্য ফ্ল্যাগগুলো সাজানো
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
                '--autoplay-policy=no-user-gesture-required',
                '--enable-features=NetworkService,NetworkServiceInProcess'
            ]
        )
        
        # অডিও, ভিডিও এবং মিডিয়া পারমিশনসহ ফুল কনটেক্সট তৈরি
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            device_scale_factor=1,
            is_mobile=False,
            has_touch=False,
            permissions=["autoplay", "media"]
        )
        
        page = context.new_page()

        # ব্রাউজারকে শতভাগ রিয়েল হিউম্যান ক্রোম হিসেবে প্রুভ করার স্ক্রিপ্ট
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
            window.chrome = { runtime: {} };
            
            // ভিডিও অটো-প্লে ব্লক যাতে না হয়
            const origPlay = HTMLMediaElement.prototype.play;
            HTMLMediaElement.prototype.play = function() {
                return origPlay.apply(this, arguments).catch(err => {
                    console.log("Autoplay prevented handled:", err);
                });
            };
        """)

        # নেটওয়ার্ক রিকোয়েস্ট থেকে ভিডিওর যেকোনো ধরনের ম্যানিফেস্ট বা স্ট্রিম লিংক লুফে নেওয়া
        def handle_request(request):
            url = request.url
            # আপনার আইডিএম ব্রাউজার যেভাবে ভিডিও স্ট্রিম ধরে, ঠিক সেই প্যাটার্নগুলো এখানে ট্র্যাক করা হচ্ছে
            if any(ext in url for ext in [".m3u8", "playlist", "manifest", "index.m3u8", "tracks-v1a1"]):
                headers = request.headers
                referer = headers.get("referer", target_url)
                if url not in captured_links:
                    captured_links.add(url)
                    link_details[url] = referer
                    print(f"Captured Playable Link: {url}")

        page.on("request", handle_request)

        try:
            print(f"Navigating to {target_url}...")
            # পেজ লোড হওয়ার সাথে সাথে ভিডিও যেন নিজে থেকে প্লে হয় তার জন্য অপেক্ষা
            page.goto(target_url, timeout=60000, wait_until="domcontentloaded")
            
            print("Waiting for video player auto-load and stream request...")
            # ভিডিও প্লেয়ারের নিজস্ব রিকোয়েস্ট আসার জন্য পর্যাপ্ত সময় দেওয়া (১৫ সেকেন্ড)
            time.sleep(15)

        except Exception as e:
            print(f"Error during navigation: {e}")
        
        finally:
            browser.close()

    print(f"Total unique streaming links captured: {len(link_details)}")
    
    # রুট ডিরেক্টরিতে status.txt ফাইল তৈরি করা
    file_content = "--- DLive Auto-Capture Status ---\n"
    file_content += f"Target URL: {target_url}\n"
    file_content += f"Capture Time: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
    file_content += f"Total Links Found: {len(link_details)}\n\n"
    file_content += "--- Playable Streaming Links with Referer ---\n"

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
