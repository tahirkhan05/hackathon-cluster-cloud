"""
Simple tests for Node Agent Phase 1.

Run with: python test_agent.py
"""
import os
import sys

# Test imports
try:
    from config import AgentConfig
    from hardware import HardwareDiscovery
    print("✅ Module imports successful")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)


def test_config():
    """Test configuration loading."""
    print("\n📋 Testing configuration...")
    
    # Set test environment
    os.environ["CONTROL_PLANE_URL"] = "http://test.example.com"
    os.environ["NODE_AGENT_ID"] = "test-node"
    os.environ["HEARTBEAT_INTERVAL_SECONDS"] = "10"
    
    config = AgentConfig.from_env()
    
    assert config.control_plane_url == "http://test.example.com"
    assert config.provider_id == "test-node"
    assert config.heartbeat_interval_seconds == 10
    
    print("✅ Configuration test passed")


def test_hardware_discovery():
    """Test hardware discovery."""
    print("\n🔍 Testing hardware discovery...")
    
    capabilities = HardwareDiscovery.discover_all()
    
    # Check required fields
    required_fields = ["platform", "hostname"]
    for field in required_fields:
        assert field in capabilities, f"Missing field: {field}"
    
    print(f"✅ Hardware discovery test passed")
    print(f"   Detected: {capabilities.get('hostname')}")
    
    # Show what was detected
    if capabilities.get("ram_total_gb"):
        print(f"   RAM: {capabilities['ram_total_gb']} GB")
    
    if capabilities.get("cpu_cores_logical"):
        print(f"   CPU: {capabilities['cpu_cores_logical']} cores")
    
    if capabilities.get("gpu_count"):
        print(f"   GPU: {capabilities['gpu_count']} device(s)")
    else:
        print(f"   GPU: None detected")


def test_imports():
    """Test all module imports."""
    print("\n📦 Testing module imports...")
    
    try:
        from agent import NodeAgent
        from registration import RegistrationManager
        from heartbeat import HeartbeatManager
        print("✅ All modules import successfully")
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        raise


def main():
    """Run all tests."""
    print("=" * 60)
    print("ClusterCloud Node Agent - Phase 1 Tests")
    print("=" * 60)
    
    try:
        test_imports()
        test_config()
        test_hardware_discovery()
        
        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
