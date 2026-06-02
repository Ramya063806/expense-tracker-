import os
from typing import Optional

import chromadb
from dotenv import load_dotenv

load_dotenv()

COLLECTION_NAME = "expenses"
_chroma_client: Optional[chromadb.CloudClient] = None
_collection = None


def get_chroma_client() -> chromadb.CloudClient:
    global _chroma_client
    if _chroma_client is None:
        host = os.getenv("CHROMA_HOST", "api.trychroma.com")
        _chroma_client = chromadb.CloudClient(
            cloud_host=host,
            cloud_port=443,
            api_key=os.environ["CHROMA_API_KEY"],
            tenant=os.environ["CHROMA_TENANT"],
            database=os.environ["CHROMA_DATABASE"],
        )
    return _chroma_client


def get_collection():
    global _collection
    if _collection is None:
        client = get_chroma_client()
        _collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"description": "Expense tracker semantic search"},
        )
    return _collection


def _document_text(description: str, category: str) -> str:
    return f"{description} | category: {category}"


def index_expense(
    expense_id: int,
    description: str,
    amount: float,
    category: str,
    expense_date: str,
) -> None:
    collection = get_collection()
    collection.upsert(
        ids=[str(expense_id)],
        documents=[_document_text(description, category)],
        metadatas=[
            {
                "expense_id": expense_id,
                "amount": amount,
                "category": category,
                "expense_date": expense_date,
            }
        ],
    )


def remove_expense(expense_id: int) -> None:
    collection = get_collection()
    try:
        collection.delete(ids=[str(expense_id)])
    except Exception:
        pass


def semantic_search(query: str, n_results: int = 10) -> list[int]:
    collection = get_collection()
    results = collection.query(
        query_texts=[query],
        n_results=min(n_results, 50),
        include=["metadatas", "distances"],
    )
    ids: list[int] = []
    if results and results.get("metadatas") and results["metadatas"][0]:
        for meta in results["metadatas"][0]:
            expense_id = meta.get("expense_id")
            if expense_id is not None:
                ids.append(int(expense_id))
    return ids
