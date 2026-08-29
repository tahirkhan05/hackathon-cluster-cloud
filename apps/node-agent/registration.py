"""
Node registration with control plane.

Handles initial registration and re-registration with retry logic.
"""
import time
import logging
from typing import Optional, Dict, Any
import requests

from config import AgentConfig

logger = logging.getLogger(__name__)


class RegistrationManager:
    """Manages node registration with the control plane."""
    
    def __init__(self, config: AgentConfig, capabilities: Dict[str, Any]):
        self.config = config
        self.capabilities = capabilities
        self.node_id: Optional[str] = None
        self.registered = False
        
    def register(self, max_retries: int = 10, retry_delay: int = 5) -> bool:
        """
        Register node with control plane.
        
        Retries on failure with exponential backoff.
        
        Args:
            max_retries: Maximum number of registration attempts
            retry_delay: Initial delay between retries (seconds)
            
        Returns:
            True if registration succeeded, False otherwise
        """
        attempt = 0
        
        while attempt < max_retries:
            attempt += 1
            
            try:
                logger.info(f"Registration attempt {attempt}/{max_retries}...")
                
                response = requests.post(
                    f"{self.config.control_plane_url}/api/nodes/register",
                    json={
                        "provider_id": self.config.provider_id,
                        "hostname": self.capabilities.get("hostname"),
                        "ip_address": self.capabilities.get("ip_address"),
                        "capabilities": self.capabilities,
                        "max_concurrent_tasks": self.config.max_concurrent_tasks,
                        "cost_per_task_clstr": self.config.cost_per_task_clstr
                    },
                    headers={"X-Node-Agent-Key": self.config.api_key},
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self.node_id = data.get("node_id")
                    self.registered = True
                    
                    logger.info(f"✅ Successfully registered with control plane")
                    logger.info(f"Node ID: {self.node_id}")
                    logger.info(f"Provider ID: {self.config.provider_id}")
                    
                    return True
                    
                else:
                    logger.warning(
                        f"Registration failed with status {response.status_code}: "
                        f"{response.text[:200]}"
                    )
                    
            except requests.exceptions.ConnectionError as e:
                logger.warning(f"Control plane unreachable: {e}")
                
            except requests.exceptions.Timeout:
                logger.warning("Registration request timed out")
                
            except Exception as e:
                logger.error(f"Registration error: {e}", exc_info=True)
            
            # Wait before retry with exponential backoff
            if attempt < max_retries:
                delay = retry_delay * (2 ** (attempt - 1))
                logger.info(f"Retrying in {delay}s...")
                time.sleep(delay)
        
        logger.error("❌ Registration failed after all retries")
        return False
    
    def is_registered(self) -> bool:
        """Check if node is currently registered."""
        return self.registered and self.node_id is not None
    
    def get_node_id(self) -> Optional[str]:
        """Get the assigned node ID."""
        return self.node_id
