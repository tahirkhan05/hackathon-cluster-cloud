"""
AWS Bedrock client wrapper.

Handles connection to Bedrock with fallback and error handling.
"""
import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class BedrockClient:
    """
    AWS Bedrock client for Claude interactions.
    
    Handles:
    - Connection initialization
    - Structured prompt/response
    - Error handling
    - Graceful fallback when unavailable
    """
    
    def __init__(
        self,
        aws_region: str,
        model_id: str = "anthropic.claude-3-sonnet-20240229-v1:0",
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None
    ):
        self.aws_region = aws_region
        self.model_id = model_id
        self.available = False
        self.client = None
        
        try:
            import boto3
            
            # Initialize bedrock runtime client
            session_kwargs = {
                "region_name": aws_region
            }
            
            if aws_access_key_id and aws_secret_access_key:
                session_kwargs["aws_access_key_id"] = aws_access_key_id
                session_kwargs["aws_secret_access_key"] = aws_secret_access_key
            
            self.client = boto3.client("bedrock-runtime", **session_kwargs)
            self.available = True
            
            logger.info(f"[BEDROCK] Client initialized (region: {aws_region}, model: {model_id})")
            
        except ImportError:
            logger.warning("[BEDROCK] boto3 not installed, using fallback mode")
            self.available = False
            
        except Exception as e:
            logger.warning(f"[BEDROCK] Initialization failed: {e} (fallback mode)")
            self.available = False
    
    def is_available(self) -> bool:
        """Check if Bedrock is available."""
        return self.available
    
    def invoke(
        self,
        system_prompt: str,
        user_message: str,
        max_tokens: int = 2048,
        temperature: float = 0.7
    ) -> Optional[str]:
        """
        Invoke Claude via Bedrock.
        
        Args:
            system_prompt: System instructions
            user_message: User message/query
            max_tokens: Maximum tokens in response
            temperature: Response temperature (0-1)
            
        Returns:
            Claude's response text, or None if failed
        """
        if not self.available:
            logger.debug("Bedrock not available, skipping invocation")
            return None
        
        try:
            # Construct request payload
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": max_tokens,
                "temperature": temperature,
                "system": system_prompt,
                "messages": [
                    {
                        "role": "user",
                        "content": user_message
                    }
                ]
            }
            
            # Invoke model
            response = self.client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(request_body)
            )
            
            # Parse response
            response_body = json.loads(response['body'].read())
            
            # Extract text from response
            if "content" in response_body and len(response_body["content"]) > 0:
                return response_body["content"][0]["text"]
            
            logger.warning("No content in Bedrock response")
            return None
            
        except Exception as e:
            logger.error(f"Bedrock invocation failed: {e}", exc_info=True)
            return None
    
    def invoke_structured(
        self,
        system_prompt: str,
        user_message: str,
        response_schema: Dict[str, Any],
        max_tokens: int = 2048
    ) -> Optional[Dict[str, Any]]:
        """
        Invoke Claude and parse structured JSON response.
        
        Args:
            system_prompt: System instructions
            user_message: User message with JSON request
            response_schema: Expected JSON schema (for documentation)
            max_tokens: Maximum tokens
            
        Returns:
            Parsed JSON dict, or None if failed
        """
        # Add JSON formatting instruction
        enhanced_system = f"{system_prompt}\n\nRespond ONLY with valid JSON matching this schema: {json.dumps(response_schema)}"
        
        response_text = self.invoke(
            system_prompt=enhanced_system,
            user_message=user_message,
            max_tokens=max_tokens,
            temperature=0.3  # Lower temperature for structured output
        )
        
        if not response_text:
            return None
        
        # Parse JSON from response
        try:
            # Try to find JSON in response (handle markdown code blocks)
            text = response_text.strip()
            
            # Remove markdown code blocks if present
            if text.startswith("```json"):
                text = text[7:]
            elif text.startswith("```"):
                text = text[3:]
            
            if text.endswith("```"):
                text = text[:-3]
            
            text = text.strip()
            
            # Parse JSON
            parsed = json.loads(text)
            return parsed
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from Claude response: {e}")
            logger.debug(f"Raw response: {response_text}")
            return None


# Global singleton instance (lazy initialized)
_bedrock_client: Optional[BedrockClient] = None


def get_bedrock_client() -> BedrockClient:
    """
    Get global Bedrock client instance.
    
    Lazy initialization on first call.
    """
    global _bedrock_client
    
    if _bedrock_client is None:
        from config import settings
        
        _bedrock_client = BedrockClient(
            aws_region=settings.AWS_REGION,
            model_id=settings.BEDROCK_MODEL_ID,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
    
    return _bedrock_client
