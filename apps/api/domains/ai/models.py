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
    
    # Identity
    recommendation_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Agent identification
    agent_name = Column(String(100), nullable=False, index=True)
    agent_version = Column(String(20), default="1.0")
    
    # Context
    request_context_id = Column(String(100), index=True)  # job_id, incident_id, etc.
    request_context_type = Column(String(50))  # "job", "incident", "node_failure", etc.
    
    # AI Input/Output
    input_data = Column(JSON)  # Structured context sent to AI
    recommendation = Column(JSON, nullable=False)  # AI's recommendation
    reasoning = Column(Text)  # AI's explanation (if provided)
    confidence = Column(Float)  # 0.0-1.0 if AI provides confidence
    
    # Validation
    validation_passed = Column(Boolean, nullable=False)
    validation_result = Column(JSON)  # Detailed validation results
    validation_errors = Column(JSON)  # List of validation errors if failed
    
    # Action taken
    action_taken = Column(String(100))  # "accepted", "rejected", "fallback"
    selected_alternative = Column(JSON)  # If fallback used instead
    
    # Metadata
    bedrock_available = Column(Boolean, default=True)
    response_time_ms = Column(Float)  # Time taken for AI response
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    def __repr__(self):
        return (
            f"<AgentRecommendation {self.agent_name} "
            f"context={self.request_context_id} "
            f"validated={self.validation_passed}>"
        )
