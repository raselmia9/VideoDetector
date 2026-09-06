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

    const capturedLinks = new Set();

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

        try {
            await page.mouse.click(500, 500);
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
