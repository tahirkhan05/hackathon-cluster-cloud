"""Ledger API router."""
from fastapi import APIRouter

router = APIRouter()


@router.get("/transactions")
async def list_transactions():
    """List ledger transactions."""
    return {"transactions": []}


@router.get("/balance/{account_id}")
async def get_balance(account_id: str):
    """Get CLSTR balance for account."""
    return {
        "account_id": account_id,
        "balance_clstr": 10000
    }
