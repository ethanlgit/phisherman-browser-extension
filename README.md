# Phisherman

**Real-time phishing and malicious-link detection, right from your browser.**

Phisherman is a browser extension backed by a machine-learning model that classifies any link on a web page the moment you hover over it. Instead of clicking blindly, you get an instant verdict — **benign, phishing, malware, or defacement** — along with a confidence score, shown in a small tooltip next to your cursor.

---

## Features

- **Hover-to-check** — Move your mouse over any `<a>` link and a tooltip appears with the model's prediction. No clicking required.
- **Multi-class classification** — Every URL is scored as one of four classes: `benign`, `phishing`, `malware`, or `defacement`.
- **Confidence graph** — The tooltip renders a small colour-coded bar chart of the model's probability for all four classes, with the predicted class highlighted.
- **Machine-learning powered** — An XGBoost model trained on ~650,000 labeled URLs, tuned with cross-validated grid search.
- **15 engineered URL features** — Lexical and structural signals extracted from each URL (see below), with no page content or network calls to the target site required.
- **Top-domain awareness** — Cross-references a top-1M domain list to recognize well-known, legitimate sites.
- **Runs locally** — The backend runs on your own machine (`127.0.0.1:5000`); URLs are never sent to a third-party service.

---

## Architecture

```
┌──────────────────┐  msg  ┌──────────────────┐   POST /predict    ┌──────────────────┐
│  content.js      │ ────> │  background.js   │ ─────────────────> │  Flask Backend   │
│  (injected page) │       │  (service worker)│  {"url":"http://…"} │  (app.py)        │
│                  │ <──── │                  │ <───────────────── │                  │
│ • hover listener │ result│ • fetch to local │  {class, score,    │ • feature extract│
│ • tooltip + graph│       │   backend        │   all_scores}      │ • XGBoost model  │
└──────────────────┘       └──────────────────┘                    └──────────────────┘
```

The content script sends the hovered URL to the extension's background service worker, which makes the actual request to the backend. This indirection is deliberate: browsers block a normal web page from reaching a `localhost` address (Local/Private Network Access), but the extension's own context is permitted to.

The project has two halves:

### 1. Browser Extension (`extension/`)
A Manifest V3 Chrome/Edge extension named **Phisherman**.

| File | Role |
|------|------|
| `manifest.json` | MV3 config — content script injection, background service worker, host permissions for the local backend, `activeTab` permission. |
| `content.js` | Injected into every page. Listens for `mouseover` on links, positions the tooltip, and asks the background worker to check the URL, then renders the confidence graph. |
| `background.js` | Service worker that performs the `fetch` to the backend on the content script's behalf (so the request isn't blocked as a page-to-localhost call). |
| `tooltip.css` | Styling for the floating tooltip and its bar chart. |

### 2. Backend and ML Model (`backend/`)
A Flask API that loads the trained model and serves predictions.

| File | Role |
|------|------|
| `app.py` | Flask app with CORS enabled. Exposes `/predict` and `/check_link` (both return the predicted class, score, and full probability distribution). Loads the pickled XGBoost model at startup. |
| `model/extract_features.py` | The feature-engineering pipeline — URL parsing, IPv6 normalization, feature computation, and top-domain lookup. |
| `model/model.ipynb` | Notebook where the model was trained and evaluated (XGBoost with `GridSearchCV` hyperparameter tuning using an F1 scorer). |
| `model/xgb_model.pkl` | The serialized, trained XGBoost classifier. |
| `model/datasets/phish_data.csv` | ~651K labeled URLs used for training. |
| `model/datasets/top-1m.csv` | Top 1,000,000 domains for the known-good reference set. |

---

## How the model decides

For each URL, `extract_features.py` computes 15 features that the model uses to make its prediction:

**Structural / lexical**
- `url_length`, `hostname_length`, `path_length`, `path_depth`
- `num_dots`, `num_hyphens`, `num_digits`, `num_subdomains`
- `has_query` — whether the URL carries query parameters

**Suspicion signals**
- `has_suspicious_keywords` — hostname contains words like `login`, `secure`, `verify`, `paypal`, `bank`, `confirm`, and similar
- `has_suspicious_tlds` — TLDs frequently abused by phishers (`.tk`, `.xyz`, `.zip`, `.top`, `.gq`, and others)
- `has_ip` — hostname is a raw IP address instead of a domain
- `has_executable_ext` — path ends in a risky extension (`.exe`, `.scr`, `.js`, `.zip`, and others)
- `has_double_extension` — disguised executables (e.g. `invoice.pdf.exe`)

**Reputation**
- `common_domain` — the hostname matches an entry in the top-1M list

Robust URL handling is built in: missing schemes are added, malformed or bracketless IPv6 addresses are normalized, and unparseable URLs fall back to a zeroed feature vector.

---

## Getting Started

### Prerequisites
- Python 3.x
- Google Chrome (or any Chromium-based browser)

### 1. Set up the backend

```powershell
# From the project root, create and activate a virtual environment
python -m venv venv
venv\Scripts\Activate.ps1        # PowerShell
# or: venv\Scripts\activate.bat  # Command Prompt

# Install dependencies
pip install -r backend/requirements.txt

# Run the API (must be run from the backend/ directory)
cd backend
python app.py
```

The server starts on `http://127.0.0.1:5000`.

> **VS Code tip:** Open the Command Palette (`Ctrl+Shift+P`), choose **Python: Select Interpreter**, and select the interpreter inside your `venv` (e.g. `.\venv\Scripts\python.exe`).

### 2. Load the extension

1. Go to `chrome://extensions` in your browser.
2. Enable **Developer mode** (top-right toggle).
3. Click **Load unpacked** and select the `extension/` folder.
4. With the backend running, hover over any link on any page — the tooltip will show the verdict.

---

## API Reference

### `POST /predict`
Classify a URL. Accepts the URL as a JSON body (`POST`) or a `?url=` query parameter (`GET`).

**Request**
```json
{ "url": "http://example-login-verify.tk/account" }
```

**Response**
```json
{
  "class": "phishing",
  "score": 0.9234,
  "all_scores": {
    "benign": 0.0412,
    "defacement": 0.0009,
    "malware": 0.0345,
    "phishing": 0.9234
  }
}
```

### `GET/POST /check_link`
Same input and output shape as `/predict` — an alternate endpoint returning the predicted class, score, and per-class probabilities.

---

## Tech Stack

- **Frontend:** JavaScript, Chrome Extension APIs (Manifest V3)
- **Backend:** Python, Flask, Flask-CORS
- **ML:** XGBoost, scikit-learn, pandas, NumPy
- **Data:** ~651K labeled phishing/benign/malware/defacement URLs, plus a top-1M domain list

---

## Notes and Limitations

- The extension talks to a **local** backend, so the Flask server must be running for predictions to work.
- Predictions are based purely on the **URL string** — no page content is fetched, which keeps it fast and private, but means visual or content-based phishing cues are not considered.
- This is a learning and research project and should be treated as an assistive signal, not a guarantee of a site's safety.
- **Known behaviour:** the model scores ~94% on its own dataset, but tends to flag many *normal, popular* websites as phishing. This is a data-representativeness issue, not a bug — see Future Improvements below.

---

## Future Improvements

The biggest limitation is the **training data**, not the code. The model reaches ~94% accuracy on its dataset, but the dataset's "benign" examples are mostly obscure deep links (e.g. `mp3raid.com/music/...`) with almost no mainstream websites. As a result the model never learned that popular, well-known sites are safe, so it over-predicts phishing on everyday browsing.

Highest-impact fixes first:

1. **Add real, popular sites to the benign class.** Mix a large sample of the existing `top-1m.csv` domains (labelled `benign`) into training so the model learns what normal websites look like. This is the single most impactful change.
2. **Make `common_domain` a useful signal.** It is currently an *exact* hostname match against the top-1M list, so `mail.google.com`, `youtube.com/watch?...`, etc. miss. Switch it to suffix matching (the codebase already has `is_top_domain()` for this) — and, combined with (1), the model will finally learn "known domain → likely safe."
3. **Address class imbalance.** Benign is ~66% of the data and malware only ~5%; consider class weighting or resampling to improve minority-class recall (phishing recall is currently ~0.76).
4. **Richer features beyond the URL string.** Domain age / WHOIS, TLS certificate info, DNS/hosting reputation, redirect chains, and (optionally) page-content signals would raise the ceiling on URLs that look lexically normal.
5. **Fresher, more diverse data.** Fold in current feeds (e.g. URLhaus, PhishTank) so the model generalises to live, real-world malicious URLs rather than a single older dataset.
6. **Model hygiene.** Re-save the model with XGBoost's native `Booster.save_model()` (avoids the pickle version warning), and add probability calibration / confidence thresholds instead of always taking the top class.
7. **UX polish.** Clamp the tooltip so it stays on-screen near window edges, and optionally let the popup surface a short "why" (the top contributing features) for each verdict.
