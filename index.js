const puppeteer = require('puppeteer');
const fs = require('fs');

async function captureStreamingLinks() {
    console.log("Launching stealth browser with proper device signature...");
    
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

    // একদম রিয়েল ডেস্কটপ ডিভাইসের ভিউপোর্ট ও সঠিক উইন্ডোজ ক্রোম ইউজার-এজেন্ট সেট করা
    await page.setViewport({ width: 1920, height: 1080 });
    const realUserAgent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36';
    await page.setUserAgent(realUserAgent);

    // ডিভাইসভিত্তিক সঠিক প্ল্যাটফর্ম ও হেডার টোকেন জেনারেট করার জন্য ওভাররাইড
    await page.evaluateOnNewDocument((ua) => {
        Object.defineProperty(navigator, 'webdriver', { get: () => false });
        Object.defineProperty(navigator, 'platform', { get: () => 'Win32' });
        Object.defineProperty(navigator, 'userAgent', { get: () => ua });
        Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
        
        window.navigator.chrome = {
            runtime: {},
        };
    }, realUserAgent);

    const capturedLinksMap = new Map();
    const targetPageUrl = 'https://dlive.sx/watch.php?id=450';

    // নেটওয়ার্ক রিকোয়েস্ট ইন্টারসেপ্ট করা
    page.on('request', (request) => {
        const url = request.url();
        if (url.includes('.m3u8') || url.includes('playlist') || url.includes('manifest')) {
            const headers = request.headers();
            const referer = headers['referer'] || targetPageUrl;

            if (!capturedLinksMap.has(url)) {
                console.log(`[Captured Link]: ${url} | Referer: ${referer}`);
                capturedLinksMap.set(url, referer);
            }
        }
    });

    try {
        console.log("Navigating to target page...");
        await page.goto(targetPageUrl, {
            waitUntil: 'domcontentloaded',
            timeout: 40000
        });

        console.log("Waiting for video player and token generation...");
        // ভিডিও প্লেয়ার লোড হওয়ার জন্য এবং টোকেন সহ রিকোয়েস্ট আসার জন্য নির্দিষ্ট সময় অপেক্ষা (১২ সেকেন্ড)
        await new Promise(resolve => setTimeout(resolve, 12000));

        // ভিডিও বা প্লেয়ার ট্রিগার করার জন্য ক্লিক সিমুলেশন
        try {
            await page.mouse.click(640, 360);
            console.log("Simulated human click on player.");
            await new Promise(resolve => setTimeout(resolve, 6000)); // ক্লিক করার পর লিংকের জন্য আরও ৬ সেকেন্ড অপেক্ষা
        } catch (e) {
            console.log("Click simulation skipped.");
        }

    } catch (error) {
        console.error("Error during execution:", error);
    } finally {
        // নির্দিষ্ট সময় পর কাজ শেষ করে ফাইল জেনারেট করা এবং প্রসেস ফিনিশ করা নিশ্চিত করা
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
        console.log("Successfully saved output to status.txt. Closing browser...");

        await browser.close();
        
        // গিটহাব অ্যাকশন্স যাতে প্রসেস আটকে না থাকে সেজন্য জোরপূর্বক এক্সিট নিশ্চিত করা
        process.exit(0);
    }
}

captureStreamingLinks();
