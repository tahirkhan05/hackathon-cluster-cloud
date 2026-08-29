"""
ClusterCloud Node Agent - Phase 1

Registers with control plane and maintains heartbeat.
Discovers hardware capabilities and reports system status.

Phase 1 scope:
- Node configuration
- Hardware discovery
- Registration with retry
- Heartbeat lifecycle
- Graceful shutdown
- Structured logging

Phase 2 will add:
- Task execution
- Docker isolation
- Failure simulation
"""
import sys
import signal
import time
import logging
from typing import Optional

from config import AgentConfig
from hardware import HardwareDiscovery
from registration import RegistrationManager
from heartbeat import HeartbeatManager

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class NodeAgent:
    """
    ClusterCloud Node Agent.
    
    Lifecycle:
    1. Load configuration from environment
    2. Discover hardware capabilities
    3. Register with control plane (with retry)
    4. Enter heartbeat loop
    5. Handle graceful shutdown on SIGINT/SIGTERM
    """
    
    def __init__(self):
        self.config: Optional[AgentConfig] = None
        self.capabilities: Optional[dict] = None
        self.registration_manager: Optional[RegistrationManager] = None
        self.heartbeat_manager: Optional[HeartbeatManager] = None
        self.running = False
        self.start_time: Optional[float] = None
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self.running = False
    
    def initialize(self) -> bool:
        """
        Initialize agent configuration and hardware discovery.
        
        Returns:
            True if initialization succeeded
        """
        logger.info("🚀 ClusterCloud Node Agent - Phase 1")
        logger.info("=" * 60)
        
        # Load configuration
        try:
            self.config = AgentConfig.from_env()
            logger.info("Configuration loaded:")
            logger.info(f"  Control Plane: {self.config.control_plane_url}")
            logger.info(f"  Provider ID: {self.config.provider_id}")
            logger.info(f"  Heartbeat Interval: {self.config.heartbeat_interval_seconds}s")
            logger.info(f"  Max Concurrent Tasks: {self.config.max_concurrent_tasks}")
            
            # Set log level
            logging.getLogger().setLevel(self.config.log_level)
            
        except Exception as e:
            logger.error(f"Configuration error: {e}")
            return False
        
        # Discover hardware
        logger.info("=" * 60)
        try:
            self.capabilities = HardwareDiscovery.discover_all()
            logger.info("Hardware discovery complete")
            
        except Exception as e:
            logger.error(f"Hardware discovery error: {e}")
            return False
        
        logger.info("=" * 60)
        return True
    
    def register(self) -> bool:
        """
        Register with control plane.
        
        Returns:
            True if registration succeeded
        """
        logger.info("Registering with control plane...")
        
        self.registration_manager = RegistrationManager(
            self.config,
            self.capabilities
        )
        
        if not self.registration_manager.register():
            logger.error("Failed to register with control plane")
            return False
        
        # Create heartbeat manager
        node_id = self.registration_manager.get_node_id()
        self.heartbeat_manager = HeartbeatManager(self.config, node_id)
        
        return True
    
    def run_heartbeat_loop(self):
        """
        Main heartbeat loop.
        
        Sends periodic heartbeats and monitors for failures.
        Handles demo failure simulation if configured.
        """
        logger.info("=" * 60)
        logger.info("Entering heartbeat loop")
        logger.info(f"Heartbeat interval: {self.config.heartbeat_interval_seconds}s")
        
        if self.config.simulate_failure:
            logger.warning(
                f"⚠️  DEMO MODE: Will simulate failure after "
                f"{self.config.failure_after_seconds}s"
            )
        
        logger.info("=" * 60)
        
        self.running = True
        self.start_time = time.time()
        next_heartbeat = time.time()
        
        try:
            while self.running:
                current_time = time.time()
                
                # Check if it's time for a heartbeat
                if current_time >= next_heartbeat:
                    success = self.heartbeat_manager.send_heartbeat()
                    
                    # Check if we should shutdown due to failures
                    if self.heartbeat_manager.should_shutdown():
                        logger.error(
                            "Too many consecutive heartbeat failures, shutting down"
                        )
                        break
                    
                    next_heartbeat = current_time + self.config.heartbeat_interval_seconds
                
                # Demo: simulate failure after configured time
                if self.config.simulate_failure:
                    elapsed = current_time - self.start_time
                    if elapsed >= self.config.failure_after_seconds:
                        logger.error(
                            f"💥 DEMO MODE: Simulating node failure after "
                            f"{elapsed:.1f}s"
                        )
                        break
                
                # Sleep briefly to avoid tight loop
                time.sleep(0.1)
                
        except Exception as e:
            logger.error(f"Error in heartbeat loop: {e}", exc_info=True)
    
    def shutdown(self):
        """Perform graceful shutdown."""
        logger.info("=" * 60)
        logger.info("Shutting down node agent")
        
        if self.heartbeat_manager:
            stats = self.heartbeat_manager.get_stats()
            logger.info(f"Heartbeat statistics:")
            logger.info(f"  Total sent: {stats['total_sent']}")
            logger.info(f"  Total failed: {stats['total_failed']}")
            logger.info(f"  Success rate: {stats['success_rate']:.2%}")
        
        if self.start_time:
            uptime = time.time() - self.start_time
            logger.info(f"Uptime: {uptime:.1f}s")
        
        logger.info("=" * 60)
        logger.info("Node agent stopped")
    
    def run(self) -> int:
        """
        Main entry point.
        
        Returns:
            Exit code (0 for success, non-zero for error)
        """
        try:
            # Initialize
            if not self.initialize():
                return 1
            
            # Register
            if not self.register():
                return 1
            
            # Run heartbeat loop
            self.run_heartbeat_loop()
            
            # Graceful shutdown
            self.shutdown()
            
            return 0
            
        except Exception as e:
            logger.error(f"Fatal error: {e}", exc_info=True)
            return 1


def main():
    """Entry point."""
    agent = NodeAgent()
    exit_code = agent.run()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
