"""
Heartbeat management.

Sends periodic heartbeats to control plane to signal node health.
Tracks consecutive failures and handles recovery.
"""
import time
import logging
from typing import Optional
import requests

from config import AgentConfig

logger = logging.getLogger(__name__)


class HeartbeatManager:
    """Manages heartbeat lifecycle and failure tracking."""
    
    def __init__(self, config: AgentConfig, node_id: str):
        self.config = config
        self.node_id = node_id
        self.consecutive_failures = 0
        self.total_heartbeats_sent = 0
        self.total_heartbeats_failed = 0
        self.last_successful_heartbeat: Optional[float] = None
        self.current_task_count = 0
        self.is_healthy = True
        
    def send_heartbeat(self) -> bool:
        """
        Send heartbeat to control plane.
        
        Returns:
            True if heartbeat succeeded, False otherwise
        """
        try:
            response = requests.post(
                f"{self.config.control_plane_url}/api/nodes/{self.node_id}/heartbeat",
                json={
                    "node_id": self.node_id,
                    "current_task_count": self.current_task_count,
                    "is_healthy": self.is_healthy
                },
                headers={"X-Node-Agent-Key": self.config.api_key},
                timeout=self.config.heartbeat_timeout_seconds
            )
            
            if response.status_code == 200:
                self.consecutive_failures = 0
                self.last_successful_heartbeat = time.time()
                self.total_heartbeats_sent += 1
                
                logger.debug(
                    f"Heartbeat #{self.total_heartbeats_sent} sent successfully"
                )
                return True
                
            else:
                self._handle_failure(f"HTTP {response.status_code}")
                return False
                
        except requests.exceptions.ConnectionError:
            self._handle_failure("connection error")
            return False
            
        except requests.exceptions.Timeout:
            self._handle_failure("timeout")
            return False
            
        except Exception as e:
            self._handle_failure(f"error: {e}")
            return False
    
    def _handle_failure(self, reason: str):
        """Handle heartbeat failure."""
        self.consecutive_failures += 1
        self.total_heartbeats_failed += 1
        
        if self.consecutive_failures >= self.config.max_heartbeat_failures:
            logger.error(
                f"❌ Heartbeat failed {self.consecutive_failures} times "
                f"consecutively ({reason})"
            )
        else:
            logger.warning(
                f"⚠️  Heartbeat failed ({reason}), "
                f"attempt {self.consecutive_failures}/{self.config.max_heartbeat_failures}"
            )
    
    def should_shutdown(self) -> bool:
        """
        Check if node should shutdown due to heartbeat failures.
        
        Returns:
            True if consecutive failures exceed threshold
        """
        return self.consecutive_failures >= self.config.max_heartbeat_failures
    
    def get_stats(self) -> dict:
        """Get heartbeat statistics."""
        return {
            "total_sent": self.total_heartbeats_sent,
            "total_failed": self.total_heartbeats_failed,
            "consecutive_failures": self.consecutive_failures,
            "last_successful": self.last_successful_heartbeat,
            "success_rate": (
                (self.total_heartbeats_sent / 
                 (self.total_heartbeats_sent + self.total_heartbeats_failed))
                if (self.total_heartbeats_sent + self.total_heartbeats_failed) > 0
                else 0
            )
        }
    
    def update_task_count(self, count: int):
        """Update current task count."""
        self.current_task_count = count
    
    def set_health_status(self, is_healthy: bool):
        """Update health status."""
        if self.is_healthy != is_healthy:
            logger.info(f"Health status changed: {is_healthy}")
            self.is_healthy = is_healthy
