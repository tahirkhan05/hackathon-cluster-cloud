"""
AI Agent Recommendation models.

Tracks AI agent decisions and validations.
"""
from sqlalchemy import Column, String, Float, Text, DateTime, JSON, Boolean
from sqlalchemy.sql import func
from datetime import datetime
import uuid

from database import Base


class AgentRecommendation(Base):
    """
    Records AI agent recommendations and validation results.
    
    Tracks the complete flow:
    - Agent reasoning → recommendation → validation → action
    """
    __tablename__ = "agent_recommendations"
    
    recommendation_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    agent_name = Column(String(100), nullable=False, index=True)
    agent_version = Column(String(20), default="1.0")
    
    request_context_id = Column(String(100), index=True)
    request_context_type = Column(String(50))
    
    input_data = Column(JSON)
    recommendation = Column(JSON, nullable=False)
    reasoning = Column(Text)
    confidence = Column(Float)
    
    validation_passed = Column(Boolean, nullable=False)
    validation_result = Column(JSON)
    validation_errors = Column(JSON)
    
    action_taken = Column(String(100))
    selected_alternative = Column(JSON)
    
    bedrock_available = Column(Boolean, default=True)
    response_time_ms = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    def __repr__(self):
        return (
            f"<AgentRecommendation {self.agent_name} "
            f"context={self.request_context_id} "
            f"validated={self.validation_passed}>"
        )
