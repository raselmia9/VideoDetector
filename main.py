import time
from playwright.sync_api import sync_playwright

def capture_all_links():
    target_url = "https://dlive.sx/watch.php?id=450"
    captured_links = set()
    link_details = {}

    print("Launching advanced browser with media emulation...")
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
                '--autoplay-policy=no-user-gesture-required',
                '--enable-features=NetworkService,NetworkServiceInProcess'
            ]
        )
        
        # 'autoplay' পারমিশনটি সরিয়ে শুধু বৈধ পারমিশনগুলো রাখা হয়েছে
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            device_scale_factor=1,
            is_mobile=False,
            has_touch=False,
            permissions=["media"]
        )
        
        page = context.new_page()

        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
            window.chrome = { runtime: {} };
            
            const origPlay = HTMLMediaElement.prototype.play;
            HTMLMediaElement.prototype.play = function() {
                return origPlay.apply(this, arguments).catch(err => {
                    console.log("Autoplay prevented handled:", err);
                });
            };
        """)

        def handle_request(request):
            url = request.url
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
            page.goto(target_url, timeout=60000, wait_until="domcontentloaded")
            
            print("Waiting for video player auto-load and stream request...")
            time.sleep(15)

        except Exception as e:
            print(f"Error during navigation: {e}")
        
        finally:
            browser.close()

    print(f"Total unique streaming links captured: {len(link_details)}")
    
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
