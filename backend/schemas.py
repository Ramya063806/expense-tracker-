from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class ExpenseCreate(BaseModel):
    description: str = Field(..., min_length=1, max_length=500)
    amount: float = Field(..., gt=0)
    category: str = Field(..., min_length=1, max_length=100)
    expense_date: date


class ExpenseResponse(BaseModel):
    id: int
    description: str
    amount: float
    category: str
    expense_date: date
    created_at: str


class SearchResult(BaseModel):
    expenses: list[ExpenseResponse]
    query: str


class StatsResponse(BaseModel):
    total: float
    count: int
    by_category: dict[str, float]
