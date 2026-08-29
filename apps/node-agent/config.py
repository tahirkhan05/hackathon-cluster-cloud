"""
Node Agent Configuration.

All configuration loaded from environment variables.
"""
import os
from typing import Optional
from dataclasses import dataclass


@dataclass
class AgentConfig:
    """Node agent configuration from environment."""
    
    control_plane_url: str
    api_key: str
    
    provider_id: str
    hostname: str
    
    heartbeat_interval_seconds: int
    heartbeat_timeout_seconds: int
    max_heartbeat_failures: int
    
    max_concurrent_tasks: int
    cost_per_task_clstr: float
    
    log_level: str
    
    simulate_failure: bool
    failure_after_seconds: int
    
    @classmethod
    def from_env(cls) -> "AgentConfig":
        """Load configuration from environment variables."""
        return cls(
            control_plane_url=os.getenv("CONTROL_PLANE_URL", "http://localhost:8000"),
            api_key=os.getenv("NODE_AGENT_API_KEY", "dev-node-agent-key"),
            provider_id=os.getenv("NODE_AGENT_ID", os.getenv("COMPUTERNAME", "unknown")),
            hostname=os.getenv("COMPUTERNAME", os.getenv("HOSTNAME", "unknown")),
            heartbeat_interval_seconds=int(os.getenv("HEARTBEAT_INTERVAL_SECONDS", "5")),
            heartbeat_timeout_seconds=int(os.getenv("HEARTBEAT_TIMEOUT_SECONDS", "10")),
            max_heartbeat_failures=int(os.getenv("MAX_HEARTBEAT_FAILURES", "3")),
            max_concurrent_tasks=int(os.getenv("MAX_CONCURRENT_TASKS", "2")),
            cost_per_task_clstr=float(os.getenv("COST_PER_TASK_CLSTR", "10.0")),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            simulate_failure=os.getenv("SIMULATE_FAILURE", "false").lower() == "true",
            failure_after_seconds=int(os.getenv("FAILURE_AFTER_SECONDS", "30"))
        )
