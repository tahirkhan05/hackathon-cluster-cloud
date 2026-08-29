"""
API Key Authentication for Node Agents.

MVP Security:
- Simple API key validation
- Keys stored in environment variables
- Basic request authentication

Production Needs:
- Key rotation
- Per-node keys
- Key revocation
- Rate limiting per key
- Encrypted key storage
"""
import secrets
import hashlib
from typing import Optional
from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
from config import settings

# API Key header scheme
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def generate_api_key() -> str:
    """
    Generate a secure random API key.
    
    Returns 32-byte hex string (64 characters).
    """
    return secrets.token_hex(32)


def hash_api_key(api_key: str) -> str:
    """
    Hash API key for storage.
    
    Uses SHA-256. In production, use bcrypt or Argon2.
    """
    return hashlib.sha256(api_key.encode()).hexdigest()


def verify_api_key(api_key: str) -> bool:
    """
    Verify API key against allowed keys.
    
    MVP: Checks single master key from environment.
    Production: Check per-node keys from database.
    """
    if not api_key:
        return False
    
    # MVP: Single master key for all nodes
    master_key = settings.NODE_API_KEY
    if not master_key:
        return True  # If no key configured, allow (development only)
    
    return secrets.compare_digest(api_key, master_key)


async def validate_node_api_key(api_key: str = Security(api_key_header)) -> str:
    """
    FastAPI dependency for API key validation.
    
    Usage:
        @router.post("/protected")
        async def endpoint(api_key: str = Depends(validate_node_api_key)):
            # Endpoint logic
    
    Raises HTTPException if invalid.
    """
    if not verify_api_key(api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    return api_key


class OptionalAPIKeyValidation:
    """
    Optional API key validation.
    
    Returns None if no key provided, validates if present.
    Useful for endpoints that support both authenticated and unauthenticated access.
    """
    
    async def __call__(self, api_key: Optional[str] = Security(api_key_header)) -> Optional[str]:
        if not api_key:
            return None
        
        if not verify_api_key(api_key):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key",
            )
        
        return api_key
