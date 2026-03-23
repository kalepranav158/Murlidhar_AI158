# BudgetIQ

BudgetIQ is an AI-powered personal finance and budget management application. It helps users track income and expenses, categorize transactions, set savings goals, and receive intelligent insights to improve their financial health.

## Repository Structure

```text
BudgetIQ/
├── backend/   FastAPI application – REST API, services, models, database access
├── frontend/  React + TypeScript client
├── data/      Seed data, database artifacts
├── docs/      Architecture notes, API contract, design decisions
└── tests/     Unit, integration, and regression test suites
```

## Tech Stack

- **Backend**: Python, FastAPI, SQLite
- **Frontend**: React, TypeScript, Vite
- **AI / Insights**: LangChain + Google GenAI
- **Auth**: JWT-based authentication

## Planned Features

- Transaction ingestion (manual entry and CSV import)
- Automatic categorization of expenses using LLM
- Monthly budget planner with spending-limit alerts
- Savings-goal tracker with progress visualizations
- AI-generated weekly financial summary and tips
- Role-based multi-user support

## Quick Start

### 1. Backend

```bash
cd BudgetIQ
pip install -r requirements.txt
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8001
```

Backend API default URL: `http://127.0.0.1:8001`

### 2. Frontend

```bash
cd BudgetIQ/frontend
npm install
npm run dev
```

Frontend default URL: `http://127.0.0.1:5174`

## Environment Variables

| Variable | Description | Default |
|---|---|---|
| `BUDGETIQ_SECRET_KEY` | JWT signing secret | *(required)* |
| `BUDGETIQ_DB_PATH` | Path to SQLite database file | `data/budgetiq.db` |
| `GOOGLE_API_KEY` | Google GenAI key for AI insights | *(required for AI features)* |
| `BUDGETIQ_DEBUG` | Enable debug endpoints | `false` |

## Development

```bash
# Run tests
python -m pytest BudgetIQ/tests -q

# Lint
cd BudgetIQ/frontend && npm run lint
```

## License

See the [LICENSE](../LICENSE) file in the repository root.
