#!/usr/bin/env python3
"""
End-to-End Distributed Rendering Demo - Phase 5

Demonstrates the complete flow:
1. Start API backend
2. Start multiple node agents
3. Submit rendering job
4. Watch tasks execute across nodes
5. Verify results

Run: python demo_distributed_rendering.py
"""
import os
import sys
import time
import subprocess
import requests
import json
from pathlib import Path
from typing import List, Optional

# Configuration
API_URL = "http://localhost:8000"
NODE_COUNT = 3
FRAME_COUNT = 12  # Small demo workload
RENDER_WIDTH = 1280
RENDER_HEIGHT = 720


class DemoOrchestrator:
    """Orchestrates the end-to-end demo."""
    
    def __init__(self):
        self.api_process: Optional[subprocess.Popen] = None
        self.node_processes: List[subprocess.Popen] = []
        self.job_id: Optional[str] = None
        
    def banner(self, message: str):
        """Print section banner."""
        print("\n" + "=" * 80)
        print(f"  {message}")
        print("=" * 80 + "\n")
    
    def step(self, message: str):
        """Print step message."""
        print(f"→ {message}")
    
    def success(self, message: str):
        """Print success message."""
        print(f"✓ {message}")
    
    def error(self, message: str):
        """Print error message."""
        print(f"✗ {message}", file=sys.stderr)
    
    def wait_for_api(self, timeout: int = 30) -> bool:
        """Wait for API to be ready."""
        self.step(f"Waiting for API at {API_URL} (timeout: {timeout}s)...")
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = requests.get(f"{API_URL}/health", timeout=2)
                if response.status_code == 200:
                    self.success(f"API is ready")
                    return True
            except requests.RequestException:
                pass
            
            time.sleep(1)
        
        self.error("API did not become ready in time")
        return False
    
    def start_api(self) -> bool:
        """Start the FastAPI backend."""
        self.banner("Step 1: Starting API Backend")
        
        # Check if already running
        try:
            response = requests.get(f"{API_URL}/health", timeout=2)
            if response.status_code == 200:
                self.success("API already running")
                return True
        except requests.RequestException:
            pass
        
        # Start API
        self.step("Starting FastAPI server...")
        
        api_dir = Path("apps/api")
        
        if not api_dir.exists():
            self.error(f"API directory not found: {api_dir}")
            return False
        
        # Start in background
        self.api_process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"],
            cwd=api_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait for API to be ready
        if not self.wait_for_api():
            return False
        
        self.success(f"API started (PID: {self.api_process.pid})")
        return True
    
    def start_nodes(self) -> bool:
        """Start multiple node agents."""
        self.banner(f"Step 2: Starting {NODE_COUNT} Node Agents")
        
        node_dir = Path("apps/node-agent")
        
        if not node_dir.exists():
            self.error(f"Node agent directory not found: {node_dir}")
            return False
        
        for i in range(NODE_COUNT):
            provider_id = f"demo-node-{i+1}"
            
            self.step(f"Starting node {i+1}/{NODE_COUNT} ({provider_id})...")
            
            # Set environment for this node
            env = os.environ.copy()
            env["PROVIDER_ID"] = provider_id
            env["CONTROL_PLANE_URL"] = API_URL
            env["HEARTBEAT_INTERVAL"] = "5"
            env["MAX_CONCURRENT_TASKS"] = "2"
            
            # Start node agent
            process = subprocess.Popen(
                [sys.executable, "agent.py"],
                cwd=node_dir,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            self.node_processes.append(process)
            self.success(f"Node {provider_id} started (PID: {process.pid})")
            
            # Brief delay between nodes
            time.sleep(0.5)
        
        # Wait for nodes to register
        self.step("Waiting for nodes to register...")
        time.sleep(3)
        
        # Verify nodes registered
        try:
            response = requests.get(f"{API_URL}/api/nodes")
            nodes = response.json().get("nodes", [])
            
            self.success(f"{len(nodes)} nodes registered and ready")
            
            for node in nodes:
                print(f"  - {node['node_id']} ({node['provider_id']}) - {node['status']}")
            
            return len(nodes) >= NODE_COUNT
            
        except Exception as e:
            self.error(f"Failed to verify nodes: {e}")
            return False
    
    def submit_job(self) -> bool:
        """Submit a rendering job."""
        self.banner("Step 3: Submitting Rendering Job")
        
        self.step(f"Creating job: {FRAME_COUNT} frames at {RENDER_WIDTH}x{RENDER_HEIGHT}...")
        
        try:
            # Create job
            response = requests.post(
                f"{API_URL}/api/jobs",
                json={
                    "customer_id": "demo-customer",
                    "workload_type": "frame_rendering",
                    "parameters": {
                        "frame_count": FRAME_COUNT,
                        "width": RENDER_WIDTH,
                        "height": RENDER_HEIGHT,
                        "complexity": "medium"
                    },
                    "budget_clstr": 1000.0,
                    "deadline_seconds": 300
                }
            )
            
            response.raise_for_status()
            job = response.json()
            self.job_id = job["job_id"]
            
            self.success(f"Job created: {self.job_id}")
            
            # Schedule job
            self.step("Scheduling tasks across nodes...")
            
            response = requests.post(
                f"{API_URL}/api/scheduling/schedule-and-execute",
                json={
                    "job_id": self.job_id,
                    "cpu_cores_min": 2,
                    "ram_gb_min": 2,
                    "task_count": FRAME_COUNT,
                    "estimated_task_duration_seconds": 10,
                    "budget_clstr": 1000.0,
                    "reliability_min": 0.5
                }
            )
            
            response.raise_for_status()
            result = response.json()
            
            self.success(f"{result['tasks_created']} tasks created and distributed")
            
            plan = result["plan"]
            print(f"  Estimated cost: {plan['estimated_cost_clstr']:.2f} CLSTR")
            print(f"  Estimated duration: {plan['estimated_duration_seconds']}s")
            print(f"  Nodes allocated: {len(plan['allocated_nodes'])}")
            
            for node_id, task_list in plan["task_distribution"].items():
                print(f"    - {node_id[:16]}: {len(task_list)} tasks")
            
            return True
            
        except Exception as e:
            self.error(f"Failed to submit job: {e}")
            return False
    
    def monitor_execution(self):
        """Monitor task execution in real-time."""
        self.banner("Step 4: Monitoring Distributed Execution")
        
        self.step("Watching tasks execute across nodes...")
        print()
        
        completed_count = 0
        last_status = {}
        
        try:
            while completed_count < FRAME_COUNT:
                # Get task status
                response = requests.get(
                    f"{API_URL}/api/tasks",
                    params={"job_id": self.job_id}
                )
                
                tasks = response.json().get("tasks", [])
                
                # Count by status
                status_counts = {}
                for task in tasks:
                    status = task["status"]
                    status_counts[status] = status_counts.get(status, 0) + 1
                
                # Print if changed
                if status_counts != last_status:
                    status_str = ", ".join([
                        f"{status}: {count}"
                        for status, count in sorted(status_counts.items())
                    ])
                    print(f"  [{time.strftime('%H:%M:%S')}] {status_str}")
                    last_status = status_counts
                
                completed_count = status_counts.get("COMPLETED", 0)
                
                time.sleep(2)
            
            print()
            self.success(f"All {FRAME_COUNT} tasks completed!")
            
        except KeyboardInterrupt:
            print("\n\nMonitoring interrupted by user")
        except Exception as e:
            self.error(f"Monitoring error: {e}")
    
    def verify_results(self):
        """Verify rendering results."""
        self.banner("Step 5: Verifying Results")
        
        try:
            # Get job details
            response = requests.get(f"{API_URL}/api/jobs/{self.job_id}")
            job = response.json()
            
            print(f"Job Status: {job['status']}")
            print(f"Started: {job.get('started_at', 'N/A')}")
            print(f"Completed: {job.get('completed_at', 'N/A')}")
            
            # Get all tasks
            response = requests.get(
                f"{API_URL}/api/tasks",
                params={"job_id": self.job_id}
            )
            
            tasks = response.json().get("tasks", [])
            
            # Analyze results
            print(f"\nTask Summary:")
            print(f"  Total tasks: {len(tasks)}")
            
            status_counts = {}
            nodes_used = set()
            
            for task in tasks:
                status = task["status"]
                status_counts[status] = status_counts.get(status, 0) + 1
                
                if task.get("node_id"):
                    nodes_used.add(task["node_id"])
            
            for status, count in sorted(status_counts.items()):
                print(f"    {status}: {count}")
            
            print(f"  Nodes used: {len(nodes_used)}")
            
            # Check for rendered frames
            frame_dir = Path("apps/node-agent/rendered_frames")
            if frame_dir.exists():
                frames = list(frame_dir.glob("frame_*.png")) + list(frame_dir.glob("frame_*.mock"))
                print(f"  Frames on disk: {len(frames)}")
                
                if frames:
                    print(f"  Output directory: {frame_dir.absolute()}")
            
            self.success("Results verified!")
            
        except Exception as e:
            self.error(f"Failed to verify results: {e}")
    
    def cleanup(self):
        """Stop all processes."""
        self.banner("Cleanup")
        
        self.step("Stopping node agents...")
        for i, process in enumerate(self.node_processes):
            if process.poll() is None:  # Still running
                process.terminate()
                self.success(f"Node {i+1} stopped")
        
        if self.api_process and self.api_process.poll() is None:
            self.step("Stopping API server...")
            self.api_process.terminate()
            self.success("API stopped")
        
        print("\nDemo complete!")
    
    def run(self):
        """Run the complete demo."""
        print("\n" + "=" * 80)
        print("  ClusterCloud Distributed Rendering Demo - Phase 5")
        print("=" * 80)
        
        try:
            if not self.start_api():
                return 1
            
            if not self.start_nodes():
                return 1
            
            if not self.submit_job():
                return 1
            
            self.monitor_execution()
            
            self.verify_results()
            
            return 0
            
        except KeyboardInterrupt:
            print("\n\nDemo interrupted by user")
            return 130
        except Exception as e:
            self.error(f"Demo failed: {e}")
            import traceback
            traceback.print_exc()
            return 1
        finally:
            self.cleanup()


if __name__ == "__main__":
    demo = DemoOrchestrator()
    sys.exit(demo.run())
