"""
Supabase Configuration and Utilities

Handles Supabase client initialization, authentication, and database operations.
"""
import os
from typing import Optional
from supabase import create_client, Client
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)

# Environment variables (set these in .env)
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")


@lru_cache()
def get_supabase_client() -> Client:
    """
    Get Supabase client (cached singleton)
    
    Returns:
        Supabase client instance
    """
    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        raise ValueError(
            "SUPABASE_URL and SUPABASE_ANON_KEY environment variables required"
        )
    
    client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    logger.info("Supabase client initialized")
    return client


@lru_cache()
def get_supabase_admin_client() -> Client:
    """
    Get Supabase admin client with service role key
    
    Use this for server-side operations that bypass RLS.
    
    Returns:
        Supabase admin client instance
    """
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        raise ValueError(
            "SUPABASE_URL and SUPABASE_SERVICE_KEY environment variables required"
        )
    
    client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    logger.info("Supabase admin client initialized")
    return client


def verify_jwt_token(token: str) -> Optional[dict]:
    """
    Verify Supabase JWT token
    
    Args:
        token: JWT token from Authorization header
        
    Returns:
        User data if valid, None otherwise
    """
    try:
        client = get_supabase_client()
        # Supabase handles JWT verification automatically
        user = client.auth.get_user(token)
        if user:
            return user.user.model_dump()
        return None
    except Exception as e:
        logger.error(f"JWT verification failed: {e}")
        return None


async def log_validation_request(
    user_id: str,
    query: str,
    output: str,
    is_valid: bool,
    violations: list,
    execution_time_ms: float,
    metadata: Optional[dict] = None
) -> bool:
    """
    Log validation request to Supabase database
    
    Args:
        user_id: User ID from JWT
        query: Original query
        output: LLM output
        is_valid: Validation result
        violations: List of violations
        execution_time_ms: Execution time
        metadata: Optional metadata
        
    Returns:
        True if logged successfully, False otherwise
    """
    try:
        client = get_supabase_admin_client()
        
        data = {
            "user_id": user_id,
            "query": query,
            "output": output,
            "is_valid": is_valid,
            "violations": violations,
            "execution_time_ms": execution_time_ms,
            "metadata": metadata or {}
        }
        
        result = client.table("validation_requests").insert(data).execute()
        logger.info(f"Validation request logged for user {user_id}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to log validation request: {e}")
        return False


async def get_user_api_key(user_id: str) -> Optional[str]:
    """
    Get user's API key from Supabase
    
    Args:
        user_id: User ID
        
    Returns:
        API key if found, None otherwise
    """
    try:
        client = get_supabase_admin_client()
        result = client.table("api_keys").select("key").eq("user_id", user_id).eq("is_active", True).execute()
        
        if result.data and len(result.data) > 0:
            return result.data[0]["key"]
        return None
        
    except Exception as e:
        logger.error(f"Failed to get API key: {e}")
        return None


async def validate_api_key(api_key: str) -> Optional[str]:
    """
    Validate API key and return user_id
    
    Args:
        api_key: API key to validate
        
    Returns:
        User ID if valid, None otherwise
    """
    try:
        client = get_supabase_admin_client()
        result = client.table("api_keys").select("user_id").eq("key", api_key).eq("is_active", True).execute()
        
        if result.data and len(result.data) > 0:
            return result.data[0]["user_id"]
        return None
        
    except Exception as e:
        logger.error(f"Failed to validate API key: {e}")
        return None


async def increment_api_usage(user_id: str, endpoint: str):
    """
    Increment API usage counter for rate limiting
    
    Args:
        user_id: User ID
        endpoint: API endpoint called
    """
    try:
        client = get_supabase_admin_client()
        
        # Insert usage record
        data = {
            "user_id": user_id,
            "endpoint": endpoint,
            "timestamp": "now()"
        }
        
        client.table("api_usage").insert(data).execute()
        logger.debug(f"API usage incremented for user {user_id}")
        
    except Exception as e:
        logger.error(f"Failed to increment API usage: {e}")
