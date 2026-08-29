"""
CLSTR Economic System

Manages wallets, transactions, rewards, penalties, and economic flows.
All operations are auditable and idempotent.
"""
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
from decimal import Decimal
import logging
from sqlalchemy.orm import Session
from sqlalchemy import func

from domains.ledger.models import Transaction, TransactionType
from config import settings

logger = logging.getLogger(__name__)


class InsufficientBalanceError(Exception):
    """Raised when account has insufficient balance."""
    pass


class InvalidTransactionError(Exception):
    """Raised when transaction is invalid."""
    pass


class EconomicSystem:
    """
    CLSTR economic system manager.
    
    Handles:
    - Wallet management
    - Payment flows
    - Rewards and penalties
    - Balance validation
    - Transaction audit trail
    """
    
    CUSTOMER_PREFIX = "customer:"
    PROVIDER_PREFIX = "provider:"
    BROKER_ACCOUNT = "broker:platform"
    STAKE_POOL = "stake:pool"
    COMPENSATION_POOL = "compensation:pool"
    
    def __init__(self, db: Session):
        self.db = db
    
    
    def get_balance(self, account: str) -> Decimal:
        """
        Get current balance for an account.
        
        Calculates from transaction ledger (source of truth).
        """
        credits = self.db.query(
            func.sum(Transaction.amount_clstr)
        ).filter(
            Transaction.to_account == account
        ).scalar() or Decimal(0)
        
        debits = self.db.query(
            func.sum(Transaction.amount_clstr)
        ).filter(
            Transaction.from_account == account
        ).scalar() or Decimal(0)
        
        balance = Decimal(credits) - Decimal(debits)
        
        logger.debug(f"Balance for {account}: {balance} CLSTR")
        
        return balance
    
    def get_balances(self, accounts: List[str]) -> Dict[str, Decimal]:
        """Get balances for multiple accounts efficiently."""
        balances = {}
        for account in accounts:
            balances[account] = self.get_balance(account)
        return balances
    
    def initialize_customer_wallet(self, customer_id: str) -> Transaction:
        """
        Initialize customer wallet with initial balance.
        
        Idempotent: Only creates transaction if no initial balance exists.
        """
        account = f"{self.CUSTOMER_PREFIX}{customer_id}"
        
        existing = self.db.query(Transaction).filter(
            Transaction.to_account == account,
            Transaction.transaction_type == TransactionType.INITIAL_BALANCE
        ).first()
        
        if existing:
            logger.info(f"Customer wallet {account} already initialized")
            return existing
        
        initial_amount = Decimal(settings.INITIAL_CUSTOMER_BALANCE)
        
        transaction = self._create_transaction(
            transaction_type=TransactionType.INITIAL_BALANCE,
            from_account="system:bank",
            to_account=account,
            amount=initial_amount,
            description=f"Initial balance for customer {customer_id}"
        )
        
        logger.info(f"Initialized customer wallet {account} with {initial_amount} CLSTR")
        
        return transaction
    
    def initialize_provider_wallet(self, provider_id: str, node_id: str) -> Transaction:
        """
        Initialize provider wallet.
        
        Providers start with 0 balance but can earn through work.
        """
        account = f"{self.PROVIDER_PREFIX}{provider_id}"
        
        existing = self.db.query(Transaction).filter(
            Transaction.to_account == account,
            Transaction.transaction_type == TransactionType.INITIAL_BALANCE
        ).first()
        
        if existing:
            return existing
        
        transaction = self._create_transaction(
            transaction_type=TransactionType.INITIAL_BALANCE,
            from_account="system:bank",
            to_account=account,
            amount=Decimal(0),
            description=f"Wallet initialized for provider {provider_id}",
            related_node_id=node_id
        )
        
        logger.info(f"Initialized provider wallet {account}")
        
        return transaction
    
    
    def job_created_payment(
        self,
        job_id: str,
        customer_id: str,
        total_budget: Decimal
    ) -> Transaction:
        """
        Customer pays for job creation.
        
        Transfers budget from customer to escrow.
        Idempotent based on job_id.
        """
        customer_account = f"{self.CUSTOMER_PREFIX}{customer_id}"
        escrow_account = f"escrow:job:{job_id}"
        
        existing = self.db.query(Transaction).filter(
            Transaction.related_job_id == job_id,
            Transaction.transaction_type == TransactionType.JOB_CREATED
        ).first()
        
        if existing:
            logger.info(f"Job {job_id} already paid")
            return existing
        
        customer_balance = self.get_balance(customer_account)
        if customer_balance < total_budget:
            raise InsufficientBalanceError(
                f"Customer {customer_id} has insufficient balance: "
                f"{customer_balance} < {total_budget}"
            )
        
        transaction = self._create_transaction(
            transaction_type=TransactionType.JOB_CREATED,
            from_account=customer_account,
            to_account=escrow_account,
            amount=total_budget,
            description=f"Job {job_id} budget locked in escrow",
            related_job_id=job_id
        )
        
        logger.info(
            f"Job {job_id}: Customer {customer_id} paid {total_budget} CLSTR to escrow"
        )
        
        return transaction
    
    def task_completed_payment(
        self,
        task_id: str,
        job_id: str,
        provider_id: str,
        node_id: str,
        task_cost: Decimal
    ) -> List[Transaction]:
        """
        Process payment when task completes successfully.
        
        Flow:
        1. Escrow → Provider (payment)
        2. Escrow → Broker (fee)
        
        Returns list of transactions created.
        Idempotent based on task_id.
        """
        existing = self.db.query(Transaction).filter(
            Transaction.related_task_id == task_id,
            Transaction.transaction_type == TransactionType.TASK_COMPLETED
        ).first()
        
        if existing:
            logger.info(f"Task {task_id} already paid")
            return self.db.query(Transaction).filter(
                Transaction.related_task_id == task_id
            ).all()
        
        escrow_account = f"escrow:job:{job_id}"
        provider_account = f"{self.PROVIDER_PREFIX}{provider_id}"
        
        broker_fee = task_cost * Decimal(settings.BROKER_FEE_PERCENTAGE) / Decimal(100)
        provider_payment = task_cost - broker_fee
        
        escrow_balance = self.get_balance(escrow_account)
        if escrow_balance < task_cost:
            raise InsufficientBalanceError(
                f"Escrow for job {job_id} has insufficient balance: "
                f"{escrow_balance} < {task_cost}"
            )
        
        transactions = []
        
        provider_tx = self._create_transaction(
            transaction_type=TransactionType.TASK_COMPLETED,
            from_account=escrow_account,
            to_account=provider_account,
            amount=provider_payment,
            description=f"Payment for task {task_id} completion",
            related_job_id=job_id,
            related_task_id=task_id,
            related_node_id=node_id
        )
        transactions.append(provider_tx)
        
        broker_tx = self._create_transaction(
            transaction_type=TransactionType.BROKER_FEE,
            from_account=escrow_account,
            to_account=self.BROKER_ACCOUNT,
            amount=broker_fee,
            description=f"Broker fee for task {task_id}",
            related_job_id=job_id,
            related_task_id=task_id
        )
        transactions.append(broker_tx)
        
        logger.info(
            f"Task {task_id}: Provider {provider_id} earned {provider_payment} CLSTR "
            f"(fee: {broker_fee} CLSTR)"
        )
        
        return transactions
    
    
    def hold_provider_stake(
        self,
        provider_id: str,
        node_id: str,
        stake_amount: Optional[Decimal] = None
    ) -> Transaction:
        """
        Hold stake from provider for reliability guarantee.
        
        Idempotent based on node_id.
        """
        if stake_amount is None:
            stake_amount = Decimal(settings.PROVIDER_RELIABILITY_STAKE)
        
        provider_account = f"{self.PROVIDER_PREFIX}{provider_id}"
        
        existing = self.db.query(Transaction).filter(
            Transaction.related_node_id == node_id,
            Transaction.transaction_type == TransactionType.STAKE_HELD
        ).first()
        
        if existing:
            logger.info(f"Stake for node {node_id} already held")
            return existing
        
        provider_balance = self.get_balance(provider_account)
        if provider_balance < stake_amount:
            raise InsufficientBalanceError(
                f"Provider {provider_id} has insufficient balance for stake: "
                f"{provider_balance} < {stake_amount}"
            )
        
        transaction = self._create_transaction(
            transaction_type=TransactionType.STAKE_HELD,
            from_account=provider_account,
            to_account=self.STAKE_POOL,
            amount=stake_amount,
            description=f"Reliability stake for node {node_id}",
            related_node_id=node_id
        )
        
        logger.info(f"Held stake of {stake_amount} CLSTR for node {node_id}")
        
        return transaction
    
    def return_provider_stake(
        self,
        provider_id: str,
        node_id: str
    ) -> Optional[Transaction]:
        """
        Return stake to provider when node deregisters cleanly.
        
        Idempotent: only returns if stake was held.
        """
        provider_account = f"{self.PROVIDER_PREFIX}{provider_id}"
        
        stake_tx = self.db.query(Transaction).filter(
            Transaction.related_node_id == node_id,
            Transaction.transaction_type == TransactionType.STAKE_HELD
        ).first()
        
        if not stake_tx:
            logger.warning(f"No stake found for node {node_id}")
            return None
        
        returned_tx = self.db.query(Transaction).filter(
            Transaction.related_node_id == node_id,
            Transaction.transaction_type == TransactionType.STAKE_RETURNED
        ).first()
        
        if returned_tx:
            logger.info(f"Stake for node {node_id} already returned")
            return returned_tx
        
        transaction = self._create_transaction(
            transaction_type=TransactionType.STAKE_RETURNED,
            from_account=self.STAKE_POOL,
            to_account=provider_account,
            amount=stake_tx.amount_clstr,
            description=f"Stake returned for node {node_id}",
            related_node_id=node_id
        )
        
        logger.info(
            f"Returned stake of {stake_tx.amount_clstr} CLSTR to provider {provider_id}"
        )
        
        return transaction
    
    
    def apply_failure_penalty(
        self,
        provider_id: str,
        node_id: str,
        incident_id: str,
        job_id: Optional[str] = None
    ) -> Transaction:
        """
        Apply penalty to provider for failure.
        
        Penalty comes from provider's stake.
        Idempotent based on incident_id.
        """
        existing = self.db.query(Transaction).filter(
            Transaction.related_incident_id == incident_id,
            Transaction.transaction_type == TransactionType.PENALTY_APPLIED
        ).first()
        
        if existing:
            logger.info(f"Penalty for incident {incident_id} already applied")
            return existing
        
        stake_tx = self.db.query(Transaction).filter(
            Transaction.related_node_id == node_id,
            Transaction.transaction_type == TransactionType.STAKE_HELD
        ).first()
        
        if not stake_tx:
            raise InvalidTransactionError(f"No stake found for node {node_id}")
        
        penalty_amount = (
            stake_tx.amount_clstr * 
            Decimal(settings.FAILURE_PENALTY_PERCENTAGE) / 
            Decimal(100)
        )
        
        transaction = self._create_transaction(
            transaction_type=TransactionType.PENALTY_APPLIED,
            from_account=self.STAKE_POOL,
            to_account=self.COMPENSATION_POOL,
            amount=penalty_amount,
            description=f"Failure penalty for incident {incident_id}",
            related_incident_id=incident_id,
            related_node_id=node_id,
            related_job_id=job_id
        )
        
        logger.warning(
            f"Applied penalty of {penalty_amount} CLSTR to provider {provider_id} "
            f"for incident {incident_id}"
        )
        
        return transaction
    
    def compensate_customer(
        self,
        customer_id: str,
        job_id: str,
        incident_id: str,
        compensation_amount: Decimal
    ) -> Transaction:
        """
        Compensate customer for failed tasks.
        
        Compensation comes from penalty pool.
        Idempotent based on incident_id + customer_id.
        """
        customer_account = f"{self.CUSTOMER_PREFIX}{customer_id}"
        
        existing = self.db.query(Transaction).filter(
            Transaction.related_incident_id == incident_id,
            Transaction.to_account == customer_account,
            Transaction.transaction_type == TransactionType.COMPENSATION_ISSUED
        ).first()
        
        if existing:
            logger.info(f"Customer {customer_id} already compensated for incident {incident_id}")
            return existing
        
        pool_balance = self.get_balance(self.COMPENSATION_POOL)
        if pool_balance < compensation_amount:
            raise InsufficientBalanceError(
                f"Compensation pool has insufficient balance: "
                f"{pool_balance} < {compensation_amount}"
            )
        
        transaction = self._create_transaction(
            transaction_type=TransactionType.COMPENSATION_ISSUED,
            from_account=self.COMPENSATION_POOL,
            to_account=customer_account,
            amount=compensation_amount,
            description=f"Compensation for incident {incident_id}",
            related_incident_id=incident_id,
            related_job_id=job_id
        )
        
        logger.info(
            f"Compensated customer {customer_id} with {compensation_amount} CLSTR "
            f"for incident {incident_id}"
        )
        
        return transaction
    
    def reward_recovery_provider(
        self,
        provider_id: str,
        node_id: str,
        task_id: str,
        incident_id: str,
        base_task_cost: Decimal
    ) -> Transaction:
        """
        Reward provider who recovered failed tasks.
        
        Recovery reward is bonus on top of normal payment.
        Idempotent based on task_id + incident.
        """
        provider_account = f"{self.PROVIDER_PREFIX}{provider_id}"
        
        existing = self.db.query(Transaction).filter(
            Transaction.related_task_id == task_id,
            Transaction.related_incident_id == incident_id,
            Transaction.transaction_type == TransactionType.RECOVERY_REWARD
        ).first()
        
        if existing:
            logger.info(f"Recovery reward for task {task_id} already issued")
            return existing
        
        reward_amount = (
            base_task_cost * 
            Decimal(settings.RECOVERY_REWARD_PERCENTAGE) / 
            Decimal(100)
        )
        
        transaction = self._create_transaction(
            transaction_type=TransactionType.RECOVERY_REWARD,
            from_account=self.COMPENSATION_POOL,
            to_account=provider_account,
            amount=reward_amount,
            description=f"Recovery reward for task {task_id}",
            related_task_id=task_id,
            related_incident_id=incident_id,
            related_node_id=node_id
        )
        
        logger.info(
            f"Rewarded provider {provider_id} with {reward_amount} CLSTR "
            f"for recovering task {task_id}"
        )
        
        return transaction
    
    
    def get_transaction_history(
        self,
        account: Optional[str] = None,
        transaction_type: Optional[TransactionType] = None,
        limit: int = 100
    ) -> List[Transaction]:
        """Get transaction history with filters."""
        query = self.db.query(Transaction)
        
        if account:
            query = query.filter(
                (Transaction.from_account == account) |
                (Transaction.to_account == account)
            )
        
        if transaction_type:
            query = query.filter(Transaction.transaction_type == transaction_type)
        
        return query.order_by(Transaction.timestamp.desc()).limit(limit).all()
    
    def get_account_summary(self, account: str) -> Dict[str, Any]:
        """Get comprehensive account summary."""
        balance = self.get_balance(account)
        
        total_credits = self.db.query(func.count(Transaction.transaction_id)).filter(
            Transaction.to_account == account
        ).scalar() or 0
        
        total_debits = self.db.query(func.count(Transaction.transaction_id)).filter(
            Transaction.from_account == account
        ).scalar() or 0
        
        recent = self.get_transaction_history(account, limit=10)
        
        return {
            "account": account,
            "balance": float(balance),
            "total_credits": total_credits,
            "total_debits": total_debits,
            "recent_transactions": [
                {
                    "transaction_id": tx.transaction_id,
                    "type": tx.transaction_type.value,
                    "amount": float(tx.amount_clstr),
                    "timestamp": tx.timestamp.isoformat()
                }
                for tx in recent
            ]
        }
    
    
    def _create_transaction(
        self,
        transaction_type: TransactionType,
        from_account: str,
        to_account: str,
        amount: Decimal,
        description: Optional[str] = None,
        related_job_id: Optional[str] = None,
        related_task_id: Optional[str] = None,
        related_incident_id: Optional[str] = None,
        related_node_id: Optional[str] = None
    ) -> Transaction:
        """Create transaction with balance tracking."""
        
        if amount < 0:
            raise InvalidTransactionError(f"Amount cannot be negative: {amount}")
        
        if amount == 0:
            raise InvalidTransactionError("Amount cannot be zero")
        
        transaction = Transaction(
            transaction_type=transaction_type,
            from_account=from_account,
            to_account=to_account,
            amount_clstr=amount,
            description=description,
            related_job_id=related_job_id,
            related_task_id=related_task_id,
            related_incident_id=related_incident_id,
            related_node_id=related_node_id
        )
        
        self.db.add(transaction)
        self.db.commit()
        self.db.refresh(transaction)
        
        transaction.from_account_balance_after = self.get_balance(from_account)
        transaction.to_account_balance_after = self.get_balance(to_account)
        
        self.db.commit()
        
        return transaction
