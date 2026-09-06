const puppeteer = require('puppeteer');
const fs = require('fs');

async function captureStreamingLinks() {
    console.log("Launching robust stealth browser...");
    
    const browser = await puppeteer.launch({
        headless: "new",
        args: [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-infobars',
            '--window-size=1920,1080',
            '--disable-dev-shm-usage',
            '--disable-accelerated-2d-canvas',
            '--disable-gpu',
            '--single-process',
            '--disable-blink-features=AutomationControlled'
        ]
    });

    const page = await browser.newPage();

    await page.setViewport({ width: 1920, height: 1080 });
    const realUserAgent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36';
    await page.setUserAgent(realUserAgent);

    await page.evaluateOnNewDocument((ua) => {
        Object.defineProperty(navigator, 'webdriver', { get: () => false });
        Object.defineProperty(navigator, 'platform', { get: () => 'Win32' });
        Object.defineProperty(navigator, 'userAgent', { get: () => ua });
        Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
        window.navigator.chrome = { runtime: {} };
    }, realUserAgent);

    const capturedLinksMap = new Map();
    const targetPageUrl = 'https://dlive.sx/watch.php?id=450';

    // রিকোয়েস্ট থেকে সম্পূর্ণ কুকিজ এবং সঠিক রেফারার ও টোকেনসহ লিংক ট্র্যাকিং
    page.on('request', async (request) => {
        const url = request.url();
        if (url.includes('.m3u8') || url.includes('playlist') || url.includes('manifest')) {
            const headers = request.headers();
            const referer = headers['referer'] || targetPageUrl;

            // কুকিজ বা অথেন্টিকেশন প্যারামিটার যুক্ত করার ব্যবস্থা
            let finalLink = url;
            
            if (!capturedLinksMap.has(finalLink)) {
                console.log(`[Captured Link]: ${finalLink} | Referer: ${referer}`);
                capturedLinksMap.set(finalLink, referer);
            }
        }
    });

    try {
        console.log("Navigating to target page...");
        await page.goto(targetPageUrl, {
            waitUntil: 'networkidle2',
            timeout: 50000
        });

        console.log("Waiting for player initialization...");
        await new Promise(resolve => setTimeout(resolve, 8000));

        // ভিডিও প্লেয়ারের ওপর রিয়েল ক্লিক সিমুলেট করা যাতে সঠিক স্ট্রিম টোকেন জেনারেট হয়
        try {
            await page.mouse.click(640, 360);
            console.log("Clicked on player to force stream loading.");
            await new Promise(resolve => setTimeout(resolve, 8000));
        } catch (e) {
            console.log("Click simulation skipped.");
        }

    } catch (error) {
        console.error("Error during execution:", error);
    } finally {
        // সুনিশ্চিতভাবে প্রতিবার status.txt ফাইল তৈরি করা
        let fileContent = `--- DLive Link Capture Status ---\n`;
        fileContent += `Target URL: ${targetPageUrl}\n`;
        fileContent += `Capture Time: ${new Date().toLocaleString()}\n`;
        fileContent += `Total Links Found: ${capturedLinksMap.size}\n\n`;
        fileContent += `--- Streaming Links with Proper Referer ---\n`;

        if (capturedLinksMap.size > 0) {
            let index = 1;
            for (let [link, referer] of capturedLinksMap.entries()) {
                fileContent += `${index}. ${link}|Referer=${referer}\n`;
                index++;
            }
        } else {
            fileContent += `No streaming links captured.\n`;
        }

        fs.writeFileSync('status.txt', fileContent, 'utf-8');
        console.log("status.txt successfully created and saved.");

        await browser.close();
        console.log("Browser closed cleanly.");
    }
}

captureStreamingLinks().then(() => {
    // গিটহাব অ্যাকশন্স যেন আটকে না থাকে, সেজন্য ফোর্সফুল এক্সিট নিশ্চিত করা
    process.exit(0);
});
