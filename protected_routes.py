"""
Protected Endpoints Example

Demonstrates endpoints that require authentication.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any
from pydantic import BaseModel

from auth import get_current_user
from supabase_config import get_supabase_admin_client

router = APIRouter(prefix="/api", tags=["Protected"])


class UserStats(BaseModel):
    """User statistics response"""
    total_validations: int
    valid_count: int
    invalid_count: int
    avg_execution_time_ms: float


@router.get("/me", response_model=Dict[str, Any])
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """
    Get current authenticated user information.
    
    Requires authentication (JWT or API key).
    """
    return {
        "user_id": current_user.get("id"),
        "email": current_user.get("email"),
        "authenticated": True
    }


@router.get("/stats", response_model=UserStats)
async def get_user_stats(current_user: dict = Depends(get_current_user)):
    """
    Get user's validation statistics.
    
    Requires authentication.
    """
    try:
        client = get_supabase_admin_client()
        user_id = current_user.get("id")
        
        # Get validations (Rolling average of last 500 for stats to save memory)
        result = client.table("validation_requests")\
            .select("is_valid, execution_time_ms")\
            .eq("user_id", user_id)\
            .order("created_at", desc=True)\
            .limit(500)\
            .execute()
        
        validations = result.data
        
        if not validations:
            return UserStats(
                total_validations=0,
                valid_count=0,
                invalid_count=0,
                avg_execution_time_ms=0.0
            )
        
        # Note: 'total' here represents the subset for rolling stats
        subset_count = len(validations)
        valid = sum(1 for v in validations if v["is_valid"])
        invalid = subset_count - valid
        avg_time = sum(v["execution_time_ms"] for v in validations) / subset_count
        
        # Get absolute total count for the user (lightweight)
        total_res = client.table("validation_requests")\
            .select("id", count="exact")\
            .eq("user_id", user_id)\
            .execute()
        total_all_time = total_res.count or 0
        
        return UserStats(
            total_validations=total_all_time,
            valid_count=valid,
            invalid_count=invalid,
            avg_execution_time_ms=round(avg_time, 2)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get stats: {str(e)}"
        )


@router.get("/history", response_model=List[Dict[str, Any]])
async def get_validation_history(
    limit: int = 10,
    current_user: dict = Depends(get_current_user)
):
    """
    Get user's validation history.
    
    Requires authentication.
    """
    try:
        client = get_supabase_admin_client()
        user_id = current_user.get("id")
        
        result = client.table("validation_requests")\
            .select("id, query, is_valid, created_at, execution_time_ms")\
            .eq("user_id", user_id)\
            .order("created_at", desc=True)\
            .limit(limit)\
            .execute()
        
        return result.data
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get history: {str(e)}"
        )
