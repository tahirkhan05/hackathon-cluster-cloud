"""Reliability data models."""
from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

from database import Base


class ReliabilityScore(Base):
    """
    Provider reputation and history tracking.
    
    Maintains detailed reliability metrics used for node selection,
    economic penalties/rewards, and provider reputation.
    """
    __tablename__ = "reliability_scores"
    
    node_id = Column(String, ForeignKey("nodes.node_id"), primary_key=True)
    
    # Core metrics
    reliability_score = Column(Float, default=1.0)  # 0.0 to 1.0
    
    # Task statistics
    tasks_completed = Column(Integer, default=0)
    tasks_failed = Column(Integer, default=0)
    tasks_reassigned = Column(Integer, default=0)
    recovery_assists = Column(Integer, default=0)
    
    # Incident statistics
    total_incidents = Column(Integer, default=0)
    heartbeat_timeouts = Column(Integer, default=0)
    task_timeouts = Column(Integer, default=0)
    crashes = Column(Integer, default=0)
    
    # Performance metrics
    average_task_duration_seconds = Column(Float, nullable=True)
    fastest_task_duration_seconds = Column(Float, nullable=True)
    slowest_task_duration_seconds = Column(Float, nullable=True)
    
    # Uptime tracking
    total_uptime_seconds = Column(Integer, default=0)
    total_downtime_seconds = Column(Integer, default=0)
    
    # Historical trend (JSON array of daily scores)
    score_history = Column(JSON, nullable=True)
    
    # Last updated
    last_calculated_at = Column(DateTime, default=datetime.utcnow)
    last_incident_at = Column(DateTime, nullable=True)
    
    # Relationships
    node = relationship("Node", back_populates="reliability")
    
    @property
    def success_rate(self) -> float:
        """Calculate task success rate."""
        total = self.tasks_completed + self.tasks_failed
        if total == 0:
            return 1.0
        return self.tasks_completed / total
    
    @property
    def uptime_percentage(self) -> float:
        """Calculate uptime percentage."""
        total = self.total_uptime_seconds + self.total_downtime_seconds
        if total == 0:
            return 100.0
        return (self.total_uptime_seconds / total) * 100
    
    def calculate_score(self) -> float:
        """
        Calculate reliability score using weighted formula.
        
        Score = (completed * 1.0 + recovery_assists * 0.5) / 
                (total_tasks + failed * 2.0)
        
        Clamped to [0.0, 1.0]
        """
        completed_weight = self.tasks_completed * 1.0
        recovery_weight = self.recovery_assists * 0.5
        numerator = completed_weight + recovery_weight
        
        total_tasks = self.tasks_completed + self.tasks_failed
        failed_penalty = self.tasks_failed * 2.0
        denominator = total_tasks + failed_penalty
        
        if denominator == 0:
            return 1.0
        
        score = numerator / denominator
        return max(0.0, min(1.0, score))
