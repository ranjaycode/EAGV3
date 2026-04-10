chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "getProductInfo") {
        const titleEl = document.getElementById('productTitle');
        let priceEl = document.querySelector('.a-price .a-offscreen') 
            || document.querySelector('#priceblock_ourprice') 
            || document.querySelector('#priceblock_dealprice')
            || document.querySelector('.a-color-price');
            
        const imgEl = document.getElementById('landingImage') || document.querySelector('#imgTagWrapperId img');

        if (titleEl) {
            sendResponse({
                title: titleEl.innerText.trim(),
                price: priceEl ? priceEl.innerText.trim() : null,
                image: imgEl ? imgEl.src : null
            });
        } else {
            sendResponse(null);
        }
    }
});
