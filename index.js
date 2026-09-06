const puppeteer = require('puppeteer');
const fs = require('fs');

async function captureStreamingLinks() {
    console.log("Launching stealth browser...");
    
    // বট ডিটেকশন এড়ানোর জন্য ব্রাউজার আর্গুমেন্ট
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
            '--lang=en-US,en;q=0.9',
            // সবচেয়ে গুরুত্বপূর্ণ: অটোমেশন ফ্ল্যাগ হাইড করার জন্য
            '--disable-blink-features=AutomationControlled'
        ]
    });

    const page = await browser.newPage();

    // ভিউপোর্ট সেট করা যেন রিয়েল ডিভাইসের মতো দেখায়
    await page.setViewport({ width: 1920, height: 1080 });

    // রিয়েল ইউজারের মতো ইউজার-এজেন্ট (User-Agent) সেট করা
    await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36');

    // অতিরিক্ত বট ডিটেকশন প্রপার্টি ওভাররাইড করা
    await page.evaluateOnNewDocument(() => {
        // navigator.webdriver ট্রু থাকলে বট বুঝে যায়, তাই এটিকে ফলস বা আনডিফাইন্ড করা
        Object.defineProperty(navigator, 'webdriver', {
            get: () => false,
        });

        // ব্রাউজারের প্লাগইন মক করা
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5],
        });

        // ভাষা বা প্ল্যাটফর্ম রিয়েল ইউজারের মতো সেট করা
        window.navigator.chrome = {
            runtime: {},
        };
    });

    const capturedLinks = new Set();

    // নেটওয়ার্ক রিকোয়েস্ট ইন্টারসেপ্ট করার জন্য
    page.on('request', (request) => {
        const url = request.url();
        if (url.includes('.m3u8') || url.includes('playlist') || url.includes('manifest')) {
            if (!capturedLinks.has(url)) {
                console.log(`[Captured Link]: ${url}`);
                capturedLinks.add(url);
            }
        }
    });

    try {
        console.log("Navigating to target page securely...");
        await page.goto('https://dlive.sx/watch.php?id=450', {
            waitUntil: 'networkidle2',
            timeout: 60000
        });

        console.log("Waiting for page stability and player trigger...");
        await new Promise(resolve => setTimeout(resolve, 10000));

        // রিয়েল ইউজারের মতো পেজে ক্লিক বা স্ক্রোল সিমুলেট করা
        try {
            await page.mouse.click(500, 500); // পেজের মাঝে একটি ক্লিক করা
            console.log("Simulated human click on page.");
            await new Promise(resolve => setTimeout(resolve, 5000));
        } catch (e) {
            console.log("Click simulation skipped.");
        }

    } catch (error) {
        console.error("Error during navigation:", error);
    } finally {
        await browser.close();
        console.log("Browser closed.");

        // status.txt ফাইলে আউটপুট সেভ করা
        let fileContent = `--- DLive Link Capture Status (Anti-Bot Bypass) ---\n`;
        fileContent += `Target URL: https://dlive.sx/watch.php?id=450\n`;
        fileContent += `Capture Time: ${new Date().toLocaleString()}\n`;
        fileContent += `Total Links Found: ${capturedLinks.size}\n\n`;
        fileContent += `--- Streaming Links ---\n`;

        if (capturedLinks.size > 0) {
            let index = 1;
            for (let link of capturedLinks) {
                fileContent += `${index}. ${link}\n`;
                index++;
            }
        } else {
            fileContent += `No streaming links captured. Site might be blocking GitHub Actions IP.\n`;
        }

        fs.writeFileSync('status.txt', fileContent, 'utf-8');
        console.log("Successfully saved output to status.txt");
    }
}

captureStreamingLinks();
