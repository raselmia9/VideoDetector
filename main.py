import time
from playwright.sync_api import sync_playwright

def capture_links():
    target_url = "https://dlive.sx/watch.php?id=450"
    captured_links = {}

    print("Launching browser...")
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu'
            ]
        )
        
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080}
        )
        
        page = context.new_page()

        def handle_request(request):
            url = request.url
            if ".m3u8" in url or "playlist" in url or "manifest" in url:
                headers = request.headers
                referer = headers.get("referer", target_url)
                if url not in captured_links:
                    print(f"Captured: {url}")
                    captured_links[url] = referer

        page.on("request", handle_request)

        try:
            print(f"Navigating to {target_url}...")
            page.goto(target_url, timeout=40000, wait_until="domcontentloaded")
            
            time.sleep(10)

            try:
                page.mouse.click(640, 360)
                print("Clicked on player.")
                time.sleep(6)
            except Exception as e:
                print(f"Click skipped: {e}")

        except Exception as e:
            print(f"Error during navigation: {e}")
        
        finally:
            browser.close()

    print("Saving results to status.txt...")
    file_content = "--- DLive Python Capture Status ---\n"
    file_content += f"Target URL: {target_url}\n"
    file_content += f"Capture Time: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
    file_content += f"Total Links Found: {len(captured_links)}\n\n"
    file_content += "--- Streaming Links with Referer ---\n"

    if captured_links:
        for idx, (link, referer) in enumerate(captured_links.items(), 1):
            file_content += f"{idx}. {link}|Referer={referer}\n"
    else:
        file_content += "No streaming links captured.\n"

    with open("status.txt", "w", encoding="utf-8") as f:
        f.write(file_content)
    
    print("status.txt created successfully.")

if __name__ == "__main__":
    capture_links()
