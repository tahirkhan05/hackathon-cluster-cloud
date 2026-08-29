"""Ledger Pydantic schemas for API validation."""
from typing import Optional
from pydantic import BaseModel
from datetime import datetime
from decimal import Decimal

from domains.ledger.models import TransactionType


class TransactionCreate(BaseModel):
    """Schema for creating a transaction."""
    transaction_type: TransactionType
    from_account: str
    to_account: str
    amount_clstr: Decimal
    related_job_id: Optional[str] = None
    related_task_id: Optional[str] = None
    related_incident_id: Optional[str] = None
    related_node_id: Optional[str] = None
    description: Optional[str] = None


class TransactionResponse(BaseModel):
    """Schema for transaction response."""
    transaction_id: str
    timestamp: datetime
    transaction_type: TransactionType
    from_account: str
    to_account: str
    amount_clstr: Decimal
    related_job_id: Optional[str]
    related_task_id: Optional[str]
    related_incident_id: Optional[str]
    related_node_id: Optional[str]
    description: Optional[str]
    is_debit: bool
    is_credit: bool
    
    class Config:
        from_attributes = True


class TransactionListResponse(BaseModel):
    """Schema for list of transactions."""
    transactions: list[TransactionResponse]
    total: int


class AccountBalance(BaseModel):
    """Schema for account balance."""
    account_id: str
    balance_clstr: Decimal
    pending_clstr: Decimal
    earned_clstr: Decimal
    spent_clstr: Decimal
