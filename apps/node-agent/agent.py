"""
ClusterCloud Node Agent

Registers with control plane, sends heartbeats, executes tasks.
For hackathon demo - simulates rendering work.
"""
import os
import time
import random
import logging
import requests
from datetime import datetime

# Configuration
CONTROL_PLANE_URL = os.getenv("CONTROL_PLANE_URL", "http://localhost:8000")
NODE_AGENT_ID = os.getenv("NODE_AGENT_ID", f"node-{random.randint(1000, 9999)}")
NODE_AGENT_API_KEY = os.getenv("NODE_AGENT_API_KEY", "dev-node-agent-key")
HEARTBEAT_INTERVAL = int(os.getenv("HEARTBEAT_INTERVAL_SECONDS", "5"))
SIMULATE_FAILURE = os.getenv("SIMULATE_FAILURE", "false").lower() == "true"
FAILURE_AFTER_SECONDS = int(os.getenv("FAILURE_AFTER_SECONDS", "30"))

logging.basicConfig(
    level=logging.INFO,
    format=f"[{NODE_AGENT_ID}] %(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class NodeAgent:
    """Simple node agent for hackathon MVP."""
    
    def __init__(self):
        self.node_id = None
        self.registered = False
        self.start_time = time.time()
        self.tasks_completed = 0
        
    def register(self):
        """Register with control plane."""
        try:
            response = requests.post(
                f"{CONTROL_PLANE_URL}/api/nodes/register",
                json={
                    "provider_id": NODE_AGENT_ID,
                    "hostname": os.getenv("COMPUTERNAME", "unknown"),
                    "capabilities": {
                        "cpu_cores": 4,
                        "ram_gb": 8,
                        "gpu_model": "simulated",
                        "docker_support": True
                    },
                    "max_concurrent_tasks": 2,
                    "cost_per_task_clstr": 10
                },
                headers={"X-Node-Agent-Key": NODE_AGENT_API_KEY},
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                self.node_id = data.get("node_id")
                self.registered = True
                logger.info(f"✅ Registered with control plane: {self.node_id}")
                return True
            else:
                logger.error(f"Registration failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Registration error: {e}")
            return False
    
    def send_heartbeat(self):
        """Send heartbeat to control plane."""
        if not self.node_id:
            return False
            
        try:
            response = requests.post(
                f"{CONTROL_PLANE_URL}/api/nodes/{self.node_id}/heartbeat",
                json={
                    "node_id": self.node_id,
                    "current_task_count": 0,
                    "is_healthy": True
                },
                headers={"X-Node-Agent-Key": NODE_AGENT_API_KEY},
                timeout=5
            )
            
            if response.status_code == 200:
                logger.debug("Heartbeat sent")
                return True
            else:
                logger.warning(f"Heartbeat failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.warning(f"Heartbeat error: {e}")
            return False
    
    def check_for_tasks(self):
        """Check if there are tasks to execute."""
        if not self.node_id:
            return
            
        try:
            response = requests.get(
                f"{CONTROL_PLANE_URL}/api/tasks/next?node_id={self.node_id}",
                headers={"X-Node-Agent-Key": NODE_AGENT_API_KEY},
                timeout=5
            )
            
            if response.status_code == 200:
                task = response.json()
                if task:
                    self.execute_task(task)
                    
        except Exception as e:
            logger.debug(f"Task check: {e}")
    
    def execute_task(self, task):
        """Simulate task execution."""
        task_id = task.get("task_id", "unknown")
        logger.info(f"🎬 Starting task: {task_id}")
        
        # Simulate rendering work
        time.sleep(random.uniform(2, 5))
        
        self.tasks_completed += 1
        logger.info(f"✅ Completed task: {task_id}")
        
        # Report completion
        try:
            requests.post(
                f"{CONTROL_PLANE_URL}/api/tasks/{task_id}/status",
                json={
                    "status": "completed",
                    "result_url": f"s3://results/{task_id}.png"
                },
                headers={"X-Node-Agent-Key": NODE_AGENT_API_KEY},
                timeout=5
            )
        except Exception as e:
            logger.error(f"Failed to report completion: {e}")
    
    def run(self):
        """Main agent loop."""
        logger.info(f"🚀 Starting ClusterCloud Node Agent: {NODE_AGENT_ID}")
        logger.info(f"Control plane: {CONTROL_PLANE_URL}")
        
        if SIMULATE_FAILURE:
            logger.warning(f"⚠️  Will simulate failure after {FAILURE_AFTER_SECONDS}s")
        
        # Register
        while not self.register():
            logger.info("Retrying registration in 5s...")
            time.sleep(5)
        
        # Main loop
        try:
            while True:
                # Check if we should simulate failure
                if SIMULATE_FAILURE:
                    elapsed = time.time() - self.start_time
                    if elapsed > FAILURE_AFTER_SECONDS:
                        logger.error("💥 Simulating node failure - stopping!")
                        break
                
                # Send heartbeat
                self.send_heartbeat()
                
                # Check for tasks (less frequently)
                if int(time.time()) % 10 == 0:
                    self.check_for_tasks()
                
                time.sleep(HEARTBEAT_INTERVAL)
                
        except KeyboardInterrupt:
            logger.info("Shutting down gracefully...")
        except Exception as e:
            logger.error(f"Agent error: {e}")


if __name__ == "__main__":
    agent = NodeAgent()
    agent.run()
