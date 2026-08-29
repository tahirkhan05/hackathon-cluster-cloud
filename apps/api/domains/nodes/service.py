"""
Node service layer.

Business logic for node registration, heartbeat management,
and stale node detection.
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime, timedelta
from typing import List, Optional
import logging

from domains.nodes.models import Node, NodeStatus
from domains.nodes.schemas import NodeRegister, NodeHeartbeat
from domains.reliability.models import ReliabilityScore
from config import settings

logger = logging.getLogger(__name__)


class NodeService:
    """Service for node operations."""
    
    @staticmethod
    def register_node(db: Session, node_data: NodeRegister) -> Node:
        """
        Register a new node or reactivate existing one.
        
        If node with same provider_id exists:
        - Reactivate it
        - Update capabilities
        - Reset status to AVAILABLE
        
        Otherwise create new node with reliability score.
        """
        existing = db.query(Node).filter(
            Node.provider_id == node_data.provider_id
        ).first()
        
        if existing:
            logger.info(f"Reactivating existing node: {existing.node_id}")
            
            existing.status = NodeStatus.AVAILABLE
            existing.last_heartbeat = datetime.utcnow()
            existing.last_seen_at = datetime.utcnow()
            existing.capabilities = node_data.capabilities
            existing.hostname = node_data.hostname
            existing.ip_address = node_data.ip_address
            existing.max_concurrent_tasks = node_data.max_concurrent_tasks
            existing.cost_per_task_clstr = node_data.cost_per_task_clstr
            existing.is_healthy = True
            existing.current_task_count = 0
            
            db.commit()
            db.refresh(existing)
            
            logger.info(f"Node reactivated: {existing.node_id}")
            return existing
        
        node = Node(
            provider_id=node_data.provider_id,
            hostname=node_data.hostname,
            ip_address=node_data.ip_address,
            capabilities=node_data.capabilities,
            max_concurrent_tasks=node_data.max_concurrent_tasks,
            cost_per_task_clstr=node_data.cost_per_task_clstr,
            status=NodeStatus.AVAILABLE
        )
        
        db.add(node)
        db.flush()
        
        reliability = ReliabilityScore(node_id=node.node_id)
        db.add(reliability)
        
        db.commit()
        db.refresh(node)
        
        logger.info(f"New node registered: {node.node_id} (provider: {node.provider_id})")
        return node
    
    @staticmethod
    def process_heartbeat(db: Session, node_id: str, heartbeat: NodeHeartbeat) -> dict:
        """
        Process node heartbeat and update status.
        
        Returns:
            Status dict with result
            
        Raises:
            ValueError: If node not found
        """
        node = db.query(Node).filter(Node.node_id == node_id).first()
        
        if not node:
            raise ValueError(f"Node not found: {node_id}")
        
        node.last_heartbeat = datetime.utcnow()
        node.last_seen_at = datetime.utcnow()
        node.current_task_count = heartbeat.current_task_count
        node.is_healthy = heartbeat.is_healthy
        
        old_status = node.status
        
        if not heartbeat.is_healthy:
            node.status = NodeStatus.OFFLINE
        elif node.current_task_count >= node.max_concurrent_tasks:
            node.status = NodeStatus.BUSY
        else:
            node.status = NodeStatus.AVAILABLE
        
        if old_status != node.status:
            logger.info(f"Node {node_id} status: {old_status} → {node.status}")
        
        db.commit()
        
        return {
            "status": "ok",
            "node_id": node_id,
            "node_status": node.status.value,
            "is_available": node.is_available
        }
    
    @staticmethod
    def get_node(db: Session, node_id: str) -> Optional[Node]:
        """Get node by ID."""
        return db.query(Node).filter(Node.node_id == node_id).first()
    
    @staticmethod
    def list_nodes(
        db: Session,
        status: Optional[NodeStatus] = None,
        available_only: bool = False
    ) -> List[Node]:
        """
        List nodes with optional filtering.
        
        Args:
            status: Filter by specific status
            available_only: Only return available nodes
        """
        query = db.query(Node)
        
        if status:
            query = query.filter(Node.status == status)
        
        if available_only:
            query = query.filter(
                and_(
                    Node.status == NodeStatus.AVAILABLE,
                    Node.is_healthy == True,
                    Node.current_task_count < Node.max_concurrent_tasks
                )
            )
        
        return query.all()
    
    @staticmethod
    def detect_stale_nodes(db: Session, timeout_seconds: int = None) -> List[Node]:
        """
        Detect nodes with stale heartbeats.
        
        A node is stale if last_heartbeat exceeds timeout threshold.
        
        Args:
            timeout_seconds: Heartbeat timeout (default from settings)
            
        Returns:
            List of stale nodes
        """
        if timeout_seconds is None:
            timeout_seconds = settings.HEARTBEAT_TIMEOUT_SECONDS
        
        threshold = datetime.utcnow() - timedelta(seconds=timeout_seconds)
        
        stale_nodes = db.query(Node).filter(
            and_(
                Node.last_heartbeat < threshold,
                Node.status != NodeStatus.OFFLINE
            )
        ).all()
        
        return stale_nodes
    
    @staticmethod
    def mark_stale_nodes_offline(db: Session, timeout_seconds: int = None) -> int:
        """
        Mark stale nodes as OFFLINE.
        
        Returns:
            Number of nodes marked offline
        """
        stale_nodes = NodeService.detect_stale_nodes(db, timeout_seconds)
        
        count = 0
        for node in stale_nodes:
            logger.warning(
                f"Marking stale node offline: {node.node_id} "
                f"(last heartbeat: {node.last_heartbeat})"
            )
            node.status = NodeStatus.OFFLINE
            node.is_healthy = False
            count += 1
        
        if count > 0:
            db.commit()
            logger.info(f"Marked {count} stale nodes offline")
        
        return count
    
    @staticmethod
    def get_available_nodes_count(db: Session) -> int:
        """Get count of available nodes."""
        return db.query(Node).filter(
            and_(
                Node.status == NodeStatus.AVAILABLE,
                Node.is_healthy == True,
                Node.current_task_count < Node.max_concurrent_tasks
            )
        ).count()
    
    @staticmethod
    def get_node_statistics(db: Session) -> dict:
        """Get overall node statistics."""
        total = db.query(Node).count()
        available = db.query(Node).filter(Node.status == NodeStatus.AVAILABLE).count()
        busy = db.query(Node).filter(Node.status == NodeStatus.BUSY).count()
        offline = db.query(Node).filter(Node.status == NodeStatus.OFFLINE).count()
        
        return {
            "total_nodes": total,
            "available": available,
            "busy": busy,
            "offline": offline,
            "healthy": db.query(Node).filter(Node.is_healthy == True).count()
        }
