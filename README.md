# SocialScope AI

**From Social Data to Smart Insights.**

A full-stack **Data Analysis Essentials (DAE)** project that turns a public
social-media URL into a cleaned, scored and visualised dataset you can inspect
in the browser and download as CSV, a formatted Excel workbook, or a written
report.

```
SOCIAL MEDIA URL → COLLECTION → CLEANING → SENTIMENT → STATISTICS → CHARTS → EXPORT
```

---

## Table of contents

1. [Data integrity rules](#1-data-integrity-rules)
2. [Features](#2-features)
3. [Tech stack](#3-tech-stack)
4. [Project structure](#4-project-structure)
5. [Installation (Windows)](#5-installation-windows)
6. [API key setup](#6-api-key-setup)
7. [Demo mode](#7-demo-mode)
8. [Running the tests](#8-running-the-tests)
9. [API reference](#9-api-reference)
10. [Sample API requests and output](#10-sample-api-requests-and-output)
11. [Methodology](#11-methodology)
12. [Exports](#12-exports)
13. [Troubleshooting](#13-troubleshooting)
14. [Limitations and future work](#14-limitations-and-future-work)

---

## 1. Data integrity rules

These rules shaped every design decision, and the test suite enforces them.

* **Official APIs only.** Collection uses the YouTube Data API v3 and the Meta
  Graph API. Nothing is scraped, no private endpoint is reverse-engineered, and
  no authentication, privacy, rate-limit or anti-bot control is bypassed.
* **A real API key is required for live analysis.** If a credential is missing,
  the request is refused with a message naming the environment variable to set.
  It never falls back to invented data.
* **Missing metrics are never estimated.** If an API does not return a field,
  the UI, the API response, the CSV, the Excel workbook and the report all say
  *"Data unavailable through the current platform API."* An empty CSV cell means
  "not available", never `0`.
* **Demo data is synthetic and labelled.** The bundled dataset exists so the
  pipeline can be demonstrated before credentials exist. It is generated
  locally, stored with `data_mode="demo"`, banner-marked in the interface, and
  carries a `data_mode` column in every export.
* **No stack traces reach the user.** Unexpected errors are logged server-side
  and returned as a friendly message.

---

## 2. Features

**Workflow**

* Landing page with an animated dashboard preview (clearly marked as sample data).
* One-time name capture; remembered in `localStorage` for later visits.
* Live platform detection while you type, with per-platform support status.
* Nine-stage animated analysis checklist.

**Analysis**

* Animated KPI tiles for views, likes, comments, shares, engagement rate,
  sentiment split, record count and analysis time.
* Nine interactive ECharts visualisations: engagement bars, sentiment donut,
  sentiment scores, sentiment-over-time, likes-vs-sentiment scatter, comment
  length, hourly activity, keyword bars, hashtag bars, correlation heatmap, and
  a CSS word cloud.
* Descriptive statistics: mean, median, mode, min, max, variance, standard
  deviation, quartiles and range.
* Pearson correlation matrix with strength/direction labels.
* Sentiment trend by day and week, plus hour-of-day activity.
* Keyword extraction with TF-IDF, bigrams, hashtags with mean sentiment, and
  top liked / most positive / most negative comments.
* Data-derived insights and an explicit data-limitations section per analysis.

**Sentiment**

* VADER classification (positive / neutral / negative) with pos/neg/neu/compound.
* TextBlob polarity and subjectivity for every record, shown side by side with
  VADER so the classification can be sanity-checked.
* Dependency-free lexicon fallback if VADER is unavailable, and an explicit
  note when TextBlob is unavailable so the UI never implies a model that did
  not run.

**Data table**

* Server-side search, sentiment filter, date range, minimum-likes filter,
  sortable columns, pagination, expandable rows and copy-to-clipboard.

**Exports**

* Clean CSV, raw pre-cleaning CSV, an eight-sheet Excel workbook, and an
  analysis report as HTML or PDF.

**Platform**

* Responsive from 360 px to 1920 px, dark and light themes, glassmorphism and
  3D hover cards, animated counters, toast notifications, route-level error
  boundary, and keyboard-accessible controls that respect
  `prefers-reduced-motion`.

---

## 3. Tech stack

### Frontend

| Purpose | Technology |
|---|---|
| Framework | React 18 + TypeScript + Vite |
| Styling | Tailwind CSS v4 (CSS-first `@theme`) |
| Animation | Framer Motion |
| Charts | Apache ECharts |
| Icons | lucide-react |
| Routing | react-router-dom |

### Backend

| Purpose | Technology |
|---|---|
| API | Python + FastAPI + Uvicorn |
| Validation | Pydantic v2 + pydantic-settings |
| Persistence | SQLAlchemy 2 (SQLite default, PostgreSQL supported) |
| HTTP client | httpx |
| Sentiment | vaderSentiment + textblob |
| Exports | openpyxl, reportlab |
| Tests | pytest |

> **A note on the wider DAE stack.** `requirements.txt` contains only what the
> runtime actually imports. `requirements-optional.txt` lists pandas, numpy,
> scikit-learn, nltk, matplotlib, seaborn and plotly for extending the analysis
> in a notebook. The statistical and sentiment stages are implemented in
> dependency-free Python so results are reproducible without a heavy scientific
> install — pandas and numpy are **not** imported by the running pipeline.

---

## 4. Project structure

```text
socialscope-ai/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI app, CORS, error handlers
│   │   ├── config.py               # Environment-backed settings
│   │   ├── database.py             # Engine, session, Base
│   │   ├── schemas.py              # Request/response contracts
│   │   ├── repository.py           # Persistence mapping
│   │   ├── api/
│   │   │   ├── analysis.py         # detect / analyze / demo / read back
│   │   │   ├── export.py           # CSV, XLSX, HTML/PDF
│   │   │   └── history.py          # History and profile
│   │   ├── platforms/
│   │   │   ├── base.py             # PlatformAdapter contract
│   │   │   ├── detector.py         # URL → platform, documented limits
│   │   │   ├── youtube.py          # YouTube Data API v3
│   │   │   ├── facebook.py         # Meta Graph API
│   │   │   ├── instagram.py        # Meta Graph API
│   │   │   ├── meta.py             # Shared Graph helpers
│   │   │   └── demo.py             # Synthetic demo generator
│   │   ├── analysis/
│   │   │   ├── cleaning.py         # Dedupe, normalize, spam, outliers
│   │   │   ├── sentiment.py        # VADER + TextBlob
│   │   │   ├── statistics.py       # Descriptive, correlation, time series
│   │   │   ├── engagement.py       # Engagement rate with availability
│   │   │   ├── keywords.py         # Keywords, hashtags, top comments
│   │   │   ├── insights.py         # Data-derived insight sentences
│   │   │   └── pipeline.py         # Orchestrates the whole run
│   │   ├── exports/
│   │   │   ├── csv_export.py
│   │   │   ├── excel_export.py
│   │   │   └── report.py           # HTML + PDF
│   │   ├── models/                 # SQLAlchemy ORM models
│   │   └── core/                   # Errors, rate limiting, URL helpers
│   ├── tests/                      # 106 pytest tests
│   ├── requirements.txt
│   ├── requirements-optional.txt
│   ├── .env.example
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/             # UI kit, table, charts, layout helpers
│   │   │   └── charts/             # EChart wrapper + chart set
│   │   ├── pages/                  # Landing, Welcome, Dashboard, Analysis…
│   │   ├── layouts/AppShell.tsx    # Sidebar + header shell
│   │   ├── services/api.ts         # Typed API client
│   │   ├── hooks/                  # useAnalysis, useHistory, useProfile
│   │   ├── context/                # User, theme, toasts
│   │   ├── utils/format.ts
│   │   ├── types/index.ts
│   │   ├── App.tsx
│   │   └── styles.css
│   ├── package.json
│   ├── vite.config.ts
│   ├── Dockerfile
│   └── nginx.conf
├── data/                           # SQLite db, raw/, cleaned/, exports/
├── docs/
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

---

## 5. Installation (Windows)

### Prerequisites

| Tool | Version |
|---|---|
| Python | 3.11 or newer |
| Node.js | 20 or newer |
| npm | 10 or newer |
| Git | optional |

### Step 1 — clone

```powershell
git clone <repository-url>
cd socialscope-ai
```

### Step 2 — backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

> If PowerShell blocks the activation script:
> `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`

Start the API:

```powershell
uvicorn app.main:app --reload --port 8000
```

- API: <http://localhost:8000>
- Interactive docs: <http://localhost:8000/docs>
- Health check: <http://localhost:8000/api/health>

The SQLite database is created automatically at `data/socialscope.db` on first
run, along with `data/raw`, `data/cleaned`, `data/exports` and `data/demo`.

### Step 3 — frontend

In a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open <http://localhost:5173>. The Vite dev server proxies `/api` to port 8000,
so no configuration is needed.

### Optional — Docker

```powershell
Copy-Item .env.example .env
docker compose up --build
```

Add `--profile postgres` to include the optional PostgreSQL service.

### Optional — PostgreSQL

```powershell
cd backend
pip install -r requirements-postgres.txt
# then in backend/.env:
# DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/socialscope
```

The driver is a separate requirements file because SQLite needs no extra
package. The `backend/Dockerfile` installs it automatically, so Docker and
container hosts work with PostgreSQL without extra steps.

---

## 6. API key setup

Keys live only in `backend/.env` (or your environment) and are never sent to the
browser, never logged, and never committed.

### YouTube

1. Open the [Google Cloud Console](https://console.cloud.google.com) and create
   a project.
2. Enable **YouTube Data API v3**.
3. Create an API key under *APIs & Services → Credentials*.
4. Set `YOUTUBE_API_KEY` in `backend/.env` and restart the API.

```env
YOUTUBE_API_KEY=AIza...
```

Then paste a public video link (`watch?v=…`, `youtu.be/…` or `/shorts/…`).

### Facebook

1. Create an app in the [Meta developers dashboard](https://developers.facebook.com).
2. Add the **Facebook** product and generate a long-lived Page access token.
3. The token must belong to the Page that owns the post — posts on personal
   profiles cannot be read through the Graph API.

```env
FACEBOOK_ACCESS_TOKEN=EAAB...
FACEBOOK_PAGE_ID=1234567890
```

### Instagram

1. Link a **professional** (Business or Creator) Instagram account to a Facebook
   Page.
2. Generate a long-lived token with the same permissions.

```env
INSTAGRAM_ACCESS_TOKEN=EAAB...
INSTAGRAM_ACCOUNT_ID=17890000000000000
```

Leave `*_ACCOUNT_ID` unset to let the backend look it up via `/me/accounts`.

> The Instagram Graph API **cannot resolve an arbitrary public post by its
> shortcode.** The media must belong to the authorised professional account, and
> the app says so plainly rather than substituting other content.

### Environment variables

| Variable | Default | Purpose |
|---|---|---|
| `YOUTUBE_API_KEY` | unset | YouTube Data API v3 key |
| `FACEBOOK_ACCESS_TOKEN` | unset | Meta token for Facebook Pages |
| `INSTAGRAM_ACCESS_TOKEN` | unset | Meta token for Instagram |
| `INSTAGRAM_ACCOUNT_ID` | unset | Skip the `/me/accounts` lookup |
| `FACEBOOK_PAGE_ID` | unset | Page identifier |
| `META_API_VERSION` | `v21.0` | Graph API version |
| `DATABASE_URL` | SQLite at `data/socialscope.db` | SQLAlchemy URL |
| `SECRET_KEY` | `change-me-in-production` | Change before deploying |
| `CORS_ORIGINS` | `http://localhost:5173` | Comma-separated origins |
| `RATE_LIMIT_REQUESTS` | `30` | Requests per window, per client |
| `RATE_LIMIT_WINDOW_SECONDS` | `60` | Rate-limit window |
| `REQUEST_TIMEOUT_SECONDS` | `20` | Upstream API timeout |
| `MAX_COMMENT_PAGES` | `5` | Comment pages fetched per run |
| `COMMENTS_PER_PAGE` | `100` | Comments requested per page |
| `SENTIMENT_BACKEND` | `auto` | `auto`, `vader` or `lexicon` |
| `ENABLE_DEMO_MODE` | `true` | Set `false` to remove demo data |
| `VITE_API_URL` | proxy `/api` | Frontend API base (build-time) |

---

## 7. Demo mode

Demo mode exists so the entire pipeline — charts, statistics, table, CSV,
Excel and report — can be demonstrated and tested **before** any API key is
configured.

* Trigger: **New Analysis → Demo Mode → choose a platform.**
* The dataset is generated locally from a fixed seed, so results are
  reproducible.
* Every demo analysis is stored with `data_mode="demo"` and displays
  **"DEMO DATA — This dataset is included for demonstration purposes and is not
  live social-media data."**
* Exports carry the same banner in the Summary sheet, the Limitations sheet and
  the report header, plus a `data_mode` column in the CSV.

**Live analysis is not stubbed out.** Pressing *Analyze Now* without a
credential returns HTTP 503 with a message naming the variable to set; it never
falls back to demo data. To remove demo data entirely, set
`ENABLE_DEMO_MODE=false`.

---

## 8. Running the tests

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
pytest -q
```

Expected: **106 passed**.

Coverage includes URL/platform detection (including lookalike domains such as
`evil.com/youtube.com` and unsafe schemes), the cleaning pipeline, sentiment
thresholds, descriptive statistics, correlation edge cases, engagement-rate
availability, the full API contract, record filtering/sorting/pagination, all
five export formats, and the guarantee that errors never leak stack traces.

```powershell
cd frontend
npm run typecheck
npm run build
```

---

## 9. API reference

All routes are prefixed with `/api`.

| Method | Route | Purpose |
|---|---|---|
| `GET` | `/health` | Service and configuration status (no secrets) |
| `GET` | `/platforms` | Supported platforms, limits, and configured state |
| `POST` | `/detect` | Validate a URL and return the detected platform |
| `POST` | `/analyze` | Detect, collect, analyse — the main endpoint |
| `POST` | `/analyze/youtube` | Same, but asserts the URL is YouTube |
| `POST` | `/analyze/facebook` | Same, but asserts the URL is Facebook |
| `POST` | `/analyze/instagram` | Same, but asserts the URL is Instagram |
| `POST` | `/demo` | Run the pipeline on bundled synthetic data |
| `GET` | `/analysis/{id}` | Full analysis: records, charts, statistics, insights |
| `GET` | `/analysis/{id}/comments` | Search, filter, sort, paginate records |
| `GET` | `/analysis/{id}/sentiment` | Summary plus the VADER/TextBlob comparison |
| `GET` | `/analysis/{id}/engagement` | Engagement metrics and correlations |
| `GET` | `/analysis/{id}/export/csv` | `?dataset=clean` (default) or `raw` |
| `GET` | `/analysis/{id}/export/excel` | Formatted multi-sheet workbook |
| `GET` | `/analysis/{id}/export/report` | `?format=html` (default) or `pdf` |
| `GET` | `/history` | Saved analyses, optional `?user_name=&platform=` |
| `GET` | `/history/{id}` | One history row |
| `DELETE` | `/history/{id}` | Delete an analysis and its records |
| `GET` | `/profile` / `/profile/{name}` | Aggregate user statistics |
| `POST` | `/profile/rename` | Reassign stored analyses to a new name |

### Error shape

Every failure returns the same structure, with a user-safe message:

```json
{
  "error": {
    "code": "unsupported_platform",
    "message": "Unsupported social-media URL (twitter.com). SocialScope AI currently supports YouTube, Facebook and Instagram.",
    "detail": {}
  }
}
```

| Code | HTTP | When |
|---|---|---|
| `validation_error` | 422 | Empty or malformed request body |
| `invalid_url` | 422 | Not a usable http(s) URL |
| `unsupported_platform` | 422 | Valid URL on an unsupported host |
| `platform_mismatch` | 422 | `/analyze/youtube` called with an Instagram URL |
| `no_data` | 422 | Content exists but exposed no public comments |
| `not_found` | 404 | Unknown analysis or route |
| `missing_credentials` | 503 | Live analysis requested with no API key |
| `platform_api_error` | 502 | Upstream API failed, refused or timed out |
| `rate_limited` | 429 | Too many analysis requests |
| `internal_error` | 500 | Unexpected failure (logged, never traced) |

---

## 10. Sample API requests and output

### Detect a platform

```powershell
Invoke-RestMethod -Uri http://localhost:8000/api/detect -Method Post `
  -ContentType 'application/json' `
  -Body '{"url":"https://youtu.be/dQw4w9WgXcQ"}'
```

```json
{
  "url": "https://youtu.be/dQw4w9WgXcQ",
  "platform": "youtube",
  "platform_label": "YouTube",
  "detected": true,
  "configured": true,
  "message": "Platform detected successfully — YouTube"
}
```

### Analyse a URL (requires a key)

```powershell
Invoke-RestMethod -Uri http://localhost:8000/api/analyze -Method Post `
  -ContentType 'application/json' `
  -Body '{"url":"https://www.youtube.com/watch?v=dQw4w9WgXcQ","user_name":"Aarav"}'
```

Abridged response:

```json
{
  "analysis_id": "a7d83f19ec054180",
  "platform": "youtube",
  "data_mode": "live",
  "status": "completed",
  "total_records": 200,
  "removed_records": 25,
  "sentiment_method": "vader",
  "engagement": {
    "views": 1284500,
    "likes": 96120,
    "comments": 2186,
    "shares": null,
    "engagement_rate": 7.6533,
    "interactions_included": ["likes", "comments"],
    "unavailable_fields": ["shares"]
  },
  "sentiment_summary": {
    "total": 200, "positive": 134, "neutral": 29, "negative": 37,
    "positive_pct": 67.0, "neutral_pct": 14.5, "negative_pct": 18.5,
    "avg_compound": 0.3401
  },
  "unavailable_fields": ["shares", "subscribers", "thumbnail"]
}
```

### Demo analysis (no key required)

```powershell
Invoke-RestMethod -Uri http://localhost:8000/api/demo -Method Post `
  -ContentType 'application/json' -Body '{"platform":"youtube","user_name":"Aarav"}'
```

```json
{
  "analysis_id": "cbb61072ab004ac3",
  "data_mode": "demo",
  "demo_notice": "DEMO DATA — This dataset is included for demonstration purposes and is not live social-media data.",
  "cleaning_report": {
    "input_count": 225, "removed_empty": 1, "removed_duplicate": 23,
    "removed_spam": 1, "output_count": 200
  }
}
```

### Filter, search and sort records

```powershell
# Only negative comments
.../api/analysis/{id}/comments?sentiment=negative&page_size=10

# Search comment text
.../api/analysis/{id}/comments?search=audio

# Most-liked first
.../api/analysis/{id}/comments?sort=likes&order=desc
```

```json
{
  "total": 19, "page": 1, "page_size": 10, "pages": 2,
  "records": [
    { "sentiment": "negative", "compound": -0.4767, "like_count": 3,
      "raw_text": "This take is wrong, the actual fix is much simpler." }
  ]
}
```

### Download exports

```powershell
.../api/analysis/{id}/export/csv
.../api/analysis/{id}/export/csv?dataset=raw
.../api/analysis/{id}/export/excel
.../api/analysis/{id}/export/report?format=pdf
```

---

## 11. Methodology

| DAE stage | Implementation |
|---|---|
| **Collection** | Platform adapters fetch only officially documented fields; provenance (API name and endpoints called) is stored on each analysis. |
| **Cleaning** | Remove empty records, duplicate IDs and duplicate normalized text, spam patterns, and link-only comments. Unwrap HTML, strip URLs/mentions/hashtag markers for NLP, remove zero-width and control characters, collapse whitespace, validate timestamps, and flag length outliers via the IQR method. Every removal is counted. |
| **Transformation** | ISO-8601 UTC timestamps, integer coercion (`1.2K` → `1200`), hashtags, mentions, keywords, word/character counts, language tag. |
| **NLP** | VADER valence scoring (compound, pos, neg, neu) with thresholds `>= 0.05` positive, `<= -0.05` negative, otherwise neutral. TextBlob polarity and subjectivity recorded alongside for comparison. Coarse emotion tag from lexical cues. |
| **Descriptive statistics** | Count, mean, median, mode, min, max, variance, standard deviation, Q1, Q3, range and sum. |
| **Correlation** | Pearson *r* between sentiment, polarity, subjectivity, likes and length. Returns `null` for fewer than three usable pairs or a zero-variance series rather than a misleading number. |
| **Engagement** | `(interactions) / views × 100`, computed **only** when views and at least one interaction were returned. The included interactions are named in the response. |
| **Visualisation** | Charts are pre-computed server-side and rendered with ECharts. |
| **Interpretation** | Insight sentences are templates filled with calculated values. A conclusion is never generated for a field the API did not provide. |
| **Export** | CSV (strictly tabular), an eight-sheet styled workbook, and an HTML/PDF report. |

**Reproducibility.** Demo data uses a fixed seed, so the same run yields the
same statistics. Sentiment is deterministic, not sampled.

---

## 12. Exports

### CSV

47 columns following the DAE convention, grouped as source, content, text,
engagement, sentiment, comparison, NLP extras and quality flags. UTF-8 with a
BOM so Excel opens it correctly. Strictly tabular — no trailing note rows, so
`pandas.read_csv` works directly. A blank cell means *not available*.

### Excel (`.xlsx`)

| Sheet | Contents |
|---|---|
| Summary | Source metadata plus a KPI table with a per-metric availability column |
| Raw Data | Records exactly as the API returned them, before cleaning |
| Clean Data | Deduplicated, normalized, scored records |
| Sentiment Analysis | VADER and TextBlob side by side per record |
| Engagement Analysis | KPIs plus every correlation |
| Keywords | Rank, frequency, TF-IDF, document frequency |
| Hashtags | Rank, frequency, mean sentiment, tone |
| Data Limitations | Every documented caveat for the analysis |

Sheets have frozen headers, autofilters, sized columns and number formatting.

### Report (HTML / PDF)

Analysis overview, engagement statistics, sentiment statistics, descriptive
statistics, correlations, keywords, hashtags, observations, data limitations
and collection notes — with the demo banner when applicable.

---

## 13. Troubleshooting

| Symptom | Cause and fix |
|---|---|
| `Cannot reach the SocialScope AI API` | Backend is not running. Start it: `uvicorn app.main:app --reload --port 8000`. |
| `The YouTube API is not configured` | Set `YOUTUBE_API_KEY` in `backend/.env` and restart. |
| YouTube 403 / quota error | Verify the key, that the API is enabled, and that the quota is not exhausted. |
| Instagram/Facebook "credentials required" | Set the Meta token and the matching account/Page ID. The app does not scrape as a fallback. |
| "No public comments were available" | A genuine platform result — comments may be disabled, held for review, or owned by another account. |
| CORS error in the browser console | Add the exact frontend origin, including port, to `CORS_ORIGINS`. |
| `Data unavailable through the current platform API` | Working as designed. The API does not expose that field. |
| Excel export 503 | `openpyxl` is missing. Run `pip install -r requirements.txt`. |
| Port already in use | Stop the other process, or change the port and update `VITE_API_URL` to match. |
| Metrics show `0` in a background tab | Fixed: the counter renders the real value when the tab is hidden. |

---

## 14. Limitations and future work

**Platform limits are real and permanent.** Private, deleted, censored and
creator-hidden comments cannot be recovered lawfully. The Graph API cannot read
personal-profile posts or resolve an arbitrary Instagram shortcode. The YouTube
Data API has no share count. Comment-level like counts are often owner-only.
The app's in-app *API Limitations* page states all of this per platform.

**Engineering limits.** The rate limiter is in-process, so a multi-worker
deployment needs Redis. Analyses run synchronously, so very large datasets would
need a background job queue. SQLite is a development default; PostgreSQL is
configured but untested against production load. There is no authentication —
the display name is a local convenience, not an identity.

**Possible next steps.** Authenticated users, a Celery/Redis job runner, Alembic
migrations, a transformer-based multilingual sentiment backend, topic modelling
on the cleaned corpus, scheduled re-analysis, and multi-campaign comparison.

---

## Conclusion

SocialScope AI implements the full DAE pipeline — collection, preprocessing,
NLP, descriptive statistics, correlation, visualisation, interpretation and
export — as a working product rather than a prototype. Every major button
performs a real request: detection validates, analysis collects through an
official API, the table queries the server, and the exporters build real CSV,
XLSX, PDF and HTML files from stored data.

Its most important design decision is provenance. Every number is either tied to
a real API response or visibly marked as synthetic demonstration data, and a
metric that could not be obtained is reported as unavailable rather than
approximated.

**SocialScope AI — From Social Data to Smart Insights.**
#   s o c i a l - m e d i a - s e n t i m e n t - a n a l y s i s  
 