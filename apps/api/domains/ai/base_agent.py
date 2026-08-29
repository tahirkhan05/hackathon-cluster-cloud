"""
Base AI Agent class.

Provides common structure for all AI agents with validation and fallback.
"""
import time
import logging
from typing import Dict, Any, Optional, Tuple
from abc import ABC, abstractmethod
from sqlalchemy.orm import Session

from domains.ai.bedrock_client import get_bedrock_client
from domains.ai.models import AgentRecommendation

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Base class for AI agents with validation and fallback support."""
    
    agent_name: str = "BaseAgent"
    agent_version: str = "1.0"
    
    def __init__(self, db: Session):
        self.db = db
        self.bedrock = get_bedrock_client()
    
    @abstractmethod
    def gather_context(self, **kwargs) -> Dict[str, Any]:
        """Gather structured context for AI decision."""
        pass
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """Get system prompt describing agent's role and constraints."""
        pass
    
    @abstractmethod
    def format_user_message(self, context: Dict[str, Any]) -> str:
        """Format context into user message for AI."""
        pass
    
    @abstractmethod
    def get_response_schema(self) -> Dict[str, Any]:
        """Get expected JSON schema for AI response."""
        pass
    
    @abstractmethod
    def validate_recommendation(
        self,
        recommendation: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Tuple[bool, Dict[str, Any], Optional[list]]:
        """Validate AI recommendation against constraints. Returns (is_valid, result, errors)."""
        pass
    
    @abstractmethod
    def deterministic_fallback(
        self,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Deterministic fallback when AI unavailable or validation fails."""
        pass
    
    def recommend(
        self,
        request_context_id: str,
        request_context_type: str,
        **kwargs
    ) -> Tuple[Dict[str, Any], AgentRecommendation]:
        """Main recommendation flow. Returns (final_recommendation, tracking_record)."""
        logger.info(f"[{self.agent_name}] Processing request: {request_context_id}")
        
        context = self.gather_context(**kwargs)
        
        ai_recommendation = None
        reasoning = None
        confidence = None
        response_time_ms = None
        bedrock_available = self.bedrock.is_available()
        
        if bedrock_available:
            start_time = time.time()
            
            system_prompt = self.get_system_prompt()
            user_message = self.format_user_message(context)
            response_schema = self.get_response_schema()
            
            ai_response = self.bedrock.invoke_structured(
                system_prompt=system_prompt,
                user_message=user_message,
                response_schema=response_schema
            )
            
            response_time_ms = (time.time() - start_time) * 1000
            
            if ai_response:
                ai_recommendation = ai_response.get("recommendation")
                reasoning = ai_response.get("reasoning")
                confidence = ai_response.get("confidence")
                
                logger.info(
                    f"[{self.agent_name}] AI response received "
                    f"(confidence: {confidence}, time: {response_time_ms:.0f}ms)"
                )
        
        if ai_recommendation:
            is_valid, validation_result, errors = self.validate_recommendation(
                ai_recommendation, context
            )
            
            if is_valid:
                final_recommendation = ai_recommendation
                action_taken = "accepted"
                selected_alternative = None
                
                logger.info(f"[{self.agent_name}] AI recommendation accepted")
            else:
                logger.warning(
                    f"[{self.agent_name}] AI recommendation failed validation: {errors}"
                )
                final_recommendation = self.deterministic_fallback(context)
                action_taken = "fallback"
                selected_alternative = final_recommendation
                is_valid = False
        else:
            logger.info(f"[{self.agent_name}] Using deterministic fallback")
            final_recommendation = self.deterministic_fallback(context)
            action_taken = "fallback"
            selected_alternative = final_recommendation
            is_valid = True
            validation_result = {"fallback": True}
            errors = None
        
        record = AgentRecommendation(
            agent_name=self.agent_name,
            agent_version=self.agent_version,
            request_context_id=request_context_id,
            request_context_type=request_context_type,
            input_data=context,
            recommendation=ai_recommendation or final_recommendation,
            reasoning=reasoning,
            confidence=confidence,
            validation_passed=is_valid,
            validation_result=validation_result,
            validation_errors=errors,
            action_taken=action_taken,
            selected_alternative=selected_alternative,
            bedrock_available=bedrock_available,
            response_time_ms=response_time_ms
        )
        
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        
        logger.info(
            f"[{self.agent_name}] Decision recorded: {record.recommendation_id} "
            f"(action: {action_taken})"
        )
        
        return final_recommendation, record
