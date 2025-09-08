from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from app.services.activity_service import activity_service
from app.schemas.analytics import RecentActivitiesResponse

router = APIRouter()

@router.get("/recent", response_model=RecentActivitiesResponse)
async def get_recent_activities(
    limit: Optional[int] = 10
):
    """
    Get recent activities across all services
    
    Returns the latest activities including account logins, proxy usage, and task executions
    """
    try:
        activities = await activity_service.get_recent_activities(limit)
        return RecentActivitiesResponse(
            activities=activities,
            total_count=len(activities)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching recent activities: {str(e)}"
        )