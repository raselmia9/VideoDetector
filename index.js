const puppeteer = require('puppeteer');
const fs = require('fs');

async function captureStreamingLinks() {
    console.log("Launching stealth browser...");
    
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
    await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36');

    await page.evaluateOnNewDocument(() => {
        Object.defineProperty(navigator, 'webdriver', {
            get: () => false,
        });
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5],
        });
        window.navigator.chrome = {
            runtime: {},
        };
    });

    // লিংক এবং তার নিজস্ব রেফারার ট্র্যাক করার জন্য Map ব্যবহার করা হলো
    const capturedLinksMap = new Map();
    const targetPageUrl = 'https://dlive.sx/watch.php?id=450';

    page.on('request', (request) => {
        const url = request.url();
        if (url.includes('.m3u8') || url.includes('playlist') || url.includes('manifest')) {
            // রিকোয়েস্ট থেকে আসল রেফারার হেডার বের করা, না থাকলে মূল পেজটি দেওয়া
            const headers = request.headers();
            const referer = headers['referer'] || targetPageUrl;

            if (!capturedLinksMap.has(url)) {
                console.log(`[Captured Link]: ${url} | Referer: ${referer}`);
                capturedLinksMap.set(url, referer);
            }
        }
    });

    try {
        console.log("Navigating to target page securely...");
        await page.goto(targetPageUrl, {
            waitUntil: 'domcontentloaded',
            timeout: 45000
        });

        console.log("Waiting for player to trigger requests...");
        await new Promise(resolve => setTimeout(resolve, 6000));

        try {
            await page.mouse.click(500, 500);
            console.log("Simulated human click on page.");
            await new Promise(resolve => setTimeout(resolve, 4000));
        } catch (e) {
            console.log("Click simulation skipped.");
        }

    } catch (error) {
        console.error("Error during navigation:", error);
    } finally {
        let fileContent = `--- DLive Link Capture Status ---\n`;
        fileContent += `Target URL: ${targetPageUrl}\n`;
        fileContent += `Capture Time: ${new Date().toLocaleString()}\n`;
        fileContent += `Total Links Found: ${capturedLinksMap.size}\n\n`;
        fileContent += `--- Streaming Links with Dynamic Referer ---\n`;

        if (capturedLinksMap.size > 0) {
            let index = 1;
            for (let [link, referer] of capturedLinksMap.entries()) {
                // প্রতিটি লিংকের সাথে তার নিজস্ব সঠিক রেফারার যুক্ত হবে
                fileContent += `${index}. ${link}|Referer=${referer}\n`;
                index++;
            }
        } else {
            fileContent += `No streaming links captured.\n`;
        }

        fs.writeFileSync('status.txt', fileContent, 'utf-8');
        console.log("Successfully saved output to status.txt");

        await browser.close();
        console.log("Browser closed successfully.");
    }
}

captureStreamingLinks();
