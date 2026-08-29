"""
Simple Frame Renderer

Generates actual image frames using PIL for demonstration.
Creates realistic CPU/GPU workload for distributed rendering.
"""
import os
import time
import logging
import hashlib
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime

try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    logging.warning("PIL not available, using mock renderer")

logger = logging.getLogger(__name__)


class FrameRenderer:
    """
    Deterministic frame renderer for distributed workload.
    
    Generates frames with:
    - Gradient background (varies per frame)
    - Frame number overlay
    - Node ID watermark
    - Timestamp
    - Render time
    
    Output: PNG images suitable for video compilation
    """
    
    DEFAULT_WIDTH = 1920
    DEFAULT_HEIGHT = 1080
    DEFAULT_FPS = 30
    
    def __init__(self, output_dir: str = "./rendered_frames"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Frame renderer initialized, output: {self.output_dir}")
    
    def render_frame(
        self,
        frame_number: int,
        total_frames: int,
        node_id: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Render a single frame.
        
        Args:
            frame_number: Frame index (0-based)
            total_frames: Total frames in sequence
            node_id: Node ID for watermark
            parameters: Additional rendering parameters
            
        Returns:
            Result dict with path, size, render_time, checksum
        """
        start_time = time.time()
        
        params = parameters or {}
        width = params.get("width", self.DEFAULT_WIDTH)
        height = params.get("height", self.DEFAULT_HEIGHT)
        complexity = params.get("complexity", "medium")
        
        logger.info(
            f"Rendering frame {frame_number}/{total_frames} "
            f"({width}x{height}, {complexity})"
        )
        
        if PIL_AVAILABLE:
            result = self._render_real_frame(
                frame_number, total_frames, node_id,
                width, height, complexity
            )
        else:
            result = self._render_mock_frame(
                frame_number, total_frames, node_id,
                width, height, complexity
            )
        
        render_time = time.time() - start_time
        result["render_time_seconds"] = render_time
        
        logger.info(f"Frame {frame_number} completed in {render_time:.2f}s")
        
        return result
    
    def _render_real_frame(
        self,
        frame_number: int,
        total_frames: int,
        node_id: str,
        width: int,
        height: int,
        complexity: str
    ) -> Dict[str, Any]:
        """Render actual image using PIL."""
        
        image = Image.new("RGB", (width, height))
        draw = ImageDraw.Draw(image)
        
        progress = frame_number / max(total_frames - 1, 1)
        
        for y in range(height):
            r = int(255 * (y / height) * (1 - progress * 0.5))
            g = int(255 * progress)
            b = int(255 * (1 - y / height) * (0.5 + progress * 0.5))
            
            draw.line([(0, y), (width, y)], fill=(r, g, b))
        
        if complexity == "high":
            for i in range(0, width, 20):
                for j in range(0, height, 20):
                    phase = (frame_number + i + j) % 100
                    alpha = int(128 + 127 * (phase / 100))
                    draw.ellipse(
                        [i, j, i + 15, j + 15],
                        fill=(alpha, alpha, 255 - alpha)
                    )
        elif complexity == "medium":
            for i in range(0, width, 40):
                draw.line(
                    [(i, 0), (i, height)],
                    fill=(255, 255, 255, 128),
                    width=2
                )
        
        try:
            font_large = ImageFont.truetype("arial.ttf", 72)
            font_small = ImageFont.truetype("arial.ttf", 24)
        except:
            font_large = ImageFont.load_default()
            font_small = ImageFont.load_default()
        
        draw.text(
            (width // 2 - 100, height // 2 - 50),
            f"Frame {frame_number}",
            fill=(255, 255, 255),
            font=font_large
        )
        
        draw.text(
            (20, height - 60),
            f"Node: {node_id[:12]}",
            fill=(200, 200, 200),
            font=font_small
        )
        
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        draw.text(
            (20, height - 30),
            timestamp,
            fill=(200, 200, 200),
            font=font_small
        )
        
        filename = f"frame_{frame_number:06d}.png"
        output_path = self.output_dir / filename
        image.save(output_path, "PNG")
        
        checksum = self._calculate_checksum(output_path)
        
        file_size = output_path.stat().st_size
        
        return {
            "frame_number": frame_number,
            "output_path": str(output_path),
            "filename": filename,
            "file_size_bytes": file_size,
            "resolution": f"{width}x{height}",
            "checksum": checksum,
            "node_id": node_id
        }
    
    def _render_mock_frame(
        self,
        frame_number: int,
        total_frames: int,
        node_id: str,
        width: int,
        height: int,
        complexity: str
    ) -> Dict[str, Any]:
        """Mock renderer when PIL not available."""
        
        work_iterations = {
            "low": 1000000,
            "medium": 5000000,
            "high": 10000000
        }.get(complexity, 5000000)
        
        result_hash = hashlib.sha256()
        for i in range(work_iterations):
            data = f"{frame_number}-{node_id}-{i}".encode()
            result_hash.update(data)
        
        checksum = result_hash.hexdigest()
        
        filename = f"frame_{frame_number:06d}.mock"
        output_path = self.output_dir / filename
        
        with open(output_path, "w") as f:
            f.write(f"Mock frame {frame_number}\n")
            f.write(f"Node: {node_id}\n")
            f.write(f"Resolution: {width}x{height}\n")
            f.write(f"Complexity: {complexity}\n")
            f.write(f"Checksum: {checksum}\n")
        
        file_size = output_path.stat().st_size
        
        logger.info(f"Mock frame {frame_number} created")
        
        return {
            "frame_number": frame_number,
            "output_path": str(output_path),
            "filename": filename,
            "file_size_bytes": file_size,
            "resolution": f"{width}x{height}",
            "checksum": checksum,
            "node_id": node_id,
            "mock": True
        }
    
    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA256 checksum of file."""
        sha256_hash = hashlib.sha256()
        
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        
        return sha256_hash.hexdigest()
    
    def cleanup_old_frames(self, keep_count: int = 100):
        """Remove old frames to save disk space."""
        frames = sorted(self.output_dir.glob("frame_*.png"))
        
        if len(frames) > keep_count:
            for frame in frames[:-keep_count]:
                frame.unlink()
                logger.info(f"Cleaned up old frame: {frame.name}")
