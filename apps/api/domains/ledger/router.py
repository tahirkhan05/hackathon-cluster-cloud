"""Ledger API router."""
from typing import Optional
from fastapi import APIRouter, Query
from sqlalchemy.orm import Session
from fastapi import Depends

from database import get_db
from .service import LedgerService

router = APIRouter()


@router.get("/transactions")
async def list_transactions(
    account_id: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """List ledger transactions."""
    service = LedgerService(db)
    transactions = service.get_transactions(account_id=account_id, limit=limit)
    return {
        "transactions": [
            {
                "transaction_id": tx.transaction_id,
                "from_account": tx.from_account,
                "to_account": tx.to_account,
                "amount": float(tx.amount_clstr),
                "transaction_type": tx.transaction_type.value if hasattr(tx.transaction_type, 'value') else str(tx.transaction_type),
                "metadata": {"description": tx.description} if tx.description else {},
                "created_at": tx.timestamp.isoformat() if tx.timestamp else None
            }
            for tx in transactions
        ]
    }


@router.get("/balance/{account_id}")
async def get_balance(account_id: str, db: Session = Depends(get_db)):
    """Get CLSTR balance for account."""
    balance = LedgerService.get_account_balance(db, account_id)
    return {
        "account_id": account_id,
        "balance": balance
    }
