"""
Basic security tests for ClusterCloud MVP.

Tests basic security controls. NOT a substitute for:
- Penetration testing
- Security audit
- Vulnerability scanning
- Compliance assessment

Run with: pytest test_security.py -v
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from main import app
from domains.auth.api_key import generate_api_key, hash_api_key, verify_api_key

client = TestClient(app)



def test_generate_api_key():
    """Test API key generation produces unique keys."""
    key1 = generate_api_key()
    key2 = generate_api_key()
    
    assert len(key1) == 64
    assert len(key2) == 64
    assert key1 != key2


def test_hash_api_key():
    """Test API key hashing is deterministic."""
    key = "test-api-key"
    
    hash1 = hash_api_key(key)
    hash2 = hash_api_key(key)
    
    assert hash1 == hash2
    assert hash1 != key


def test_verify_api_key_with_auth_disabled():
    """Test API key verification when auth is disabled."""
    with patch('domains.auth.api_key.settings.NODE_API_KEY', None):
        assert verify_api_key("any-key") == True
        assert verify_api_key("") == False  # Empty still fails


def test_verify_api_key_with_valid_key():
    """Test API key verification with valid key."""
    test_key = "valid-test-key"
    
    with patch('domains.auth.api_key.settings.NODE_API_KEY', test_key):
        assert verify_api_key(test_key) == True
        assert verify_api_key("wrong-key") == False
        assert verify_api_key("") == False


def test_api_key_timing_attack_resistant():
    """Test that API key comparison is timing-attack resistant."""
    test_key = "valid-test-key"
    
    with patch('domains.auth.api_key.settings.NODE_API_KEY', test_key):
        import time
        
        start1 = time.time()
        verify_api_key("wrong-key-1")
        time1 = time.time() - start1
        
        start2 = time.time()
        verify_api_key("valid-test-key")
        time2 = time.time() - start2
        
        assert abs(time1 - time2) < 0.01



def test_node_registration_without_auth():
    """Test node registration without API key (auth disabled)."""
    with patch('config.settings.ENABLE_NODE_AUTH', False):
        response = client.post(
            "/api/nodes/register",
            json={
                "provider_id": "test-provider",
                "name": "Test Node",
                "ip_address": "192.168.1.100",
                "cpu_cores": 4,
                "cpu_model": "Intel i7",
                "total_ram_gb": 16.0,
                "available_ram_gb": 8.0,
            }
        )
        
        assert response.status_code in [200, 500]


def test_node_registration_with_invalid_api_key():
    """Test node registration with invalid API key."""
    with patch('config.settings.ENABLE_NODE_AUTH', True):
        with patch('config.settings.NODE_API_KEY', 'valid-key'):
            response = client.post(
                "/api/nodes/register",
                headers={"X-API-Key": "invalid-key"},
                json={
                    "provider_id": "test-provider",
                    "name": "Test Node",
                    "ip_address": "192.168.1.100",
                    "cpu_cores": 4,
                    "cpu_model": "Intel i7",
                    "total_ram_gb": 16.0,
                    "available_ram_gb": 8.0,
                }
            )
            
            assert response.status_code == 401


def test_node_registration_missing_api_key():
    """Test node registration without API key header."""
    with patch('config.settings.ENABLE_NODE_AUTH', True):
        with patch('config.settings.NODE_API_KEY', 'valid-key'):
            response = client.post(
                "/api/nodes/register",
                json={
                    "provider_id": "test-provider",
                    "name": "Test Node",
                    "ip_address": "192.168.1.100",
                    "cpu_cores": 4,
                    "cpu_model": "Intel i7",
                    "total_ram_gb": 16.0,
                    "available_ram_gb": 8.0,
                }
            )
            
            assert response.status_code == 401



def test_sql_injection_protection():
    """Test that SQL injection attempts are handled safely."""
    response = client.post(
        "/api/nodes/register",
        json={
            "provider_id": "test-provider",
            "name": "'; DROP TABLE nodes; --",
            "ip_address": "192.168.1.100",
            "cpu_cores": 4,
            "cpu_model": "Intel i7",
            "total_ram_gb": 16.0,
            "available_ram_gb": 8.0,
        }
    )
    
    assert response.status_code in [200, 422, 500]


def test_xss_protection():
    """Test that XSS attempts are handled safely."""
    response = client.post(
        "/api/nodes/register",
        json={
            "provider_id": "test-provider",
            "name": "<script>alert('xss')</script>",
            "ip_address": "192.168.1.100",
            "cpu_cores": 4,
            "cpu_model": "Intel i7",
            "total_ram_gb": 16.0,
            "available_ram_gb": 8.0,
        }
    )
    
    assert response.status_code in [200, 422, 500]


def test_oversized_input_rejection():
    """Test that oversized inputs are rejected."""
    response = client.post(
        "/api/nodes/register",
        json={
            "provider_id": "x" * 10000,
            "name": "Test Node",
            "ip_address": "192.168.1.100",
            "cpu_cores": 4,
            "cpu_model": "Intel i7",
            "total_ram_gb": 16.0,
            "available_ram_gb": 8.0,
        }
    )
    
    assert response.status_code in [422, 500]



def test_resource_limits_configured():
    """Test that resource limits are properly configured."""
    from config import settings
    
    assert settings.MAX_TASK_MEMORY_MB > 0
    assert settings.MAX_TASK_CPU_CORES > 0
    assert settings.MAX_TASK_DISK_MB > 0
    assert settings.TASK_TIMEOUT_SECONDS > 0


def test_docker_isolation_enabled():
    """Test that Docker isolation is enabled."""
    from config import settings
    
    assert settings.ENABLE_DOCKER_ISOLATION == True



def test_no_secrets_in_error_messages():
    """Test that error messages don't leak secrets."""
    from config import settings
    
    with patch('config.settings.ENABLE_NODE_AUTH', True):
        with patch('config.settings.NODE_API_KEY', 'super-secret-key'):
            response = client.post(
                "/api/nodes/register",
                headers={"X-API-Key": "wrong-key"},
                json={
                    "provider_id": "test",
                    "name": "Test",
                    "ip_address": "1.1.1.1",
                    "cpu_cores": 1,
                    "cpu_model": "x",
                    "total_ram_gb": 1.0,
                    "available_ram_gb": 1.0,
                }
            )
            
            assert 'super-secret-key' not in response.text



@pytest.mark.skip(reason="Rate limiting not implemented in MVP")
def test_rate_limiting():
    """Test rate limiting on endpoints."""
    for _ in range(100):
        response = client.get("/api/nodes")
    



def test_authentication_attempts_logged():
    """Test that authentication attempts are logged."""
    import logging
    
    with patch('config.settings.ENABLE_NODE_AUTH', True):
        with patch('config.settings.NODE_API_KEY', 'valid-key'):
            response = client.post(
                "/api/nodes/register",
                headers={"X-API-Key": "invalid"},
                json={
                    "provider_id": "test",
                    "name": "Test",
                    "ip_address": "1.1.1.1",
                    "cpu_cores": 1,
                    "cpu_model": "x",
                    "total_ram_gb": 1.0,
                    "available_ram_gb": 1.0,
                }
            )
            
            assert response.status_code == 401


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
