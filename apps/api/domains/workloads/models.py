"""Workload data models."""
from sqlalchemy import Column, String, Boolean, JSON, Integer
from sqlalchemy.orm import relationship

from database import Base


class WorkloadType(Base):
    """
    Workload type definition.
    
    Defines characteristics of supported workload types.
    MVP: frame_rendering (parallelizable, stateless, GPU-preferred)
    """
    __tablename__ = "workload_types"
    
    workload_type = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    parallelizable = Column(Boolean, default=False)
    description = Column(String, nullable=True)
    
    resource_requirements = Column(JSON, nullable=True)
    
    estimated_task_duration = Column(Integer, nullable=True)
    
    jobs = relationship("Job", back_populates="workload")
