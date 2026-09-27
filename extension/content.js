// console.log("Content script loaded - debug version");

// // Test 1: Basic DOM manipulation
// try {
//     const testDiv = document.createElement("div");
//     testDiv.textContent = "Extension working!";
//     testDiv.style.position = "fixed";
//     testDiv.style.top = "10px";
//     testDiv.style.right = "10px";
//     testDiv.style.backgroundColor = "green";
//     testDiv.style.color = "white";
//     testDiv.style.padding = "10px";
//     testDiv.style.zIndex = "99999";
//     document.body.appendChild(testDiv);
//     console.log("DOM manipulation works");
// } catch (error) {
//     console.error("DOM manipulation failed:", error);
// }

// // Test 2: Event listeners
// document.addEventListener("click", function(event) {
//     console.log("Click detected on:", event.target);

//     // Test if we can find links
//     const link = event.target.closest ? event.target.closest("a") : null;
//     if (link) {
//         console.log("Found link:", link.href);

//         // Test 3: Basic fetch (comment out if needed)
//         console.log("Attempting fetch...");
//         fetch("http://127.0.0.1:5000/predict", {
//             method: "POST",
//             headers: {"Content-Type": "application/json"},
//             body: JSON.stringify({url: link.href})
//         })
//         .then(response => {
//             console.log("Fetch response status:", response.status);
//             return response.json();
//         })
//         .then(data => {
//             console.log("Fetch successful:", data);
//             alert(`Link check result: ${data.class}`);
//         })
//         .catch(error => {
//             console.error("Fetch failed:", error);
//             alert(`Fetch error: ${error.message}`);
//         });
//     }
// });

// // Test 4: Check if backend is reachable
// setTimeout(() => {
//     console.log("Testing backend connectivity...");
//     fetch("http://127.0.0.1:5000/predict", {
//         method: "GET"
//     })
//     .then(response => response.json())
//     .then(data => console.log("Backend test successful:", data))
//     .catch(error => console.error("Backend test failed:", error));
// }, 2000);

console.log("Content script loaded.");

var tooltip = document.createElement("div");
tooltip.id = "phisherman-tooltip";
document.body.appendChild(tooltip);

// --- graph helpers (added) ---
const CLASS_COLORS = {
    benign: "#0ca30c",
    phishing: "#d03b3b",
    malware: "#ec835a",
    defacement: "#fab219"
};
const CLASS_ORDER = ["benign", "phishing", "malware", "defacement"];

// Draws a small bar-chart of the per-class probabilities into the tooltip.
function renderGraph(data) {
    const scores = data.all_scores || {};
    tooltip.textContent = "";

    const header = document.createElement("div");
    header.className = "tt-header";
    header.textContent = `${data.class} — ${(data.score * 100).toFixed(2)}%`;
    header.style.color = CLASS_COLORS[data.class] || "#fff";
    tooltip.appendChild(header);

    CLASS_ORDER.forEach((cls) => {
        if (!(cls in scores)) return;
        const row = document.createElement("div");
        row.className = "tt-row" + (cls === data.class ? " tt-row-top" : "");

        const name = document.createElement("span");
        name.className = "tt-name";
        name.textContent = cls;

        const track = document.createElement("div");
        track.className = "tt-track";
        const bar = document.createElement("div");
        bar.className = "tt-bar";
        bar.style.width = Math.max(2, scores[cls] * 100) + "%";
        bar.style.backgroundColor = CLASS_COLORS[cls] || "#888";
        track.appendChild(bar);

        const val = document.createElement("span");
        val.className = "tt-val";
        val.textContent = (scores[cls] * 100).toFixed(0) + "%";

        row.appendChild(name);
        row.appendChild(track);
        row.appendChild(val);
        tooltip.appendChild(row);
    });
}
// --- end graph helpers ---

document.addEventListener("mouseover", (event) => {
    var link = event.target.closest("a");
    if (!link || !link.href) return;

    const linkLength = link.textContent.trim().length;
    if (linkLength === 0) return;

    // const container = link.closest("p, article, .post, .comment");
    // if (!container) return;

    const rect = link.getBoundingClientRect();
    if (rect.width === 0 || rect.height === 0) return;

    const role = link.getAttribute("role");
    const className = link.className.toLowerCase();
    const computed = window.getComputedStyle(link);
    const isTransparent = computed.backgroundColor === "rgba(0, 0, 0, 0)" || computed.backgroundColor === "transparent";

    const isButtonLike = role === "button" || className.includes("btn") || (computed.cursor === "pointer" && isTransparent);

    //console.log("yeerrrr")

    //if (isButtonLike) return;

    const display = window.getComputedStyle(link).display;
    const isInLine = display === "inline" || display === "inline-block";

    //console.log("yayaya")

    // if (isInLine) {

    tooltip.textContent = "Checking link for safety...";
    // Sit at the bottom-right of the cursor (offset right and down).
    tooltip.style.left = (event.clientX + 14) + "px";
    tooltip.style.top = (event.clientY + 16) + "px";
    tooltip.style.opacity = "1";
    const url = link.href;

    // If the extension was reloaded, this stale content script loses its link
    // to chrome.runtime. Bail out quietly instead of throwing (refresh the page
    // to get a working script again).
    if (typeof chrome === "undefined" || !chrome.runtime || !chrome.runtime.id) {
        tooltip.textContent = "Reload this page (extension was updated).";
        return;
    }

    // The fetch runs in background.js (the extension context) so the browser
    // doesn't block it as a page-to-localhost request.
    chrome.runtime.sendMessage({type: "checkLink", url}, (response) => {
        if (chrome.runtime.lastError) {
            console.log("Error:", chrome.runtime.lastError.message);
            return;
        }
        if (response && response.ok) {
            console.log("Prediction:", response.data);
            renderGraph(response.data);
        } else {
            console.log("Error:", response && response.error);
        }
    });

        // console.log("Link found.");
        // // tooltip.textContent = "Checking link for safety...";

    //}

    // if (link && link.href) {
    //     const isWordLink = link.textContent.trim().length > 0 && link.children.length === 0;

    //     if (isWordLink) {
    //         console.log("Link found.");
    //         tooltip.textContent = "Checking link for safety...";
    //         tooltip.style.left = event.clientX + "px";
    //         tooltip.style.top = (event.clientY - 50) + "px";
    //         tooltip.style.opacity = "1";
    //     }
    // }
})

document.addEventListener("mouseout", (event) => {
    const link = event.target.closest("a");
    if (!link) {
        tooltip.style.opacity = "0";
    }
})
