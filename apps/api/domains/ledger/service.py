"""Ledger service for CLSTR token operations."""
from decimal import Decimal
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import func

from domains.ledger.models import Transaction, TransactionType
from domains.ledger.schemas import TransactionCreate


class LedgerService:
    """Service for managing CLSTR token transactions."""
    
    @staticmethod
    def create_transaction(db: Session, transaction: TransactionCreate) -> Transaction:
        """Create a new transaction record."""
        db_transaction = Transaction(
            transaction_type=transaction.transaction_type,
            from_account=transaction.from_account,
            to_account=transaction.to_account,
            amount_clstr=transaction.amount_clstr,
            related_job_id=transaction.related_job_id,
            related_task_id=transaction.related_task_id,
            related_incident_id=transaction.related_incident_id,
            related_node_id=transaction.related_node_id,
            description=transaction.description
        )
        
        db.add(db_transaction)
        db.commit()
        db.refresh(db_transaction)
        return db_transaction
    
    @staticmethod
    def get_account_balance(db: Session, account_id: str) -> Decimal:
        """
        Calculate current account balance.
        
        Sum all incoming transactions minus all outgoing transactions.
        """
        credits = db.query(func.sum(Transaction.amount_clstr)).filter(
            Transaction.to_account == account_id
        ).scalar() or Decimal(0)
        
        debits = db.query(func.sum(Transaction.amount_clstr)).filter(
            Transaction.from_account == account_id
        ).scalar() or Decimal(0)
        
        return credits - debits
    
    @staticmethod
    def initialize_account(db: Session, account_id: str, initial_balance: Decimal) -> Transaction:
        """Initialize account with starting balance."""
        transaction = TransactionCreate(
            transaction_type=TransactionType.INITIAL_BALANCE,
            from_account="system",
            to_account=account_id,
            amount_clstr=initial_balance,
            description=f"Initial balance for {account_id}"
        )
        
        return LedgerService.create_transaction(db, transaction)
    
    @staticmethod
    def get_balance(db: Session, account_id: str) -> float:
        """Get account balance as float."""
        balance = LedgerService.get_account_balance(db, account_id)
        return float(balance)
    
    @staticmethod
    def get_transactions(
        db: Session, 
        account_id: Optional[str] = None, 
        limit: int = 20
    ) -> List[Transaction]:
        """Get transactions, optionally filtered by account_id."""
        query = db.query(Transaction)
        
        if account_id:
            query = query.filter(
                (Transaction.from_account == account_id) | 
                (Transaction.to_account == account_id)
            )
        
        return query.order_by(Transaction.created_at.desc()).limit(limit).all()
