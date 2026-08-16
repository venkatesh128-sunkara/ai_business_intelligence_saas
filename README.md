# InsightIQ — AI Business Intelligence SaaS

A full-stack, production-style **Natural Language Data Analytics platform**. Upload a CSV/Excel file, ask questions in plain English, and InsightIQ writes the SQL, executes it, builds a chart, and explains the answer — plus automatic business insights, conversation memory, dashboards, multi-user workspaces, subscription usage limits and an admin panel.

Built as a complete end-to-end product (not just a dashboard) to demonstrate the full BI + AI stack.

```
User uploads CSV/Excel
        │
        ▼
Data cleaning + profiling (pandas)
        │
        ▼
SQL database (SQLite/PostgreSQL)
        │
        ▼
AI schema understanding (RAG over columns)
        │
        ▼
Natural language question ──► AI → SQL ──► Query execution
                                          │
                          Charts (Plotly) + Dashboard
                                          │
                                      AI business insights
```

---

## ✨ Features

### Core
- **Authentication** — JWT login/register with bcrypt password hashing, role-based access (admin/member)
- **CSV/Excel upload** — automatic cleaning, column-name normalization, dtype inference, date parsing, deduplication
- **NL → SQL** — ask questions in English; the engine generates and executes SQL
- **Charts** — automatic chart recommendation (line/bar/pie/scatter/indicator) rendered with Plotly
- **Query history & conversation memory** — follow-up questions remember earlier context

### Advanced
- **RAG over schemas** — each column (name, dtype, samples, stats, aliases) is embedded and the top-K relevant columns are retrieved to guide SQL generation
- **AI business insights** — automatic trend/outlier/top-performer/correlation/data-quality analysis, optionally rewritten into narrative by an LLM
- **Dashboard builder** — save any query result as a chart widget and compose live dashboards
- **Multi-user workspaces** — invite members, owner/editor/viewer roles
- **Subscription & usage limits** — per-user monthly query count, dataset and storage quotas (free/pro plans)
- **Admin dashboard** — platform-wide stats: users, datasets, queries, dashboards
- **Data quality checks** — missing-value and outlier detection reported as insights

### Professional / SaaS
- REST API with OpenAPI docs (`/docs`), Docker + docker-compose deployment
- Works **fully offline** via a built-in rule-based NL2SQL engine, and improves automatically when an LLM API key is added

---

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, TypeScript, Vite, Tailwind CSS, React Router, react-plotly.js |
| Backend | Python, FastAPI, SQLAlchemy 2, Pydantic v2 |
| AI | OpenAI-compatible LLM client (OpenAI / Gemini / Ollama), embeddings, RAG, rule-based NL2SQL fallback |
| Data | Pandas, openpyxl, SQLite (default) / PostgreSQL |
| Visuals | Plotly figure JSON |
| Ops | Docker, docker-compose, uvicorn |

**Note on the AI layer:** set `OPENAI_API_KEY` in `backend/.env` to enable the LLM path (SQL generation + insight narrative). Without a key, a deterministic rule engine handles common analytic questions, so the whole product is demo-able with zero cost/API.

---

## 🚀 Quick Start (local, no Docker)

### 1. Backend

```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
# source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env          # optional: add OPENAI_API_KEY

python -m app.seed            # creates admin, demo user + 3000-row sample dataset
uvicorn app.main:app --reload # http://localhost:8000  (docs at /docs)
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev                   # http://localhost:5173 (proxies /api to :8000)
```

### 3. Log in

| Role | Email | Password |
|---|---|---|
| Admin | `admin@insightiq.dev` | `admin123` |
| Demo user | `demo@insightiq.dev` | `demo123` |

Open **http://localhost:5173** → sign in as the demo user → open **Ask AI** and try:
- `What were the highest-revenue products?`
- `Total sales by region`
- `Show monthly revenue trend`
- `How many orders in Q2 2023?`
- `Top 5 customers by total revenue`

---

## 🐳 Run with Docker

```bash
docker compose up --build
# Frontend:  http://localhost:8080
# Backend:   http://localhost:8000
```

---

## 🧭 Project Structure

```
.
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI app + CORS + router registration
│   │   ├── seed.py            # admin/demo users + sample sales dataset
│   │   ├── core/              # settings, JWT/bcrypt security
│   │   ├── db/                # SQLAlchemy engine + session
│   │   ├── models/            # User, Workspace, Dataset, Query, Dashboard, Usage
│   │   ├── schemas/           # Pydantic request/response models
│   │   ├── api/               # auth, datasets, query, insights, dashboards, admin
│   │   └── services/
│   │       ├── data_processor.py   # CSV/Excel ingestion + cleaning + profiling
│   │       ├── nl2sql.py           # LLM NL2SQL + rule-based fallback
│   │       ├── vector_store.py     # RAG over column schemas
│   │       ├── chart_engine.py     # result rows → Plotly figure JSON
│   │       ├── insight_engine.py   # trends, outliers, correlations, missing data
│   │       └── ai_provider.py      # OpenAI-compatible LLM client
│   └── tests/                 # smoke + integration test scripts
├── frontend/
│   └── src/
│       ├── pages/             # Overview, Datasets, AskAI, Insights, Dashboards, Admin
│       ├── components/        # Layout, ChartView, DataTable, UploadDataset, InsightCard
│       └── lib/               # api client, auth context, types
├── docker-compose.yml
└── README.md
```

---

## 🔄 Data Flow

1. **Upload** — file is read with pandas, cleaned (name normalization, date inference, dedup, type coercion), profiled per column (missing, unique, samples, stats) and persisted to a SQL table.
2. **Schema knowledge** — every column becomes a knowledge chunk embedded into a vector store. At query time the question retrieves the most relevant columns (RAG).
3. **Ask** — the question + schema + RAG context + conversation history go to the LLM (or rule engine) which returns `{sql, chart spec, summary}`.
4. **Execute** — SQL runs against the database; rows are capped at 1000 for safety.
5. **Chart** — the chart spec drives Plotly figure JSON (auto-scaled colors, hovertemplates, dark theme).
6. **Insights** — statistical engine computes trends/outliers/top performers/correlations/missing-data; optionally LLM-rewritten into executive narrative.
7. **Dashboards** — any saved query result can be pinned as a widget.

---

## 🔐 Security & Limits

- Passwords hashed with bcrypt; JWT access tokens; role checks on every route
- Datasets are scoped to workspaces — non-members cannot read them
- Query count, dataset count and storage are tracked monthly per user (free/pro)
- SQL is generated against the analysis DB only; results limited to 1,000 rows
- Upload size and row-count caps enforced

---

## 🧪 Tests

```bash
# with the backend running
cd backend
python tests/smoke_test.py       # NL2SQL coverage
python tests/integration_test.py # auth, upload, insights, dashboards, admin, usage
```

---

## ☁️ Deployment Notes

- Switch to PostgreSQL by setting `DATABASE_URL=postgresql+psycopg://...` in `backend/.env`
- Set a long random `SECRET_KEY` in production
- Add `OPENAI_API_KEY` (+ `OPENAI_BASE_URL` for Gemini) to enable full LLM mode
- Frontend is a static build served by nginx (or any static host); point `/api` at the backend
