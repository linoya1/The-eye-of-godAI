from fastapi import APIRouter, HTTPException, Query
from backend.models.schemas import Event
from backend.data.mock_data import MOCK_EVENTS

router = APIRouter()

@router.get("/events", response_model=list[Event], tags=["Events"])
def get_events(domain: str | None = Query(default=None, description="Filter by domain slug")):
    """
    Returns AI events. Optionally filtered by domain slug.
    Example: GET /events?domain=ai-cyber-risk
    In production this queries Supabase filtered by the user's selected interests.
    """
    events = [Event(**e) for e in MOCK_EVENTS]
    if domain:
        events = [e for e in events if domain in e.domains]
    return events

@router.get("/events/{event_id}", response_model=Event, tags=["Events"])
def get_event(event_id: str):
    """
    Returns a single event by ID.
    Used by the Event Detail page when a user clicks on an event card.
    """
    for e in MOCK_EVENTS:
        if e["id"] == event_id:
            return Event(**e)
    raise HTTPException(status_code=404, detail=f"Event '{event_id}' not found.")
