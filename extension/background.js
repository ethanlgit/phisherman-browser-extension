// Runs in the extension's own context, which (via host_permissions for
// 127.0.0.1:5000) is allowed to reach the local backend even when the page
// itself is blocked from doing so by the browser's Local Network Access rules.
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message && message.type === "checkLink") {
        fetch("http://127.0.0.1:5000/predict", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({url: message.url}),
        })
        .then(response => response.json())
        .then(data => sendResponse({ok: true, data}))
        .catch(err => sendResponse({ok: false, error: String(err)}));

        return true; // keep the channel open for the async sendResponse
    }
});
