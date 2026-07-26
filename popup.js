document.addEventListener('DOMContentLoaded', async () => {
    try {
        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
        
        if (!tab) {
             showError("Could not detect active tab.");
             return;
        }

        const isAmazon = tab.url && (tab.url.includes('amazon.com') || tab.url.includes('amazon.in') || tab.url.includes('amazon.co.uk') || tab.url.includes('amazon.ca'));
        
        if (!isAmazon) {
            showError("Please open an Amazon product page to use OmniPrice.");
            return;
        }

        requestProductInfo(tab);
    } catch (e) {
        showError("An error occurred while initializing. Please try again.");
    }
});

async function requestProductInfo(tab) {
    try {
        const response = await chrome.tabs.sendMessage(tab.id, { action: "getProductInfo" });
        handleProductResponse(response);
    } catch (e) {
        // Content script might not be injected yet
        try {
            await chrome.scripting.executeScript({
                target: { tabId: tab.id },
                files: ['content.js']
            });
            const response = await chrome.tabs.sendMessage(tab.id, { action: "getProductInfo" });
            handleProductResponse(response);
        } catch (injectError) {
            showError("Could not analyze this page. Please refresh the Amazon page and try again.");
        }
    }
}

function handleProductResponse(response) {
    if (response && response.title) {
        renderProductInfo(response);
        fetchPrices(response.title);
    } else {
        showError("Could not find product details on this page. Are you on a product detail page?");
    }
}

function showError(msg) {
    document.getElementById('loader').style.display = 'none';
    document.getElementById('product-view').style.display = 'none';
    document.getElementById('error-view').style.display = 'flex';
    document.getElementById('error-text').innerText = msg;
}

function renderProductInfo(info) {
    document.getElementById('loader').style.display = 'none';
    document.getElementById('error-view').style.display = 'none';
    document.getElementById('product-view').style.display = 'block';
    
    document.getElementById('product-title').innerText = info.title;
    document.getElementById('amazon-price').innerText = info.price || "Price not found";
    
    if (info.image && info.image !== "") {
        document.getElementById('product-image').src = info.image;
    }
}

// Helper to clean title
function cleanTitle(title) {
    // Remove stuff after a comma, pipe, dash, or parenthesis to make search more generic
    let cleaned = title.split(',')[0].split('|')[0].split('-')[0].split('(')[0].trim();
    // take first 5-6 words max for better search results
    let words = cleaned.split(' ');
    return words.slice(0, Math.min(6, words.length)).join(' ');
}

function fetchPrices(rawTitle) {
    const searchTitle = cleanTitle(rawTitle);
    const storeList = document.getElementById('store-list');
    storeList.innerHTML = ''; // prevent duplicates if called twice
    
    const stores = [
        { id: 'ebay', name: 'eBay', class: 'store-ebay', letter: 'e' },
        { id: 'walmart', name: 'Walmart', class: 'store-walmart', letter: 'W' },
        { id: 'bestbuy', name: 'Best Buy', class: 'store-bestbuy', letter: 'B' }
    ];

    stores.forEach(store => {
        const item = document.createElement('a');
        item.className = 'store-item';
        item.target = '_blank';
        // Add a placeholder loading state
        item.innerHTML = `
            <div class="store-brand">
                <div class="store-logo ${store.class}">${store.letter}</div>
                <div class="store-name">${store.name}</div>
            </div>
            <div class="store-price loading" id="price-${store.id}"></div>
        `;
        storeList.appendChild(item);
    });

    // Fetch eBay from Background Script
    chrome.runtime.sendMessage({ action: "fetchEbayPrice", query: searchTitle }, (response) => {
        const priceEl = document.getElementById('price-ebay');
        if(!priceEl) return;
        
        priceEl.classList.remove('loading');
        if (response && response.price) {
            priceEl.innerText = response.price;
            priceEl.parentElement.href = response.url;
        } else {
            priceEl.innerText = "Search";
            priceEl.classList.add('view-btn');
            priceEl.parentElement.href = response ? response.url : `https://www.ebay.com/sch/i.html?_nkw=${encodeURIComponent(searchTitle)}`;
        }
    });

    // Walmart and BestBuy 
    // They strongly block automated browser-less fetches. We'll simulate checking and provide the direct search link
    setTimeout(() => {
        const wmPrice = document.getElementById('price-walmart');
        if(wmPrice) {
            wmPrice.classList.remove('loading');
            wmPrice.innerText = "Check";
            wmPrice.classList.add('view-btn');
            wmPrice.parentElement.href = `https://www.walmart.com/search?q=${encodeURIComponent(searchTitle)}`;
        }

        const bbPrice = document.getElementById('price-bestbuy');
        if(bbPrice) {
            bbPrice.classList.remove('loading');
            bbPrice.innerText = "Check";
            bbPrice.classList.add('view-btn');
            bbPrice.parentElement.href = `https://www.bestbuy.com/site/searchpage.jsp?st=${encodeURIComponent(searchTitle)}`;
        }
    }, 800); // 800ms gives a nice natural feeling before the buttons appear
}
