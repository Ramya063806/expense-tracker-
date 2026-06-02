# Expense Tracker

A personal expense tracker with **SQLite** for structured storage and **Chroma Cloud** for semantic search over your expense descriptions.

## Features

- Add, list, and delete expenses (description, amount, category, date)
- Dashboard stats: total spent, transaction count, breakdown by category
- **Semantic search** powered by Chroma — find expenses by meaning, not exact keywords
- Modern web UI served by FastAPI

## Setup

1. **Python 3.10+** required.

2. Create a virtual environment and install dependencies:

   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Configure Chroma Cloud in `.env` (already provided for this project):

   ```
   CHROMA_HOST=api.trychroma.com
   CHROMA_API_KEY=...
   CHROMA_TENANT=...
   CHROMA_DATABASE=development
   ```

4. Run the app:

   ```bash
   python run.py
   ```

5. Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser.

## API

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Health + Chroma connection status |
| GET | `/api/expenses` | List expenses (`?category=Food`) |
| POST | `/api/expenses` | Create expense |
| DELETE | `/api/expenses/{id}` | Delete expense |
| GET | `/api/search?q=...` | Semantic search via Chroma |
| GET | `/api/stats` | Spending statistics |

## Project layout

```
expense tracker/
├── .env                 # Chroma credentials (not committed)
├── backend/
│   ├── main.py          # FastAPI app
│   ├── database.py      # SQLite
│   ├── chroma_service.py
│   └── schemas.py
├── static/              # Web UI
├── data/                # SQLite DB (created at runtime)
└── run.py
```

## Security

Never commit `.env` or API keys to version control. Use `.env.example` as a template.
