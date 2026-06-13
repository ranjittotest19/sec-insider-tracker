# SEC Insider Tracker — Complete Build & Deploy Guide

## What You're Deploying

| Layer      | Tech                  | Host    | Cost     |
|------------|-----------------------|---------|----------|
| Database   | PostgreSQL            | Railway | ~$5/mo   |
| Backend    | Python / FastAPI      | Railway | included |
| Frontend   | Next.js               | Vercel  | Free     |
| Data       | SEC EDGAR (public API)| —       | Free     |

**Total: ~$5/month.**

---

## Project Structure

```
sec-insider-tracker/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app entry point
│   │   ├── database.py          # SQLAlchemy DB connection
│   │   ├── models.py            # DB schema (Form4, 13DG, CompanyInfo)
│   │   ├── schemas.py           # Pydantic response models
│   │   ├── scheduler.py         # Background polling (every 15 min)
│   │   ├── api/
│   │   │   ├── form4.py         # /api/form4/* routes
│   │   │   ├── filings_13dg.py  # /api/13dg/* routes
│   │   │   ├── screener.py      # /api/screener/* routes
│   │   │   └── search.py        # /api/search/* routes
│   │   └── services/
│   │       ├── edgar_form4.py   # Form 4 EDGAR ingestion logic
│   │       └── edgar_13dg.py    # 13D/13G EDGAR ingestion logic
│   ├── scripts/
│   │   └── backfill.py          # One-time historical data loader (2020–now)
│   ├── requirements.txt
│   ├── Dockerfile
│   └── railway.toml
└── frontend/
    ├── src/
    │   ├── app/
    │   │   ├── page.tsx               # Live feed (homepage)
    │   │   ├── screener/page.tsx      # Screener with filters
    │   │   ├── 13dg/page.tsx          # 13D/13G feed
    │   │   ├── cluster-buys/page.tsx  # Cluster buy detector
    │   │   ├── company/[ticker]/page.tsx  # Company detail
    │   │   └── insider/[cik]/page.tsx     # Insider profile
    │   ├── components/
    │   │   ├── Navbar.tsx
    │   │   ├── SearchBar.tsx
    │   │   ├── FilterBar.tsx
    │   │   ├── StatsBar.tsx
    │   │   ├── tables/FilingsTable.tsx
    │   │   └── charts/BuySellChart.tsx
    │   └── lib/
    │       ├── api.ts
    │       └── format.ts
    ├── package.json
    ├── tailwind.config.js
    └── vercel.json
```

---

## Step 1 — Prerequisites

Install these on your local machine:
- **Git**: https://git-scm.com
- **Node.js 20+**: https://nodejs.org
- **Python 3.11+**: https://python.org
- **Railway CLI**: `npm install -g @railway/cli`
- **Vercel CLI**: `npm install -g vercel`

---

## Step 2 — One-Time SEC User-Agent Setup

**IMPORTANT**: The SEC requires a User-Agent header identifying your app.
Open these two files and replace `contact@yoursite.com` with your real email:

```
backend/app/services/edgar_form4.py  — line 5 of HEADERS dict
backend/app/services/edgar_13dg.py  — line 5 of HEADERS dict
```

Change:
```python
"User-Agent": "SecInsiderTracker contact@yoursite.com",
```
To:
```python
"User-Agent": "YourAppName your-real@email.com",
```

---

## Step 3 — Set Up GitHub Repo

```bash
cd sec-insider-tracker
git init
git add .
git commit -m "Initial commit"
# Create a new repo at github.com, then:
git remote add origin https://github.com/YOUR_USERNAME/sec-insider-tracker.git
git branch -M main
git push -u origin main
```

---

## Step 4 — Deploy Backend to Railway

### 4a. Create Railway project

1. Go to https://railway.app and sign in (free account)
2. Click **New Project → Deploy from GitHub repo**
3. Select your `sec-insider-tracker` repo
4. When prompted for root directory, type: `backend`

### 4b. Add PostgreSQL

1. Inside your Railway project, click **+ Add Service → Database → PostgreSQL**
2. Railway auto-creates `DATABASE_URL` and injects it into your backend service

### 4c. Verify environment variables

In Railway → your backend service → **Variables**, confirm `DATABASE_URL` exists.
It should look like: `postgresql://postgres:xxxx@monorail.proxy.railway.app:PORT/railway`

### 4d. Deploy

Railway auto-deploys when you push to GitHub. Check **Deployments** tab — the
health check hits `/api/health`. When you see a green checkmark, you're live.

Copy your Railway backend URL — it looks like:
`https://sec-insider-tracker-production.up.railway.app`

---

## Step 5 — Run the Backfill (One-Time, ~4–8 hours)

This populates 5 years of historical data (2020–2025).
Run this from your local machine — it hits EDGAR, not Railway.

```bash
cd backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Set your DATABASE_URL to the Railway PostgreSQL URL:
export DATABASE_URL="postgresql://postgres:xxxx@monorail.proxy.railway.app:PORT/railway"

# Backfill Form 4s (large — run in tmux/screen so it survives disconnects):
python -m scripts.backfill --start 2020 --end 2025 --form 4

# Backfill 13D/13G (faster — fewer filings):
python -m scripts.backfill --start 2020 --end 2025 --form 13dg
```

**Tips for backfill:**
- Run `--form 4` and `--form 13dg` in separate terminal windows simultaneously
- If it stops, rerun — it skips already-ingested accession numbers
- Form 4s: ~300K–500K records total (2020–2025)
- 13D/13G: ~30K–50K records total

---

## Step 6 — Deploy Frontend to Vercel

```bash
cd ../frontend
npm install

# Test locally first:
cp .env.example .env.local
# Edit .env.local and set:
# NEXT_PUBLIC_API_URL=https://your-backend.up.railway.app

npm run dev
# Open http://localhost:3000 — verify data loads

# Deploy to Vercel:
vercel
# Follow prompts: link to your GitHub repo, set framework to Next.js
```

### 6b. Set environment variable in Vercel

1. Go to https://vercel.com → your project → **Settings → Environment Variables**
2. Add: `NEXT_PUBLIC_API_URL` = `https://your-backend.up.railway.app`
3. Redeploy: `vercel --prod`

---

## Step 7 — Verify Everything Works

Test these URLs in your browser:

| What | URL |
|------|-----|
| Backend health | `https://your-backend.up.railway.app/api/health` |
| Form 4 feed | `https://your-backend.up.railway.app/api/form4/feed?days=7` |
| 13D/13G feed | `https://your-backend.up.railway.app/api/13dg/feed?days=30` |
| Search | `https://your-backend.up.railway.app/api/search/?q=AAPL` |
| API docs | `https://your-backend.up.railway.app/docs` |
| Frontend | `https://your-app.vercel.app` |

---

## Step 8 — Automatic Polling (Already Built In)

The scheduler in `backend/app/scheduler.py` runs automatically when the app starts:
- **Form 4**: polls EDGAR every **15 minutes**
- **13D/13G**: polls EDGAR every **20 minutes**

No cron job needed — it runs as a background thread inside FastAPI.

---

## API Reference (Key Endpoints)

### Form 4
| Endpoint | Description |
|----------|-------------|
| `GET /api/form4/feed` | Paginated feed. Params: `txn_type`, `days`, `min_value`, `ticker`, `page` |
| `GET /api/form4/company/{ticker}` | All Form 4s for a stock |
| `GET /api/form4/insider/{cik}` | All trades by a specific insider |
| `GET /api/form4/cluster-buys` | Stocks with 2+ insiders buying in same window |
| `GET /api/form4/buy-sell-ratio/{ticker}` | Monthly buy/sell volume for charting |

### 13D/13G
| Endpoint | Description |
|----------|-------------|
| `GET /api/13dg/feed` | Paginated 13D/13G feed. Params: `form_type`, `days`, `ticker` |
| `GET /api/13dg/company/{ticker}` | All 13D/13G for a stock |
| `GET /api/13dg/filer/{cik}` | All filings by an institutional filer |

### Screener
| Endpoint | Description |
|----------|-------------|
| `GET /api/screener/form4` | Filter by `txn_type`, `min_value`, `days`, `role`, `is_officer`, `exclude_awards` |

### Search
| Endpoint | Description |
|----------|-------------|
| `GET /api/search/?q={query}` | Search tickers and insider names |

Full interactive docs: `https://your-backend.up.railway.app/docs`

---

## Database Schema (Summary)

### `form4_filings`
Stores every non-derivative and derivative transaction from Form 4 filings.
Key columns: `ticker`, `insider_name`, `insider_cik`, `txn_date`, `txn_type` (A/D),
`txn_code` (P=purchase, S=sale, A=award, etc.), `shares`, `price_per_share`, `total_value`,
`officer_title`, `filing_date`, `accession_number`

### `filings_13dg`
Stores SC 13D, SC 13D/A, SC 13G, SC 13G/A filings.
Key columns: `form_type`, `subject_ticker`, `filer_name`, `percent_owned`,
`shares_owned`, `event_date`, `filing_date`

---

## Future Enhancements (Phase 2)

- **Email alerts**: Add a `watched_tickers` table + daily cron using SendGrid (free tier)
- **13F filings**: Quarterly institutional holdings — shows full portfolio changes
- **RSS feed**: Expose `/api/feed.rss` so users can subscribe in Feedly
- **Custom domain**: Add a domain in Vercel settings ($10–15/yr via Namecheap)
- **Caching**: Add Redis on Railway for frequently-hit endpoints (~$0/mo on free tier)
- **Rate limiting**: Add `slowapi` middleware to protect the public API

---

## Troubleshooting

**SEC returning 403 errors during backfill**
→ You forgot to update the `User-Agent` header in both service files (Step 2).

**Backend not connecting to PostgreSQL**
→ Check Railway Variables tab — `DATABASE_URL` must be set. Redeploy after adding.

**Frontend shows no data**
→ Check `NEXT_PUBLIC_API_URL` in Vercel environment variables. Must point to Railway.
→ Check CORS: the backend allows all origins by default — restrict in production.

**Backfill stops halfway**
→ Just rerun the same command. It deduplicates on `accession_number`.

**Railway free tier sleeping**
→ Railway's Starter plan ($5/mo) keeps services always-on. The free trial is limited.
→ For zero cost, use Render free tier — but it sleeps after 15 min of inactivity.
