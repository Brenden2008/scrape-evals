const puppeteer = require('puppeteer');

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

async function main() {
    const url = process.argv[2];
    const actionsB64 = process.argv[3] || null;
    let actions = [];
    if (actionsB64) {
        try {
            const json = Buffer.from(actionsB64, 'base64').toString('utf8');
            actions = JSON.parse(json);
        } catch (e) {
            // ignore, keep actions empty
        }
    }
    if (!url) {
        console.error(JSON.stringify({ error: "No URL provided" }));
        process.exit(1);
    }
    let browser;
    try {
        const headful = process.env.PUPPETEER_HEADFUL === '1' || process.env.PUPPETEER_HEADFUL === 'true';
        browser = await puppeteer.launch({ headless: !headful, devtools: headful, args: headful ? [] : undefined });
        const page = await browser.newPage();
        const response = await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30000 });
        const status = response ? response.status() : null;
        // Execute actions sequentially
        if (Array.isArray(actions) && actions.length > 0) {
            for (const a of actions) {
                const t = a && a.type;
                try {
                    if (t === 'click' && a.selector) {
                        await page.click(a.selector, { timeout: 5000 });
                        await sleep(800);
                    } else if (t === 'scroll') {
                        const sel = a.selector;
                        if (sel) {
                            try { await page.waitForSelector(sel, { timeout: 5000 }); } catch {}
                            // Ensure events route to the element/container
                            try { await page.hover(sel); } catch {}
                            try { await page.focus(sel); } catch {}
                            // Scroll the nearest scrollable container of the element
                            for (let i = 0; i < 240; i++) {
                                const endReached = await page.evaluate((selector) => {
                                    const el = document.querySelector(selector);
                                    if (!el) return true;
                                    function getScrollParent(node) {
                                        let p = node;
                                        while (p && p.parentElement) {
                                            p = p.parentElement;
                                            const style = getComputedStyle(p);
                                            const oy = style.overflowY;
                                            if ((oy === 'auto' || oy === 'scroll') && p.scrollHeight > p.clientHeight) return p;
                                        }
                                        return document.scrollingElement || document.documentElement;
                                    }
                                    const container = getScrollParent(el);
                                    const maxTop = Math.max(0, container.scrollHeight - container.clientHeight);
                                    const stepBy = Math.max(Math.floor(container.clientHeight * 0.95), 800);
                                    const before = container.scrollTop;
                                    if (typeof container.scrollTo === 'function') {
                                        container.scrollTo({ top: Math.min(container.scrollTop + stepBy, maxTop), left: 0, behavior: 'instant' });
                                    } else {
                                        container.scrollTop = Math.min(container.scrollTop + stepBy, maxTop);
                                    }
                                    container.dispatchEvent(new Event('scroll', { bubbles: true }));
                                    el.scrollIntoView({ behavior: 'instant', block: 'end' });
                                    const atEnd = container.scrollTop >= maxTop;
                                    const moved = container.scrollTop !== before;
                                    return atEnd || !moved;
                                }, sel);
                                await sleep(120);
                                try { await page.mouse.wheel({ deltaY: 1200 }); } catch {}
                                try { await page.keyboard.press('PageDown'); } catch {}
                                if (endReached) break;
                            }
                            // Final force to bottom of the container
                            try {
                                await page.evaluate((selector) => {
                                    const el = document.querySelector(selector);
                                    if (!el) return;
                                    function getScrollParent(node) {
                                        let p = node;
                                        while (p && p.parentElement) {
                                            p = p.parentElement;
                                            const style = getComputedStyle(p);
                                            const oy = style.overflowY;
                                            if ((oy === 'auto' || oy === 'scroll') && p.scrollHeight > p.clientHeight) return p;
                                        }
                                        return document.scrollingElement || document.documentElement;
                                    }
                                    const container = getScrollParent(el);
                                    const maxTop = Math.max(0, container.scrollHeight - container.clientHeight);
                                    if (typeof container.scrollTo === 'function') {
                                        container.scrollTo({ top: maxTop, left: 0, behavior: 'instant' });
                                    } else {
                                        container.scrollTop = maxTop;
                                    }
                                    container.dispatchEvent(new Event('scroll', { bubbles: true }));
                                }, sel);
                                await sleep(200);
                            } catch {}
                        } else {
                            // No selector: no-op to avoid scrolling whole page unintentionally
                            await sleep(200);
                        }
                        await sleep(800);
                    } else if (t === 'wait') {
                        const ms = Number.isFinite(a.milliseconds) ? a.milliseconds : 1000;
                        await sleep(ms);
                    } else if (t === 'write') {
                        const text = typeof a.text === 'string' ? a.text : '';
                        if (a.selector) {
                            try { await page.click(a.selector, { timeout: 5000 }); } catch {}
                            await page.type(a.selector, text, { delay: 0 });
                        } else {
                            await page.keyboard.type(text);
                        }
                    } else if (t === 'press') {
                        const key = a.key || 'Enter';
                        if (a.selector) {
                            try { await page.focus(a.selector); } catch {}
                        }
                        await page.keyboard.press(key);
                    } else if (t === 'executeJavascript') {
                        const script = a.script;
                        if (script) {
                            await page.evaluate(script);
                        }
                    }
                } catch (_) {
                    // ignore per-action errors
                }
            }
            await sleep(600);
        }
        const html = await page.content();
        await browser.close();
        console.log(JSON.stringify({
            status_code: status,
            error: status && status < 400 ? null : `HTTP error: ${status}`,
            html: html,
        }));
    } catch (e) {
        if (browser) await browser.close();
        console.log(JSON.stringify({
            status_code: null,
            error: e.toString(),
            html: null,
        }));
    }
}
main(); 