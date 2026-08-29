"""Workload data models - stub for initial setup."""
from sqlalchemy import Column, String, Boolean, JSON

from database import Base


class WorkloadType(Base):
    """Workload type model - to be fully implemented in task #3."""
    __tablename__ = "workload_types"
    
    workload_type = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    parallelizable = Column(Boolean, default=False)
    description = Column(String, nullable=True)
    resource_requirements = Column(JSON, nullable=True)
