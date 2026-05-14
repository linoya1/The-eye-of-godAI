from fastapi import APIRouter
from backend.models.schemas import HealthResponse

router = APIRouter()

@router.get("/health", response_model=HealthResponse, tags=["System"])
def health_check():
    """
    Health check endpoint.
    Used to verify the backend is running and reachable.
    The frontend can call this on startup to confirm the API is alive.
    """
    return HealthResponse(
        status="ok",
        version="0.1.0",
        message="The Eye of GodAI backend is running.",
    )
