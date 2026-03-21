# ◈ FLIP.TC — Torn City Market Analyzer

A dark, fast, browser-based flipping tool for [Torn City](https://www.torn.com).
Analyze item market listings, detect undercut opportunities, estimate profit after the 5% market tax, and track multiple items with auto-refresh.

![Screenshot placeholder](docs/screenshot.png)
> _Screenshot will appear here once the app is running_

---

## Features

| Feature | Details |
|---------|---------|
| **API Key Vault** | Paste your Torn API key once — stored in `localStorage`, never sent anywhere except `api.torn.com` |
| **Item Search** | Search any item by ID or pick from popular flip targets |
| **Flip Analysis** | Detects lowest price, 2nd/3rd price levels, undercut spreads |
| **Profit Calculator** | Input quantity → gross revenue, 5% tax, net profit, ROI% |
| **Watchlist** | Save items; each refreshes automatically every **60 seconds** |
| **Dark UI** | Crime-city aesthetic: black/dark-gray with neon green & gold accents |
| **Mobile Responsive** | Works on phones and tablets |

---

## Tech Stack

- [React 19](https://react.dev/) + [Vite](https://vitejs.dev/)
- [Tailwind CSS v3](https://tailwindcss.com/)
- JetBrains Mono (Google Fonts)
- No extra runtime dependencies

---

## Setup

### Prerequisites

- Node.js >= 18
- A Torn City account with an API key

### 1. Clone & Install

```bash
git clone https://github.com/YOUR_USERNAME/torn-flip-tracker.git
cd torn-flip-tracker
npm install
```

### 2. Start Dev Server

```bash
npm run dev
```

Open http://localhost:5173 in your browser.

### 3. Build for Production

```bash
npm run build
# Preview the build locally:
npm run preview
```

The `dist/` folder can be deployed to any static host (Vercel, Netlify, GitHub Pages, Cloudflare Pages, etc.).

---

## Getting a Torn API Key

1. Log in to torn.com
2. Go to **Preferences -> API** or visit torn.com/preferences.php#tab=api
3. Create a **read-only** key -- the app only needs `user` + `market` selections
4. Paste the key into the app's API Key field

> Your key is stored only in your browser's `localStorage`. It never touches any server other than `api.torn.com`.

---

## How Flip Detection Works

```
lowestPrice   = cheapest listing on the market
secondPrice   = next distinct price tier above lowest
netSell       = floor(secondPrice x 0.95)   <- after 5% market tax
profitPerUnit = netSell - lowestPrice
marginPct     = (profitPerUnit / lowestPrice) x 100
```

**Strategy:** buy everything at `lowestPrice`, list just below `secondPrice`.
The app highlights listings marked **BUY** (buy target) and **FLIP** (sell target).

---

## Project Structure

```
src/
├── components/
│   ├── ApiKeyInput.jsx     # API key form + validated status
│   ├── FlipSummary.jsx     # Flip analysis stat boxes
│   ├── Header.jsx          # Sticky nav / tab bar
│   ├── ItemSearch.jsx      # Item ID search + quick picks
│   ├── ListingsTable.jsx   # Full market listings table
│   ├── ProfitEstimator.jsx # Quantity x price estimator
│   └── Watchlist.jsx       # Auto-refreshing watchlist
├── hooks/
│   ├── useApiKey.js        # Key storage + Torn API validation
│   ├── useMarketData.js    # Fetch & normalize market listings
│   └── useWatchlist.js     # localStorage-backed watchlist state
├── utils/
│   └── calculations.js     # analyzeFlip(), calcProfit(), formatMoney()
├── App.jsx
├── main.jsx
└── index.css               # Tailwind + custom component classes
```

---

## License

MIT -- do whatever you want, but be kind to the Torn API rate limits.
