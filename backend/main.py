from datetime import date
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend import database as db
from backend import chroma_service as chroma
from backend.schemas import ExpenseCreate, ExpenseResponse, SearchResult, StatsResponse

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

app = FastAPI(title="Expense Tracker", version="1.0.0")


@app.on_event("startup")
def startup() -> None:
    db.init_db()
    try:
        chroma.get_collection()
    except Exception as e:
        print(f"Warning: Chroma connection failed at startup: {e}")


def to_response(row: dict) -> ExpenseResponse:
    return ExpenseResponse(
        id=row["id"],
        description=row["description"],
        amount=row["amount"],
        category=row["category"],
        expense_date=date.fromisoformat(row["expense_date"]),
        created_at=row["created_at"],
    )


@app.get("/api/health")
def health():
    chroma_ok = False
    try:
        chroma.get_chroma_client().heartbeat()
        chroma_ok = True
    except Exception:
        pass
    return {"status": "ok", "chroma_connected": chroma_ok}


@app.get("/api/expenses", response_model=list[ExpenseResponse])
def list_expenses(category: Optional[str] = None):
    rows = db.list_expenses(category=category)
    return [to_response(r) for r in rows]


@app.post("/api/expenses", response_model=ExpenseResponse, status_code=201)
def create_expense(payload: ExpenseCreate):
    row = db.create_expense(
        description=payload.description.strip(),
        amount=payload.amount,
        category=payload.category.strip(),
        expense_date=payload.expense_date,
    )
    try:
        chroma.index_expense(
            expense_id=row["id"],
            description=row["description"],
            amount=row["amount"],
            category=row["category"],
            expense_date=row["expense_date"],
        )
    except Exception as e:
        db.delete_expense(row["id"])
        raise HTTPException(
            status_code=503,
            detail=f"Expense saved locally failed to index in Chroma: {e}",
        ) from e
    return to_response(row)


@app.delete("/api/expenses/{expense_id}", status_code=204)
def delete_expense(expense_id: int):
    if not db.delete_expense(expense_id):
        raise HTTPException(status_code=404, detail="Expense not found")
    try:
        chroma.remove_expense(expense_id)
    except Exception:
        pass


@app.get("/api/search", response_model=SearchResult)
def search_expenses(q: str = Query(..., min_length=1)):
    try:
        ids = chroma.semantic_search(q.strip())
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Semantic search unavailable: {e}",
        ) from e
    rows = db.get_expenses_by_ids(ids)
    return SearchResult(
        expenses=[to_response(r) for r in rows],
        query=q.strip(),
    )


@app.get("/api/stats", response_model=StatsResponse)
def stats():
    data = db.get_stats()
    return StatsResponse(**data)


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
