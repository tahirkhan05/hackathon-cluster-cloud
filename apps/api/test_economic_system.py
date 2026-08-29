"""
Tests for CLSTR Economic System - Phase 9

Run with: pytest test_economic_system.py -v
"""
import pytest
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Base
from domains.ledger.economic_system import (
    EconomicSystem,
    InsufficientBalanceError,
    InvalidTransactionError
)
from domains.ledger.models import TransactionType

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_economic.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_test_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


# ============================================================================
# WALLET INITIALIZATION TESTS
# ============================================================================

def test_initialize_customer_wallet():
    """Test customer wallet initialization with initial balance."""
    db = next(get_test_db())
    econ = EconomicSystem(db)
    
    tx = econ.initialize_customer_wallet("customer-1")
    
    # Verify transaction created
    assert tx.transaction_type == TransactionType.INITIAL_BALANCE
    assert tx.to_account == "customer:customer-1"
    assert tx.amount_clstr == Decimal(10000)  # Default initial balance
    
    # Verify balance
    balance = econ.get_balance("customer:customer-1")
    assert balance == Decimal(10000)


def test_initialize_customer_wallet_idempotent():
    """Test wallet initialization is idempotent."""
    db = next(get_test_db())
    econ = EconomicSystem(db)
    
    tx1 = econ.initialize_customer_wallet("customer-1")
    tx2 = econ.initialize_customer_wallet("customer-1")
    
    # Should return same transaction
    assert tx1.transaction_id == tx2.transaction_id
    
    # Balance should not double
    balance = econ.get_balance("customer:customer-1")
    assert balance == Decimal(10000)


def test_initialize_provider_wallet():
    """Test provider wallet initialization (zero balance)."""
    db = next(get_test_db())
    econ = EconomicSystem(db)
    
    tx = econ.initialize_provider_wallet("provider-1", "node-1")
    
    assert tx.transaction_type == TransactionType.INITIAL_BALANCE
    assert tx.to_account == "provider:provider-1"
    assert tx.amount_clstr == Decimal(0)
    
    balance = econ.get_balance("provider:provider-1")
    assert balance == Decimal(0)


# ============================================================================
# JOB PAYMENT TESTS
# ============================================================================

def test_job_created_payment():
    """Test customer pays for job creation."""
    db = next(get_test_db())
    econ = EconomicSystem(db)
    
    # Initialize customer
    econ.initialize_customer_wallet("customer-1")
    
    # Pay for job
    tx = econ.job_created_payment(
        job_id="job-1",
        customer_id="customer-1",
        total_budget=Decimal(1000)
    )
    
    assert tx.transaction_type == TransactionType.JOB_CREATED
    assert tx.from_account == "customer:customer-1"
    assert tx.to_account == "escrow:job:job-1"
    assert tx.amount_clstr == Decimal(1000)
    
    # Verify balances
    customer_balance = econ.get_balance("customer:customer-1")
    assert customer_balance == Decimal(9000)  # 10000 - 1000
    
    escrow_balance = econ.get_balance("escrow:job:job-1")
    assert escrow_balance == Decimal(1000)


def test_job_payment_insufficient_balance():
    """Test job payment fails with insufficient balance."""
    db = next(get_test_db())
    econ = EconomicSystem(db)
    
    econ.initialize_customer_wallet("customer-1")
    
    # Try to pay more than balance
    with pytest.raises(InsufficientBalanceError):
        econ.job_created_payment(
            job_id="job-1",
            customer_id="customer-1",
            total_budget=Decimal(50000)  # > 10000 initial balance
        )


def test_job_payment_idempotent():
    """Test job payment is idempotent."""
    db = next(get_test_db())
    econ = EconomicSystem(db)
    
    econ.initialize_customer_wallet("customer-1")
    
    tx1 = econ.job_created_payment("job-1", "customer-1", Decimal(1000))
    tx2 = econ.job_created_payment("job-1", "customer-1", Decimal(1000))
    
    # Should return same transaction
    assert tx1.transaction_id == tx2.transaction_id
    
    # Should not double charge
    customer_balance = econ.get_balance("customer:customer-1")
    assert customer_balance == Decimal(9000)


# ============================================================================
# TASK COMPLETION PAYMENT TESTS
# ============================================================================

def test_task_completed_payment():
    """Test payment flow when task completes."""
    db = next(get_test_db())
    econ = EconomicSystem(db)
    
    # Setup
    econ.initialize_customer_wallet("customer-1")
    econ.initialize_provider_wallet("provider-1", "node-1")
    econ.job_created_payment("job-1", "customer-1", Decimal(1000))
    
    # Complete task
    transactions = econ.task_completed_payment(
        task_id="task-1",
        job_id="job-1",
        provider_id="provider-1",
        node_id="node-1",
        task_cost=Decimal(100)
    )
    
    # Should create 2 transactions (provider payment + broker fee)
    assert len(transactions) == 2
    
    # Verify provider payment
    provider_tx = transactions[0]
    assert provider_tx.transaction_type == TransactionType.TASK_COMPLETED
    assert provider_tx.to_account == "provider:provider-1"
    assert provider_tx.amount_clstr == Decimal(95)  # 100 - 5% fee
    
    # Verify broker fee
    broker_tx = transactions[1]
    assert broker_tx.transaction_type == TransactionType.BROKER_FEE
    assert broker_tx.to_account == "broker:platform"
    assert broker_tx.amount_clstr == Decimal(5)  # 5% of 100
    
    # Verify balances
    provider_balance = econ.get_balance("provider:provider-1")
    assert provider_balance == Decimal(95)
    
    broker_balance = econ.get_balance("broker:platform")
    assert broker_balance == Decimal(5)
    
    escrow_balance = econ.get_balance("escrow:job:job-1")
    assert escrow_balance == Decimal(900)  # 1000 - 100


def test_task_payment_idempotent():
    """Test task payment is idempotent."""
    db = next(get_test_db())
    econ = EconomicSystem(db)
    
    econ.initialize_customer_wallet("customer-1")
    econ.initialize_provider_wallet("provider-1", "node-1")
    econ.job_created_payment("job-1", "customer-1", Decimal(1000))
    
    # Complete task twice
    tx1 = econ.task_completed_payment("task-1", "job-1", "provider-1", "node-1", Decimal(100))
    tx2 = econ.task_completed_payment("task-1", "job-1", "provider-1", "node-1", Decimal(100))
    
    # Should return same transactions
    assert len(tx1) == len(tx2)
    assert tx1[0].transaction_id == tx2[0].transaction_id
    
    # Should not double pay
    provider_balance = econ.get_balance("provider:provider-1")
    assert provider_balance == Decimal(95)


# ============================================================================
# STAKE MANAGEMENT TESTS
# ============================================================================

def test_hold_provider_stake():
    """Test holding provider stake."""
    db = next(get_test_db())
    econ = EconomicSystem(db)
    
    # Give provider some balance
    econ.initialize_customer_wallet("temp")
    econ.job_created_payment("temp-job", "temp", Decimal(1000))
    econ.task_completed_payment("temp-task", "temp-job", "provider-1", "node-1", Decimal(200))
    
    # Hold stake
    tx = econ.hold_provider_stake("provider-1", "node-1")
    
    assert tx.transaction_type == TransactionType.STAKE_HELD
    assert tx.from_account == "provider:provider-1"
    assert tx.to_account == "stake:pool"
    assert tx.amount_clstr == Decimal(100)  # Default stake
    
    # Verify balances
    provider_balance = econ.get_balance("provider:provider-1")
    assert provider_balance == Decimal(90)  # 190 - 100 stake
    
    stake_pool_balance = econ.get_balance("stake:pool")
    assert stake_pool_balance == Decimal(100)


def test_return_provider_stake():
    """Test returning provider stake."""
    db = next(get_test_db())
    econ = EconomicSystem(db)
    
    # Setup: earn money and hold stake
    econ.initialize_customer_wallet("temp")
    econ.job_created_payment("temp-job", "temp", Decimal(1000))
    econ.task_completed_payment("temp-task", "temp-job", "provider-1", "node-1", Decimal(200))
    econ.hold_provider_stake("provider-1", "node-1")
    
    # Return stake
    tx = econ.return_provider_stake("provider-1", "node-1")
    
    assert tx.transaction_type == TransactionType.STAKE_RETURNED
    assert tx.from_account == "stake:pool"
    assert tx.to_account == "provider:provider-1"
    assert tx.amount_clstr == Decimal(100)
    
    # Verify stake returned
    provider_balance = econ.get_balance("provider:provider-1")
    assert provider_balance == Decimal(190)  # Back to original


# ============================================================================
# FAILURE ECONOMICS TESTS
# ============================================================================

def test_apply_failure_penalty():
    """Test applying penalty for failure."""
    db = next(get_test_db())
    econ = EconomicSystem(db)
    
    # Setup: provider with stake
    econ.initialize_customer_wallet("temp")
    econ.job_created_payment("temp-job", "temp", Decimal(1000))
    econ.task_completed_payment("temp-task", "temp-job", "provider-1", "node-1", Decimal(200))
    econ.hold_provider_stake("provider-1", "node-1")
    
    # Apply penalty
    tx = econ.apply_failure_penalty(
        provider_id="provider-1",
        node_id="node-1",
        incident_id="incident-1",
        job_id="job-1"
    )
    
    assert tx.transaction_type == TransactionType.PENALTY_APPLIED
    assert tx.from_account == "stake:pool"
    assert tx.to_account == "compensation:pool"
    assert tx.amount_clstr == Decimal(20)  # 20% of 100 stake
    
    # Verify penalty moved to compensation pool
    comp_balance = econ.get_balance("compensation:pool")
    assert comp_balance == Decimal(20)


def test_compensate_customer():
    """Test customer compensation."""
    db = next(get_test_db())
    econ = EconomicSystem(db)
    
    # Setup: penalty applied
    econ.initialize_customer_wallet("temp")
    econ.job_created_payment("temp-job", "temp", Decimal(1000))
    econ.task_completed_payment("temp-task", "temp-job", "provider-1", "node-1", Decimal(200))
    econ.hold_provider_stake("provider-1", "node-1")
    econ.apply_failure_penalty("provider-1", "node-1", "incident-1", "job-1")
    
    # Initialize affected customer
    econ.initialize_customer_wallet("customer-1")
    
    # Compensate
    tx = econ.compensate_customer(
        customer_id="customer-1",
        job_id="job-1",
        incident_id="incident-1",
        compensation_amount=Decimal(15)
    )
    
    assert tx.transaction_type == TransactionType.COMPENSATION_ISSUED
    assert tx.from_account == "compensation:pool"
    assert tx.to_account == "customer:customer-1"
    assert tx.amount_clstr == Decimal(15)
    
    # Verify customer received compensation
    customer_balance = econ.get_balance("customer:customer-1")
    assert customer_balance == Decimal(10015)  # 10000 + 15


def test_reward_recovery_provider():
    """Test recovery reward."""
    db = next(get_test_db())
    econ = EconomicSystem(db)
    
    # Setup: penalty in pool
    econ.initialize_customer_wallet("temp")
    econ.job_created_payment("temp-job", "temp", Decimal(1000))
    econ.task_completed_payment("temp-task", "temp-job", "provider-1", "node-1", Decimal(200))
    econ.hold_provider_stake("provider-1", "node-1")
    econ.apply_failure_penalty("provider-1", "node-1", "incident-1", "job-1")
    
    # Initialize recovery provider
    econ.initialize_provider_wallet("provider-2", "node-2")
    
    # Reward recovery
    tx = econ.reward_recovery_provider(
        provider_id="provider-2",
        node_id="node-2",
        task_id="task-2",
        incident_id="incident-1",
        base_task_cost=Decimal(100)
    )
    
    assert tx.transaction_type == TransactionType.RECOVERY_REWARD
    assert tx.from_account == "compensation:pool"
    assert tx.to_account == "provider:provider-2"
    assert tx.amount_clstr == Decimal(10)  # 10% of 100
    
    # Verify reward issued
    provider_balance = econ.get_balance("provider:provider-2")
    assert provider_balance == Decimal(10)


# ============================================================================
# VALIDATION TESTS
# ============================================================================

def test_prevent_negative_amount():
    """Test that negative amounts are rejected."""
    db = next(get_test_db())
    econ = EconomicSystem(db)
    
    with pytest.raises(InvalidTransactionError):
        econ._create_transaction(
            transaction_type=TransactionType.INITIAL_BALANCE,
            from_account="system:bank",
            to_account="customer:test",
            amount=Decimal(-100)
        )


def test_prevent_zero_amount():
    """Test that zero amounts are rejected."""
    db = next(get_test_db())
    econ = EconomicSystem(db)
    
    with pytest.raises(InvalidTransactionError):
        econ._create_transaction(
            transaction_type=TransactionType.INITIAL_BALANCE,
            from_account="system:bank",
            to_account="customer:test",
            amount=Decimal(0)
        )


def test_balance_cannot_go_negative():
    """Test that operations fail if balance would go negative."""
    db = next(get_test_db())
    econ = EconomicSystem(db)
    
    # Initialize with 100
    econ.initialize_customer_wallet("customer-1")
    
    # Try to spend more than balance
    with pytest.raises(InsufficientBalanceError):
        econ.job_created_payment("job-1", "customer-1", Decimal(20000))
    
    # Balance should remain unchanged
    balance = econ.get_balance("customer:customer-1")
    assert balance == Decimal(10000)


# ============================================================================
# TRANSACTION HISTORY TESTS
# ============================================================================

def test_get_transaction_history():
    """Test transaction history retrieval."""
    db = next(get_test_db())
    econ = EconomicSystem(db)
    
    econ.initialize_customer_wallet("customer-1")
    econ.job_created_payment("job-1", "customer-1", Decimal(100))
    econ.job_created_payment("job-2", "customer-1", Decimal(200))
    
    # Get customer history
    history = econ.get_transaction_history("customer:customer-1")
    
    assert len(history) >= 3  # init + 2 payments
    
    # Most recent should be job-2
    assert history[0].related_job_id == "job-2"


def test_get_account_summary():
    """Test account summary."""
    db = next(get_test_db())
    econ = EconomicSystem(db)
    
    econ.initialize_customer_wallet("customer-1")
    econ.job_created_payment("job-1", "customer-1", Decimal(500))
    
    summary = econ.get_account_summary("customer:customer-1")
    
    assert summary["account"] == "customer:customer-1"
    assert summary["balance"] == 9500.0
    assert summary["total_credits"] >= 1  # Initial balance
    assert summary["total_debits"] >= 1  # Job payment
    assert len(summary["recent_transactions"]) > 0


# ============================================================================
# END-TO-END ECONOMIC FLOW TEST
# ============================================================================

def test_complete_economic_flow():
    """
    Test complete economic flow:
    Customer → Job → Tasks → Provider earnings → Failure → Penalty → Compensation → Recovery reward
    """
    db = next(get_test_db())
    econ = EconomicSystem(db)
    
    # Step 1: Initialize wallets
    econ.initialize_customer_wallet("customer-1")
    econ.initialize_provider_wallet("provider-1", "node-1")
    econ.initialize_provider_wallet("provider-2", "node-2")
    
    assert econ.get_balance("customer:customer-1") == Decimal(10000)
    
    # Step 2: Customer creates job
    econ.job_created_payment("job-1", "customer-1", Decimal(1000))
    
    assert econ.get_balance("customer:customer-1") == Decimal(9000)
    assert econ.get_balance("escrow:job:job-1") == Decimal(1000)
    
    # Step 3: Provider 1 completes some tasks
    econ.task_completed_payment("task-1", "job-1", "provider-1", "node-1", Decimal(100))
    econ.task_completed_payment("task-2", "job-1", "provider-1", "node-1", Decimal(100))
    
    assert econ.get_balance("provider:provider-1") == Decimal(190)  # 95 * 2
    assert econ.get_balance("broker:platform") == Decimal(10)  # 5 * 2
    
    # Step 4: Provider 1 stakes
    econ.hold_provider_stake("provider-1", "node-1")
    
    assert econ.get_balance("provider:provider-1") == Decimal(90)
    assert econ.get_balance("stake:pool") == Decimal(100)
    
    # Step 5: Provider 1 fails
    econ.apply_failure_penalty("provider-1", "node-1", "incident-1", "job-1")
    
    assert econ.get_balance("compensation:pool") == Decimal(20)
    
    # Step 6: Customer compensated
    econ.compensate_customer("customer-1", "job-1", "incident-1", Decimal(15))
    
    assert econ.get_balance("customer:customer-1") == Decimal(9015)  # 9000 + 15
    
    # Step 7: Provider 2 recovers failed tasks
    econ.task_completed_payment("task-3", "job-1", "provider-2", "node-2", Decimal(100))
    econ.reward_recovery_provider("provider-2", "node-2", "task-3", "incident-1", Decimal(100))
    
    assert econ.get_balance("provider:provider-2") == Decimal(105)  # 95 + 10 reward
    
    # Verify total economy balance (should be conserved)
    total_in_system = (
        econ.get_balance("customer:customer-1") +
        econ.get_balance("provider:provider-1") +
        econ.get_balance("provider:provider-2") +
        econ.get_balance("broker:platform") +
        econ.get_balance("escrow:job:job-1") +
        econ.get_balance("stake:pool") +
        econ.get_balance("compensation:pool")
    )
    
    # Total should equal initial (10000) minus what's still in escrow
    # 10000 initial - 300 paid out + 0 net in/out = 10000
    assert total_in_system == Decimal(10000)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
