"""
Hardware discovery and system information.

Detects CPU, RAM, GPU, disk, and other system capabilities.
"""
import platform
import socket
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class HardwareDiscovery:
    """Discover and report system hardware capabilities."""
    
    @staticmethod
    def get_cpu_info() -> Dict[str, Any]:
        """Get CPU information."""
        try:
            import psutil
            cpu_count = psutil.cpu_count(logical=False) or psutil.cpu_count()
            cpu_freq = psutil.cpu_freq()
            
            return {
                "cpu_cores_physical": psutil.cpu_count(logical=False),
                "cpu_cores_logical": psutil.cpu_count(logical=True),
                "cpu_frequency_mhz": cpu_freq.current if cpu_freq else None,
                "cpu_architecture": platform.machine(),
                "cpu_processor": platform.processor()
            }
        except ImportError:
            logger.warning("psutil not available, using basic CPU detection")
            return {
                "cpu_cores_physical": None,
                "cpu_cores_logical": None,
                "cpu_architecture": platform.machine(),
                "cpu_processor": platform.processor()
            }
    
    @staticmethod
    def get_memory_info() -> Dict[str, Any]:
        """Get RAM information."""
        try:
            import psutil
            mem = psutil.virtual_memory()
            
            return {
                "ram_total_gb": round(mem.total / (1024**3), 2),
                "ram_available_gb": round(mem.available / (1024**3), 2),
                "ram_percent_used": mem.percent
            }
        except ImportError:
            logger.warning("psutil not available, RAM detection unavailable")
            return {
                "ram_total_gb": None,
                "ram_available_gb": None
            }
    
    @staticmethod
    def get_disk_info() -> Dict[str, Any]:
        """Get disk information."""
        try:
            import psutil
            disk = psutil.disk_usage('/')
            
            return {
                "disk_total_gb": round(disk.total / (1024**3), 2),
                "disk_free_gb": round(disk.free / (1024**3), 2),
                "disk_percent_used": disk.percent
            }
        except ImportError:
            logger.warning("psutil not available, disk detection unavailable")
            return {
                "disk_total_gb": None,
                "disk_free_gb": None
            }
    
    @staticmethod
    def get_gpu_info() -> Optional[Dict[str, Any]]:
        """
        Get GPU information if available.
        
        Attempts to detect NVIDIA GPUs using nvidia-smi or pynvml.
        Returns None if no GPU detected or libraries unavailable.
        """
        # Try pynvml first (more reliable)
        try:
            import pynvml
            pynvml.nvmlInit()
            
            device_count = pynvml.nvmlDeviceGetCount()
            if device_count == 0:
                return None
            
            gpus = []
            for i in range(device_count):
                handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                name = pynvml.nvmlDeviceGetName(handle)
                memory_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                
                gpus.append({
                    "gpu_index": i,
                    "gpu_name": name.decode('utf-8') if isinstance(name, bytes) else name,
                    "gpu_memory_total_gb": round(memory_info.total / (1024**3), 2),
                    "gpu_memory_free_gb": round(memory_info.free / (1024**3), 2)
                })
            
            pynvml.nvmlShutdown()
            return {"gpus": gpus, "gpu_count": len(gpus)}
            
        except Exception as e:
            logger.debug(f"pynvml GPU detection failed: {e}")
        
        # Fallback: try nvidia-smi command
        try:
            import subprocess
            result = subprocess.run(
                ['nvidia-smi', '--query-gpu=name,memory.total', '--format=csv,noheader'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                gpus = []
                for i, line in enumerate(lines):
                    parts = line.split(',')
                    if len(parts) >= 2:
                        name = parts[0].strip()
                        memory_str = parts[1].strip().replace(' MiB', '')
                        memory_gb = round(int(memory_str) / 1024, 2)
                        
                        gpus.append({
                            "gpu_index": i,
                            "gpu_name": name,
                            "gpu_memory_total_gb": memory_gb
                        })
                
                return {"gpus": gpus, "gpu_count": len(gpus)}
                
        except Exception as e:
            logger.debug(f"nvidia-smi GPU detection failed: {e}")
        
        return None
    
    @staticmethod
    def get_network_info() -> Dict[str, Any]:
        """Get network information."""
        try:
            hostname = socket.gethostname()
            ip_address = socket.gethostbyname(hostname)
            
            return {
                "hostname": hostname,
                "ip_address": ip_address,
                "fqdn": socket.getfqdn()
            }
        except Exception as e:
            logger.warning(f"Network info detection failed: {e}")
            return {
                "hostname": platform.node(),
                "ip_address": None
            }
    
    @classmethod
    def discover_all(cls) -> Dict[str, Any]:
        """
        Discover all system capabilities.
        
        Returns complete hardware profile for node registration.
        """
        logger.info("Discovering system hardware...")
        
        capabilities = {
            "platform": platform.system(),
            "platform_release": platform.release(),
            "platform_version": platform.version(),
            "python_version": platform.python_version()
        }
        
        # CPU
        cpu_info = cls.get_cpu_info()
        capabilities.update(cpu_info)
        logger.info(f"CPU: {cpu_info.get('cpu_cores_logical', '?')} cores")
        
        # Memory
        mem_info = cls.get_memory_info()
        capabilities.update(mem_info)
        logger.info(f"RAM: {mem_info.get('ram_total_gb', '?')} GB")
        
        # Disk
        disk_info = cls.get_disk_info()
        capabilities.update(disk_info)
        logger.info(f"Disk: {disk_info.get('disk_free_gb', '?')} GB free")
        
        # GPU (optional)
        gpu_info = cls.get_gpu_info()
        if gpu_info:
            capabilities.update(gpu_info)
            logger.info(f"GPU: {gpu_info['gpu_count']} device(s) detected")
        else:
            capabilities["gpu_available"] = False
            logger.info("GPU: None detected")
        
        # Network
        net_info = cls.get_network_info()
        capabilities.update(net_info)
        
        return capabilities
