const puppeteer = require('puppeteer');
const fs = require('fs');

async function captureStreamingLinks() {
    console.log("Starting lightweight stealth capture...");
    
    const browser = await puppeteer.launch({
        headless: "new",
        args: [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-infobars',
            '--window-size=1280,720',
            '--disable-dev-shm-usage',
            '--disable-gpu',
            '--single-process',
            '--disable-blink-features=AutomationControlled'
        ]
    });

    const page = await browser.newPage();
    await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36');

    const capturedLinksMap = new Map();
    const targetPageUrl = 'https://dlive.sx/watch.php?id=450';

    // নেটওয়ার্ক রিকোয়েস্ট মনিটর করা
    page.on('request', (request) => {
        const url = request.url();
        // ভিডিও স্ট্রিম বা ম্যানিফেস্ট ফাইল ফিল্টার করা
        if (url.includes('.m3u8') || url.includes('playlist') || url.includes('index.m3u8')) {
            const headers = request.headers();
            const referer = headers['referer'] || targetPageUrl;

            if (!capturedLinksMap.has(url)) {
                console.log(`[Captured]: ${url}`);
                capturedLinksMap.set(url, referer);
            }
        }
    });

    try {
        console.log("Navigating to page...");
        await page.goto(targetPageUrl, {
            waitUntil: 'domcontentloaded',
            timeout: 30000
        });

        // ভিডিও লোড হওয়ার জন্য সর্বোচ্চ ১৫ সেকেন্ড অপেক্ষা
        console.log("Waiting for video stream requests...");
        await new Promise(resolve => setTimeout(resolve, 15000));

        // প্লেয়ারে ক্লিক সিমুলেট করা
        try {
            await page.mouse.click(640, 360);
            console.log("Clicked on player.");
            await new Promise(resolve => setTimeout(resolve, 8000));
        } catch (e) {
            console.log("Click skipped.");
        }

    } catch (error) {
        console.error("Navigation error:", error);
    } finally {
        // নিশ্চিতভাবে status.txt ফাইল তৈরি করা
        let fileContent = `--- DLive Link Capture Status ---\n`;
        fileContent += `Target URL: ${targetPageUrl}\n`;
        fileContent += `Capture Time: ${new Date().toLocaleString()}\n`;
        fileContent += `Total Links Found: ${capturedLinksMap.size}\n\n`;
        fileContent += `--- Streaming Links with Referer ---\n`;

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
        console.log("status.txt generated successfully.");

        await browser.close();
    }
}

// স্ক্রিপ্ট রান করে নির্দিষ্ট সময়ে ফোর্স এক্সিট নিশ্চিত করা
captureStreamingLinks().then(() => {
    console.log("Process completed successfully.");
    process.exit(0);
}).catch((err) => {
    console.error("Fatal error:", err);
    process.exit(1);
});
