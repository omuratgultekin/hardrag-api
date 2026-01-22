"""
Authentication Middleware for FastAPI

Handles JWT and API key authentication using Supabase.
"""
from fastapi import HTTPException, Security, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, APIKeyHeader
from typing import Optional
import logging

from supabase_config import verify_jwt_token, validate_api_key

logger = logging.getLogger(__name__)

# Security schemes
security_bearer = HTTPBearer(auto_error=False)
security_api_key = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_current_user_jwt(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security_bearer)
) -> Optional[dict]:
    """
    Get current user from JWT token
    
    Args:
        credentials: Bearer token from Authorization header
        
    Returns:
        User data if authenticated, None otherwise
        
    Raises:
        HTTPException: If token is invalid
    """
    if not credentials:
        return None
    
    token = credentials.credentials
    user = verify_jwt_token(token)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


async def get_current_user_api_key(
    api_key: Optional[str] = Security(security_api_key)
) -> Optional[dict]:
    """
    Get current user from API key
    
    Args:
        api_key: API key from X-API-Key header
        
    Returns:
        User data (user_id) if authenticated, None otherwise
        
    Raises:
        HTTPException: If API key is invalid
    """
    if not api_key:
        return None
    
    user_id = await validate_api_key(api_key)
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    return {"user_id": user_id}


async def get_current_user(
    jwt_user: Optional[dict] = Depends(get_current_user_jwt),
    api_key_user: Optional[dict] = Depends(get_current_user_api_key)
) -> dict:
    """
    Get current user from either JWT or API key
    
    Tries JWT first, then API key.
    
    Args:
        jwt_user: User from JWT token
        api_key_user: User from API key
        
    Returns:
        User data
        
    Raises:
        HTTPException: If neither authentication method succeeds
    """
    if jwt_user:
        return jwt_user
    
    if api_key_user:
        return api_key_user
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required. Provide JWT token or API key.",
        headers={"WWW-Authenticate": "Bearer"}
    )


async def get_optional_user(
    jwt_user: Optional[dict] = Depends(get_current_user_jwt),
    api_key_user: Optional[dict] = Depends(get_current_user_api_key)
) -> Optional[dict]:
    """
    Get current user if authenticated, None otherwise
    
    Use this for endpoints that work both with and without authentication.
    
    Args:
        jwt_user: User from JWT token
        api_key_user: User from API key
        
    Returns:
        User data if authenticated, None otherwise
    """
    if jwt_user:
        return jwt_user
    
    if api_key_user:
        return api_key_user
    
    return None
