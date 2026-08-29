"""
Tests for Node Registration and Heartbeat - Phase 2

Run with: pytest test_nodes.py -v
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta

from main import app
from database import Base, get_db
from domains.nodes.models import Node, NodeStatus
from domains.nodes.service import NodeService

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    """Create test database before each test."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def test_health_endpoint():
    """Test basic health check."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_node_registration():
    """Test successful node registration."""
    response = client.post(
        "/api/nodes/register",
        json={
            "provider_id": "test-node-01",
            "hostname": "test-machine",
            "ip_address": "192.168.1.100",
            "capabilities": {
                "cpu_cores": 8,
                "ram_gb": 16,
                "gpu_available": False
            },
            "max_concurrent_tasks": 2,
            "cost_per_task_clstr": 10
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "node_id" in data
    assert data["provider_id"] == "test-node-01"
    assert data["hostname"] == "test-machine"
    assert data["status"] == "available"
    assert data["is_healthy"] == True
    assert data["capabilities"]["cpu_cores"] == 8


def test_duplicate_node_registration():
    """Test registering same provider_id twice (should reactivate)."""
    # First registration
    response1 = client.post(
        "/api/nodes/register",
        json={
            "provider_id": "test-node-02",
            "hostname": "machine-a",
            "capabilities": {"cpu_cores": 4},
            "max_concurrent_tasks": 2,
            "cost_per_task_clstr": 10
        }
    )
    assert response1.status_code == 200
    node_id_1 = response1.json()["node_id"]
    
    # Second registration with same provider_id
    response2 = client.post(
        "/api/nodes/register",
        json={
            "provider_id": "test-node-02",  # Same provider_id
            "hostname": "machine-b",  # Different hostname
            "capabilities": {"cpu_cores": 8},  # Different capabilities
            "max_concurrent_tasks": 4,
            "cost_per_task_clstr": 15
        }
    )
    assert response2.status_code == 200
    node_id_2 = response2.json()["node_id"]
    
    # Should be same node ID (reactivation)
    assert node_id_1 == node_id_2
    
    # Should have updated capabilities
    assert response2.json()["capabilities"]["cpu_cores"] == 8
    assert response2.json()["max_concurrent_tasks"] == 4


def test_heartbeat():
    """Test heartbeat updates node status."""
    # Register node
    reg_response = client.post(
        "/api/nodes/register",
        json={
            "provider_id": "test-node-03",
            "capabilities": {"cpu_cores": 4},
            "max_concurrent_tasks": 2,
            "cost_per_task_clstr": 10
        }
    )
    node_id = reg_response.json()["node_id"]
    
    # Send heartbeat
    hb_response = client.post(
        f"/api/nodes/{node_id}/heartbeat",
        json={
            "node_id": node_id,
            "current_task_count": 0,
            "is_healthy": True
        }
    )
    
    assert hb_response.status_code == 200
    assert hb_response.json()["status"] == "ok"
    assert hb_response.json()["node_status"] == "available"


def test_heartbeat_nonexistent_node():
    """Test heartbeat for non-existent node."""
    response = client.post(
        "/api/nodes/fake-node-id/heartbeat",
        json={
            "node_id": "fake-node-id",
            "current_task_count": 0,
            "is_healthy": True
        }
    )
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_heartbeat_capacity_full():
    """Test node becomes BUSY when at capacity."""
    # Register node with max 2 tasks
    reg_response = client.post(
        "/api/nodes/register",
        json={
            "provider_id": "test-node-04",
            "capabilities": {"cpu_cores": 2},
            "max_concurrent_tasks": 2,
            "cost_per_task_clstr": 10
        }
    )
    node_id = reg_response.json()["node_id"]
    
    # Heartbeat with 2 tasks (at capacity)
    hb_response = client.post(
        f"/api/nodes/{node_id}/heartbeat",
        json={
            "node_id": node_id,
            "current_task_count": 2,
            "is_healthy": True
        }
    )
    
    assert hb_response.json()["node_status"] == "busy"
    assert hb_response.json()["is_available"] == False


def test_heartbeat_unhealthy():
    """Test node becomes OFFLINE when unhealthy."""
    # Register node
    reg_response = client.post(
        "/api/nodes/register",
        json={
            "provider_id": "test-node-05",
            "capabilities": {"cpu_cores": 4},
            "max_concurrent_tasks": 2,
            "cost_per_task_clstr": 10
        }
    )
    node_id = reg_response.json()["node_id"]
    
    # Heartbeat with unhealthy status
    hb_response = client.post(
        f"/api/nodes/{node_id}/heartbeat",
        json={
            "node_id": node_id,
            "current_task_count": 0,
            "is_healthy": False
        }
    )
    
    assert hb_response.json()["node_status"] == "offline"


def test_list_nodes():
    """Test listing all nodes."""
    # Register multiple nodes
    for i in range(3):
        client.post(
            "/api/nodes/register",
            json={
                "provider_id": f"test-node-{i}",
                "capabilities": {"cpu_cores": 4},
                "max_concurrent_tasks": 2,
                "cost_per_task_clstr": 10
            }
        )
    
    # List all nodes
    response = client.get("/api/nodes/")
    assert response.status_code == 200
    
    data = response.json()
    assert data["total"] == 3
    assert len(data["nodes"]) == 3


def test_list_nodes_filter_by_status():
    """Test filtering nodes by status."""
    # Register node
    reg_response = client.post(
        "/api/nodes/register",
        json={
            "provider_id": "test-node-filter",
            "capabilities": {"cpu_cores": 4},
            "max_concurrent_tasks": 2,
            "cost_per_task_clstr": 10
        }
    )
    node_id = reg_response.json()["node_id"]
    
    # Make it busy
    client.post(
        f"/api/nodes/{node_id}/heartbeat",
        json={
            "node_id": node_id,
            "current_task_count": 2,
            "is_healthy": True
        }
    )
    
    # Filter by busy status
    response = client.get("/api/nodes/?status=busy")
    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["nodes"][0]["status"] == "busy"


def test_get_node():
    """Test getting specific node details."""
    # Register node
    reg_response = client.post(
        "/api/nodes/register",
        json={
            "provider_id": "test-node-detail",
            "hostname": "detail-machine",
            "capabilities": {"cpu_cores": 8},
            "max_concurrent_tasks": 4,
            "cost_per_task_clstr": 15
        }
    )
    node_id = reg_response.json()["node_id"]
    
    # Get node details
    response = client.get(f"/api/nodes/{node_id}")
    assert response.status_code == 200
    
    data = response.json()
    assert data["node_id"] == node_id
    assert data["hostname"] == "detail-machine"
    assert data["capabilities"]["cpu_cores"] == 8


def test_get_nonexistent_node():
    """Test getting non-existent node returns 404."""
    response = client.get("/api/nodes/fake-id")
    assert response.status_code == 404


def test_node_statistics():
    """Test node statistics endpoint."""
    # Register nodes with different states
    for i in range(5):
        client.post(
            "/api/nodes/register",
            json={
                "provider_id": f"stats-node-{i}",
                "capabilities": {"cpu_cores": 4},
                "max_concurrent_tasks": 2,
                "cost_per_task_clstr": 10
            }
        )
    
    # Get statistics
    response = client.get("/api/nodes/statistics")
    assert response.status_code == 200
    
    stats = response.json()
    assert stats["total_nodes"] == 5
    assert stats["available"] >= 0
    assert stats["busy"] >= 0
    assert stats["offline"] >= 0


def test_stale_node_detection():
    """Test stale node detection service."""
    db = next(override_get_db())
    
    # Register node
    reg_response = client.post(
        "/api/nodes/register",
        json={
            "provider_id": "stale-test-node",
            "capabilities": {"cpu_cores": 4},
            "max_concurrent_tasks": 2,
            "cost_per_task_clstr": 10
        }
    )
    node_id = reg_response.json()["node_id"]
    
    # Get node and manually set old heartbeat
    node = db.query(Node).filter(Node.node_id == node_id).first()
    node.last_heartbeat = datetime.utcnow() - timedelta(seconds=60)
    db.commit()
    
    # Detect stale nodes (20 second timeout)
    stale_nodes = NodeService.detect_stale_nodes(db, timeout_seconds=20)
    assert len(stale_nodes) == 1
    assert stale_nodes[0].node_id == node_id


def test_mark_stale_nodes_offline():
    """Test marking stale nodes as offline."""
    db = next(override_get_db())
    
    # Register node
    reg_response = client.post(
        "/api/nodes/register",
        json={
            "provider_id": "mark-stale-node",
            "capabilities": {"cpu_cores": 4},
            "max_concurrent_tasks": 2,
            "cost_per_task_clstr": 10
        }
    )
    node_id = reg_response.json()["node_id"]
    
    # Make heartbeat old
    node = db.query(Node).filter(Node.node_id == node_id).first()
    node.last_heartbeat = datetime.utcnow() - timedelta(seconds=60)
    db.commit()
    
    # Mark stale nodes offline
    count = NodeService.mark_stale_nodes_offline(db, timeout_seconds=20)
    assert count == 1
    
    # Verify node is offline
    db.refresh(node)
    assert node.status == NodeStatus.OFFLINE
    assert node.is_healthy == False


def test_invalid_registration_missing_fields():
    """Test registration with missing required fields."""
    response = client.post(
        "/api/nodes/register",
        json={
            "provider_id": "incomplete-node"
            # Missing capabilities and other required fields
        }
    )
    assert response.status_code == 422  # Validation error


def test_invalid_heartbeat_payload():
    """Test heartbeat with invalid payload."""
    # Register valid node first
    reg_response = client.post(
        "/api/nodes/register",
        json={
            "provider_id": "test-node-invalid-hb",
            "capabilities": {"cpu_cores": 4},
            "max_concurrent_tasks": 2,
            "cost_per_task_clstr": 10
        }
    )
    node_id = reg_response.json()["node_id"]
    
    # Send invalid heartbeat
    response = client.post(
        f"/api/nodes/{node_id}/heartbeat",
        json={
            "invalid_field": "value"
            # Missing required fields
        }
    )
    assert response.status_code == 422  # Validation error


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
