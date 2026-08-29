"""Ledger data models."""
from sqlalchemy import Column, String, DateTime, Numeric, Enum as SQLEnum, Text, Index
from datetime import datetime
import uuid
import enum

from database import Base


class TransactionType(str, enum.Enum):
    """CLSTR transaction types."""
    JOB_CREATED = "job_created"
    TASK_COMPLETED = "task_completed"
    BROKER_FEE = "broker_fee"
    STAKE_HELD = "stake_held"
    STAKE_RETURNED = "stake_returned"
    PENALTY_APPLIED = "penalty_applied"
    COMPENSATION_ISSUED = "compensation_issued"
    RECOVERY_REWARD = "recovery_reward"
    INITIAL_BALANCE = "initial_balance"


class Transaction(Base):
    """
    CLSTR token transaction ledger.
    
    Immutable record of all economic activity in the system.
    Tracks customer spending, provider earnings, penalties,
    rewards, and platform fees.
    
    All transactions are deterministic and auditable.
    """
    __tablename__ = "transactions"
    
    transaction_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    transaction_type = Column(SQLEnum(TransactionType), nullable=False, index=True)
    
    from_account = Column(String, nullable=False, index=True)
    to_account = Column(String, nullable=False, index=True)
    
    amount_clstr = Column(Numeric(10, 2), nullable=False)
    
    related_job_id = Column(String, nullable=True, index=True)
    related_task_id = Column(String, nullable=True)
    related_incident_id = Column(String, nullable=True)
    related_node_id = Column(String, nullable=True)
    
    description = Column(Text, nullable=True)
    
    from_account_balance_after = Column(Numeric(10, 2), nullable=True)
    to_account_balance_after = Column(Numeric(10, 2), nullable=True)
    
    __table_args__ = (
        Index('idx_transactions_account_time', 'from_account', 'timestamp'),
        Index('idx_transactions_job', 'related_job_id', 'timestamp'),
    )
    
    @property
    def is_debit(self) -> bool:
        """Check if transaction is a debit (outgoing)."""
        return self.amount_clstr < 0
    
    @property
    def is_credit(self) -> bool:
        """Check if transaction is a credit (incoming)."""
        return self.amount_clstr > 0
