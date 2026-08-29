"""
Tests for AI Agents - Phase 8

Tests validation logic and fallback behavior.
Run with: pytest test_ai_agents.py -v
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Base
from domains.ai.workload_agent import WorkloadAnalysisAgent
from domains.ai.provider_agent import ProviderRecommendationAgent
from domains.ai.recovery_agent import RecoveryAgent

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_ai_agents.db"
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
# WORKLOAD AGENT TESTS
# ============================================================================

def test_workload_agent_deterministic_fallback():
    """Test workload agent fallback without AI."""
    db = next(get_test_db())
    
    agent = WorkloadAnalysisAgent(db)
    
    # Simulate context
    context = agent.gather_context(
        workload_type="frame_rendering",
        parameters={
            "frame_count": 100,
            "width": 1920,
            "height": 1080,
            "complexity": "medium"
        },
        customer_budget=5000
    )
    
    # Get fallback recommendation
    recommendation = agent.deterministic_fallback(context)
    
    # Verify structure
    assert "cpu_cores_min" in recommendation
    assert "ram_gb_min" in recommendation
    assert "gpu_required" in recommendation
    assert "estimated_task_duration_seconds" in recommendation
    assert recommendation["fallback"] == True
    
    # Verify reasonable values
    assert recommendation["cpu_cores_min"] >= 2
    assert recommendation["ram_gb_min"] >= 4
    assert recommendation["suggested_task_count"] == 100


def test_workload_agent_validation_success():
    """Test validation accepts valid recommendation."""
    db = next(get_test_db())
    
    agent = WorkloadAnalysisAgent(db)
    
    context = {
        "workload_type": "frame_rendering",
        "parameters": {"frame_count": 100},
        "customer_budget": 5000
    }
    
    valid_recommendation = {
        "cpu_cores_min": 4,
        "ram_gb_min": 8,
        "gpu_required": False,
        "gpu_vram_gb_min": None,
        "estimated_total_cost_clstr": 3000,
        "parallelization_recommended": True,
        "suggested_task_count": 100
    }
    
    is_valid, result, errors = agent.validate_recommendation(
        valid_recommendation, context
    )
    
    assert is_valid == True
    assert errors is None


def test_workload_agent_validation_missing_fields():
    """Test validation rejects incomplete recommendation."""
    db = next(get_test_db())
    
    agent = WorkloadAnalysisAgent(db)
    
    context = {"customer_budget": 5000}
    
    incomplete_recommendation = {
        "cpu_cores_min": 4
        # Missing other required fields
    }
    
    is_valid, result, errors = agent.validate_recommendation(
        incomplete_recommendation, context
    )
    
    assert is_valid == False
    assert errors is not None
    assert len(errors) > 0


def test_workload_agent_validation_exceeds_budget():
    """Test validation rejects over-budget recommendation."""
    db = next(get_test_db())
    
    agent = WorkloadAnalysisAgent(db)
    
    context = {"customer_budget": 1000}
    
    expensive_recommendation = {
        "cpu_cores_min": 4,
        "ram_gb_min": 8,
        "gpu_required": False,
        "estimated_total_cost_clstr": 5000  # 5x budget
    }
    
    is_valid, result, errors = agent.validate_recommendation(
        expensive_recommendation, context
    )
    
    assert is_valid == False
    assert any("budget" in str(e).lower() for e in errors)


# ============================================================================
# PROVIDER AGENT TESTS
# ============================================================================

def test_provider_agent_deterministic_fallback():
    """Test provider agent selects node deterministically."""
    db = next(get_test_db())
    
    agent = ProviderRecommendationAgent(db)
    
    # Mock candidate nodes
    candidates = [
        {
            "node_id": "node-1",
            "provider_id": "provider-1",
            "reliability_score": 0.95,
            "cost_per_task_clstr": 10,
            "available_capacity": 3,
            "failure_count": 0
        },
        {
            "node_id": "node-2",
            "provider_id": "provider-2",
            "reliability_score": 0.85,
            "cost_per_task_clstr": 5,
            "available_capacity": 2,
            "failure_count": 1
        },
        {
            "node_id": "node-3",
            "provider_id": "provider-3",
            "reliability_score": 0.90,
            "cost_per_task_clstr": 8,
            "available_capacity": 4,
            "failure_count": 0
        }
    ]
    
    context = {"candidate_nodes": candidates, "requirements": {}}
    
    recommendation = agent.deterministic_fallback(context)
    
    # Should select based on scoring
    assert "node_id" in recommendation
    assert "provider_id" in recommendation
    assert recommendation["fallback"] == True
    
    # node-1 should win (highest reliability + good capacity)
    assert recommendation["node_id"] == "node-1"


def test_provider_agent_validation_node_in_list():
    """Test validation accepts node from candidate list."""
    db = next(get_test_db())
    
    agent = ProviderRecommendationAgent(db)
    
    candidates = [
        {"node_id": "node-abc123", "provider_id": "prov-1"}
    ]
    
    context = {"candidate_nodes": candidates}
    
    recommendation = {
        "node_id": "node-abc",  # Partial match OK
        "provider_id": "prov-1"
    }
    
    is_valid, result, errors = agent.validate_recommendation(
        recommendation, context
    )
    
    assert is_valid == True


def test_provider_agent_validation_node_not_in_list():
    """Test validation rejects node not in candidates."""
    db = next(get_test_db())
    
    agent = ProviderRecommendationAgent(db)
    
    candidates = [
        {"node_id": "node-123", "provider_id": "prov-1"}
    ]
    
    context = {"candidate_nodes": candidates}
    
    recommendation = {
        "node_id": "node-999",  # Not in list
        "provider_id": "prov-999"
    }
    
    is_valid, result, errors = agent.validate_recommendation(
        recommendation, context
    )
    
    assert is_valid == False
    assert errors is not None


# ============================================================================
# RECOVERY AGENT TESTS
# ============================================================================

def test_recovery_agent_deterministic_fallback_urgent():
    """Test recovery agent chooses immediate reassign when urgent."""
    db = next(get_test_db())
    
    agent = RecoveryAgent(db)
    
    # Urgent scenario: many tasks, deadline pressure
    context = {
        "incident": {"severity": "HIGH"},
        "affected_tasks_count": 15,
        "available_nodes_count": 5,
        "has_deadline_pressure": True
    }
    
    recommendation = agent.deterministic_fallback(context)
    
    assert recommendation["strategy"] == "immediate_reassign"
    assert recommendation["priority"] == "high"
    assert recommendation["should_notify_customer"] == True


def test_recovery_agent_deterministic_fallback_wait():
    """Test recovery agent waits when appropriate."""
    db = next(get_test_db())
    
    agent = RecoveryAgent(db)
    
    # Low urgency: few tasks, no deadline
    context = {
        "incident": {"severity": "MEDIUM"},
        "affected_tasks_count": 2,
        "available_nodes_count": 5,
        "has_deadline_pressure": False
    }
    
    recommendation = agent.deterministic_fallback(context)
    
    assert recommendation["strategy"] == "wait_for_recovery"
    assert recommendation["priority"] == "low"
    assert recommendation["should_notify_customer"] == False
    assert recommendation["max_wait_seconds"] is not None


def test_recovery_agent_validation_invalid_strategy():
    """Test validation rejects invalid strategy."""
    db = next(get_test_db())
    
    agent = RecoveryAgent(db)
    
    context = {"available_nodes_count": 5}
    
    invalid_recommendation = {
        "strategy": "do_nothing",  # Invalid
        "priority": "medium"
    }
    
    is_valid, result, errors = agent.validate_recommendation(
        invalid_recommendation, context
    )
    
    assert is_valid == False
    assert any("strategy" in str(e).lower() for e in errors)


def test_recovery_agent_validation_impossible_reassign():
    """Test validation rejects reassignment with no nodes."""
    db = next(get_test_db())
    
    agent = RecoveryAgent(db)
    
    context = {"available_nodes_count": 0}
    
    impossible_recommendation = {
        "strategy": "immediate_reassign",  # But no nodes!
        "priority": "high",
        "should_notify_customer": True
    }
    
    is_valid, result, errors = agent.validate_recommendation(
        impossible_recommendation, context
    )
    
    assert is_valid == False
    assert any("no available nodes" in str(e).lower() for e in errors)


# ============================================================================
# FALLBACK BEHAVIOR TESTS
# ============================================================================

def test_agents_work_without_bedrock():
    """Test all agents function without Bedrock available."""
    db = next(get_test_db())
    
    # All agents should work in fallback mode
    workload_agent = WorkloadAnalysisAgent(db)
    provider_agent = ProviderRecommendationAgent(db)
    recovery_agent = RecoveryAgent(db)
    
    # Workload agent
    workload_rec, workload_record = workload_agent.recommend(
        request_context_id="test-job",
        request_context_type="job",
        workload_type="frame_rendering",
        parameters={"frame_count": 10},
        customer_budget=1000
    )
    
    assert workload_rec is not None
    assert "cpu_cores_min" in workload_rec
    assert workload_record.action_taken == "fallback"
    
    # Provider agent
    provider_rec, provider_record = provider_agent.recommend(
        request_context_id="test-task",
        request_context_type="task",
        candidate_nodes=[{
            "node_id": "node-1",
            "provider_id": "prov-1",
            "reliability_score": 0.9,
            "cost_per_task_clstr": 10,
            "available_capacity": 2
        }],
        requirements={}
    )
    
    assert provider_rec is not None
    assert "node_id" in provider_rec
    assert provider_record.action_taken == "fallback"
    
    # Recovery agent
    recovery_rec, recovery_record = recovery_agent.recommend(
        request_context_id="test-incident",
        request_context_type="incident",
        incident_data={"severity": "HIGH"},
        affected_tasks=[],
        available_nodes_count=5
    )
    
    assert recovery_rec is not None
    assert "strategy" in recovery_rec
    assert recovery_record.action_taken == "fallback"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
