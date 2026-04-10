// background.js (Service Worker)

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "fetchEbayPrice") {
        const query = encodeURIComponent(request.query);
        const url = `https://www.ebay.com/sch/i.html?_nkw=${query}`;
        
        fetch(url, {
            headers: {
                // Emulate a standard browser request format
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
        })
            .then(res => res.text())
            .then(html => {
                // simple regex to find the first price.
                // eBay typically uses <span class="s-item__price">$1,299.00</span>
                const priceMatch = html.match(/<span class="s-item__price"[^>]*>([^<]+)<\/span>/);
                if (priceMatch && priceMatch[1] && !priceMatch[1].toLowerCase().includes("to")) {
                    // It found a direct price (not a range like "$10 to $20")
                    sendResponse({ price: priceMatch[1], url: url });
                } else {
                    sendResponse({ price: null, url: url });
                }
            })
            .catch(err => {
                console.error("OmniPrice Background Fetch Error:", err);
                sendResponse({ price: null, url: url });
            });
            
        // Return true to indicate we will send the response asynchronously
        return true;
    }
});
