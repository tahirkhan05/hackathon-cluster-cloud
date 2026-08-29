"""
Task Executor - Phase 5

Polls for tasks, executes rendering workload, reports progress and results.
"""
import time
import logging
import httpx
from typing import Optional, Dict, Any
from pathlib import Path

from renderer import FrameRenderer

logger = logging.getLogger(__name__)


class TaskExecutor:
    """
    Executes rendering tasks assigned to this node.
    
    Workflow:
    1. Poll for assigned tasks
    2. Execute rendering workload
    3. Report progress updates
    4. Upload result
    5. Mark task complete
    """
    
    def __init__(
        self,
        control_plane_url: str,
        node_id: str,
        output_dir: str = "./rendered_frames"
    ):
        self.control_plane_url = control_plane_url.rstrip("/")
        self.node_id = node_id
        self.renderer = FrameRenderer(output_dir)
        self.current_task_id: Optional[str] = None
        
        logger.info(f"Task executor initialized for node {node_id}")
    
    def poll_for_task(self) -> Optional[Dict[str, Any]]:
        """
        Poll control plane for assigned task.
        
        Returns:
            Task dict if available, None otherwise
        """
        try:
            url = f"{self.control_plane_url}/api/tasks/poll"
            
            with httpx.Client(timeout=10.0) as client:
                response = client.post(
                    url,
                    json={"node_id": self.node_id}
                )
                
                if response.status_code == 200:
                    task = response.json()
                    logger.info(f"Received task: {task.get('task_id')}")
                    return task
                elif response.status_code == 404:
                    # No tasks available
                    return None
                else:
                    logger.warning(
                        f"Poll failed: {response.status_code} - {response.text}"
                    )
                    return None
                    
        except Exception as e:
            logger.error(f"Error polling for task: {e}")
            return None
    
    def execute_task(self, task: Dict[str, Any]) -> bool:
        """
        Execute a rendering task.
        
        Args:
            task: Task specification
            
        Returns:
            True if execution succeeded
        """
        task_id = task["task_id"]
        self.current_task_id = task_id
        
        try:
            logger.info(f"Starting task {task_id}")
            
            # Mark task as running
            self._update_task_status(task_id, "RUNNING")
            
            # Extract parameters
            params = task.get("parameters", {})
            frame_number = params.get("frame_number", params.get("task_index", 0))
            total_frames = params.get("total_frames", 100)
            
            # Report progress: started
            self._report_progress(task_id, 0, f"Starting frame {frame_number}")
            
            # Render frame
            result = self.renderer.render_frame(
                frame_number=frame_number,
                total_frames=total_frames,
                node_id=self.node_id,
                parameters=params
            )
            
            # Report progress: rendering complete
            self._report_progress(task_id, 80, "Rendering complete, uploading...")
            
            # Upload result (for now, just send metadata)
            self._upload_result(task_id, result)
            
            # Report progress: complete
            self._report_progress(task_id, 100, "Upload complete")
            
            # Mark task as completed
            self._update_task_status(
                task_id,
                "COMPLETED",
                result=result
            )
            
            logger.info(f"Task {task_id} completed successfully")
            self.current_task_id = None
            return True
            
        except Exception as e:
            logger.error(f"Task {task_id} failed: {e}", exc_info=True)
            
            # Mark task as failed
            self._update_task_status(
                task_id,
                "FAILED",
                error=str(e)
            )
            
            self.current_task_id = None
            return False
    
    def _update_task_status(
        self,
        task_id: str,
        status: str,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ):
        """Update task status on control plane."""
        try:
            url = f"{self.control_plane_url}/api/tasks/{task_id}/status"
            
            payload = {"status": status}
            
            if result:
                payload["result"] = result
            
            if error:
                payload["error_message"] = error
            
            with httpx.Client(timeout=10.0) as client:
                response = client.put(url, json=payload)
                
                if response.status_code == 200:
                    logger.debug(f"Task {task_id} status updated to {status}")
                else:
                    logger.warning(
                        f"Failed to update task status: "
                        f"{response.status_code} - {response.text}"
                    )
                    
        except Exception as e:
            logger.error(f"Error updating task status: {e}")
    
    def _report_progress(self, task_id: str, progress: int, message: str):
        """Report task progress."""
        try:
            url = f"{self.control_plane_url}/api/tasks/{task_id}/progress"
            
            payload = {
                "progress_percent": progress,
                "message": message
            }
            
            with httpx.Client(timeout=5.0) as client:
                response = client.post(url, json=payload)
                
                if response.status_code == 200:
                    logger.debug(f"Progress reported: {progress}% - {message}")
                else:
                    logger.warning(f"Failed to report progress: {response.status_code}")
                    
        except Exception as e:
            logger.warning(f"Error reporting progress: {e}")
    
    def _upload_result(self, task_id: str, result: Dict[str, Any]):
        """
        Upload rendered frame result.
        
        For MVP, we just send metadata. In production, would upload to S3/storage.
        """
        try:
            # For now, just log that we would upload
            logger.info(
                f"Result ready for task {task_id}: "
                f"{result['filename']} ({result['file_size_bytes']} bytes)"
            )
            
            # In production, would upload file to storage:
            # - Upload to S3/GCS/Azure Blob
            # - Update result with download URL
            # - Send URL to control plane
            
            # For MVP, result metadata is sent with completion status
            
        except Exception as e:
            logger.error(f"Error uploading result: {e}")
    
    def run_task_loop(
        self,
        poll_interval: float = 5.0,
        max_iterations: Optional[int] = None
    ):
        """
        Main task execution loop.
        
        Args:
            poll_interval: Seconds between polls
            max_iterations: Max iterations (None for infinite)
        """
        logger.info("Starting task execution loop")
        logger.info(f"Poll interval: {poll_interval}s")
        
        iteration = 0
        
        try:
            while True:
                # Check max iterations
                if max_iterations and iteration >= max_iterations:
                    logger.info(f"Reached max iterations ({max_iterations})")
                    break
                
                iteration += 1
                
                # Poll for task
                task = self.poll_for_task()
                
                if task:
                    # Execute task
                    self.execute_task(task)
                else:
                    # No task available, sleep
                    logger.debug("No tasks available, waiting...")
                    time.sleep(poll_interval)
                
        except KeyboardInterrupt:
            logger.info("Task loop interrupted")
        except Exception as e:
            logger.error(f"Error in task loop: {e}", exc_info=True)
        finally:
            logger.info("Task execution loop stopped")
