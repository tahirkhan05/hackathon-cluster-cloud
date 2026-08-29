"""Ledger data models - stub for initial setup."""
from sqlalchemy import Column, String, DateTime, Numeric, Enum as SQLEnum
from datetime import datetime
import uuid
import enum

from database import Base


class TransactionType(str, enum.Enum):
    """Transaction type enum."""
    JOB_CREATED = "job_created"
    TASK_COMPLETED = "task_completed"
    BROKER_FEE = "broker_fee"
    STAKE_HELD = "stake_held"
    STAKE_RETURNED = "stake_returned"
    PENALTY_APPLIED = "penalty_applied"
    COMPENSATION_ISSUED = "compensation_issued"
    RECOVERY_REWARD = "recovery_reward"


class Transaction(Base):
    """Transaction model - to be fully implemented in task #3."""
    __tablename__ = "transactions"
    
    transaction_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    timestamp = Column(DateTime, default=datetime.utcnow)
    transaction_type = Column(SQLEnum(TransactionType), nullable=False)
    from_account = Column(String, nullable=False)
    to_account = Column(String, nullable=False)
    amount_clstr = Column(Numeric(10, 2), nullable=False)
