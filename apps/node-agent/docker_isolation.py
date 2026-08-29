"""
Docker-based workload isolation.

MVP Security:
- Network isolation
- Resource limits (CPU, memory, disk)
- Read-only root filesystem where possible
- Drop unnecessary capabilities
- No privileged mode

Production Needs:
- User namespaces
- Seccomp profiles
- AppArmor/SELinux
- Runtime security scanning
- Audit logging
"""
import logging
import subprocess
import json
from typing import Optional, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class DockerIsolation:
    """
    Secure Docker container isolation for workload execution.
    """
    
    def __init__(
        self,
        max_memory_mb: int = 2048,
        max_cpu_cores: float = 2.0,
        max_disk_mb: int = 5120,
        network: str = "none",
        enable_isolation: bool = True
    ):
        self.max_memory_mb = max_memory_mb
        self.max_cpu_cores = max_cpu_cores
        self.max_disk_mb = max_disk_mb
        self.network = network
        self.enable_isolation = enable_isolation
    
    def build_docker_args(
        self,
        image: str,
        command: list,
        work_dir: Path,
        env_vars: Optional[Dict[str, str]] = None
    ) -> list:
        """
        Build secure Docker run arguments.
        
        Security controls:
        - Memory limit
        - CPU limit
        - Network isolation
        - No privileged mode
        - Drop all capabilities
        - Read-only root filesystem (where possible)
        - Temporary filesystem for /tmp
        - Security options
        """
        if not self.enable_isolation:
            # Bypass Docker for development
            return None
        
        args = [
            "docker", "run",
            "--rm",  # Remove container after execution
            
            # Resource limits
            f"--memory={self.max_memory_mb}m",
            f"--memory-swap={self.max_memory_mb}m",  # No swap
            f"--cpus={self.max_cpu_cores}",
            f"--storage-opt=size={self.max_disk_mb}M",
            
            # Network isolation
            f"--network={self.network}",
            
            # Security
            "--security-opt=no-new-privileges:true",  # Prevent privilege escalation
            "--cap-drop=ALL",  # Drop all capabilities
            "--read-only",  # Read-only root filesystem
            "--tmpfs=/tmp:rw,noexec,nosuid,size=512m",  # Writable /tmp
            
            # User (non-root)
            "--user=nobody",  # Run as nobody user
            
            # Work directory mount (ephemeral)
            f"--volume={work_dir.absolute()}:/work:rw",
            "--workdir=/work",
        ]
        
        # Environment variables
        if env_vars:
            for key, value in env_vars.items():
                args.append(f"--env={key}={value}")
        
        # Container image
        args.append(image)
        
        # Command
        args.extend(command)
        
        return args
    
    def execute_isolated(
        self,
        image: str,
        command: list,
        work_dir: Path,
        env_vars: Optional[Dict[str, str]] = None,
        timeout: int = 300
    ) -> Dict[str, Any]:
        """
        Execute command in isolated Docker container.
        
        Returns:
            {
                "success": bool,
                "exit_code": int,
                "stdout": str,
                "stderr": str,
                "error": str (if failed)
            }
        """
        args = self.build_docker_args(image, command, work_dir, env_vars)
        
        if args is None:
            # Direct execution without Docker (development only)
            logger.warning("Docker isolation disabled - executing directly")
            return self._execute_direct(command, work_dir, env_vars, timeout)
        
        logger.info(f"Executing isolated workload: {' '.join(args[:5])}...")
        
        try:
            result = subprocess.run(
                args,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=work_dir
            )
            
            return {
                "success": result.returncode == 0,
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }
        
        except subprocess.TimeoutExpired:
            logger.error(f"Task execution timeout after {timeout}s")
            return {
                "success": False,
                "exit_code": -1,
                "stdout": "",
                "stderr": f"Execution timeout after {timeout}s",
                "error": "timeout"
            }
        
        except Exception as e:
            logger.error(f"Task execution failed: {e}")
            return {
                "success": False,
                "exit_code": -1,
                "stdout": "",
                "stderr": str(e),
                "error": str(e)
            }
    
    def _execute_direct(
        self,
        command: list,
        work_dir: Path,
        env_vars: Optional[Dict[str, str]],
        timeout: int
    ) -> Dict[str, Any]:
        """
        Direct execution without Docker isolation.
        
        WARNING: Use only in development. No isolation provided.
        """
        import os
        
        env = os.environ.copy()
        if env_vars:
            env.update(env_vars)
        
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=work_dir,
                env=env
            )
            
            return {
                "success": result.returncode == 0,
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }
        
        except Exception as e:
            return {
                "success": False,
                "exit_code": -1,
                "stdout": "",
                "stderr": str(e),
                "error": str(e)
            }
    
    @staticmethod
    def check_docker_available() -> bool:
        """Check if Docker is available."""
        try:
            result = subprocess.run(
                ["docker", "version"],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False
    
    @staticmethod
    def pull_image(image: str) -> bool:
        """Pull Docker image if not present."""
        try:
            logger.info(f"Pulling Docker image: {image}")
            result = subprocess.run(
                ["docker", "pull", image],
                capture_output=True,
                timeout=300
            )
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Failed to pull image {image}: {e}")
            return False
