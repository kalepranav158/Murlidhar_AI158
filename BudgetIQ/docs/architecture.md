# BudgetIQ – Architecture Overview

## High-Level Design

```
┌─────────────────────────────────┐
│           React Frontend         │
│  (Vite + TypeScript)             │
└──────────────┬──────────────────┘
               │ HTTP / REST
┌──────────────▼──────────────────┐
│         FastAPI Backend          │
│  ┌───────────┐  ┌─────────────┐ │
│  │ Auth API  │  │ Finance API │ │
│  └───────────┘  └─────────────┘ │
│  ┌────────────────────────────┐ │
│  │     AI Insights Service    │ │
│  │  (LangChain + Google GenAI)│ │
│  └────────────────────────────┘ │
└──────────────┬──────────────────┘
               │
┌──────────────▼──────────────────┐
│           SQLite DB              │
└─────────────────────────────────┘
```

## Data Models

- **User** – id, username, hashed_password, created_at
- **Transaction** – id, user_id, amount, category, description, date, type (income/expense)
- **Budget** – id, user_id, category, monthly_limit, month
- **SavingsGoal** – id, user_id, name, target_amount, current_amount, deadline

## API Endpoints (planned)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/auth/register` | Register new user |
| POST | `/auth/login` | Obtain JWT token |
| GET | `/transactions` | List transactions |
| POST | `/transactions` | Create transaction |
| GET | `/budgets` | List budgets |
| POST | `/budgets` | Create/update budget |
| GET | `/goals` | List savings goals |
| POST | `/goals` | Create savings goal |
| GET | `/insights/summary` | AI-generated financial summary |
