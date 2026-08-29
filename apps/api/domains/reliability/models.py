"""Reliability data models - stub for initial setup."""
from sqlalchemy import Column, String, Float, Integer
from database import Base


class ReliabilityScore(Base):
    """Reliability score model - to be fully implemented in task #3."""
    __tablename__ = "reliability_scores"
    
    node_id = Column(String, primary_key=True)
    reliability_score = Column(Float, default=1.0)
    tasks_completed = Column(Integer, default=0)
    tasks_failed = Column(Integer, default=0)
