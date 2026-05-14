import logging
from fastapi import APIRouter, HTTPException, Query
from backend.models.schemas import Event
from backend.data.mock_data import MOCK_EVENTS
from backend.db.supabase import get_supabase

logger = logging.getLogger(__name__)
router = APIRouter()

def map_db_event_to_pydantic(e: dict) -> Event:
    """Maps the flattened Supabase event structure to the nested Pydantic schema."""
    # Handle the source join (Supabase might return it as 'sources')
    source_data = e.get("sources") or {"name": "Unknown", "credibility_score": 0.0}
    
    # Handle the event_domains join
    # Format from Supabase: {"event_domains": [{"domains": {"slug": "ai-cyber-risk"}}]}
    domains_list = []
    for ed in e.get("event_domains", []):
        if ed.get("domains") and ed["domains"].get("slug"):
            domains_list.append(ed["domains"]["slug"])

    return Event(
        id=e["id"],
        title=e["title"],
        summary=e.get("summary", ""),
        url=e["url"],
        published_at=str(e.get("published_at", "")),
        source=source_data,
        domains=domains_list,
        scores={
            "breakthrough_score": float(e.get("breakthrough_score") or 0.0),
            "risk_signal": float(e.get("risk_signal") or 0.0),
            "evidence_level": str(e.get("evidence_level") or ""),
            "impact_areas": e.get("impact_areas") or [],
            "trend_momentum": float(e.get("trend_momentum") or 0.0),
        }
    )

@router.get("/events", response_model=list[Event], tags=["Events"])
def get_events(domain: str | None = Query(default=None, description="Filter by domain slug")):
    """
    Returns AI events. Optionally filtered by domain slug.
    Reads from Supabase if configured, otherwise falls back to mock data.
    """
    db = get_supabase()
    
    if not db:
        events = [Event(**e) for e in MOCK_EVENTS]
        if domain:
            events = [e for e in events if domain in e.domains]
        return events

    try:
        # We need to join sources and event_domains to get the full shape
        logger.info("Executing Supabase query for events: select *, sources(*), event_domains(domains(slug))")
        query = db.table("events").select("*, sources(*), event_domains(domains(slug))").order("published_at", desc=True)
        response = query.execute()
        
        logger.info(f"Successfully fetched {len(response.data)} rows from events table.")
        
        events = []
        for e in response.data:
            # Safely check if joins returned data
            has_source = "sources" in e and e["sources"] is not None
            has_domains = "event_domains" in e and len(e["event_domains"]) > 0
            logger.debug(f"Event ID {e.get('id')}: Source Joined={has_source}, Domains Joined={has_domains}")
            
            mapped_event = map_db_event_to_pydantic(e)
            if domain:
                if domain in mapped_event.domains:
                    events.append(mapped_event)
            else:
                events.append(mapped_event)
                
        return events
        
    except Exception as e:
        logger.error(f"Supabase connection/query failed in /events: {str(e)[:200]}")
        logger.warning("Falling back to mock events due to error.")
        
        # Safe fallback
        events = [Event(**e) for e in MOCK_EVENTS]
        if domain:
            events = [e for e in events if domain in e.domains]
        return events

@router.get("/events/{event_id}", response_model=Event, tags=["Events"])
def get_event(event_id: str):
    """
    Returns a single event by ID.
    """
    db = get_supabase()
    
    if not db:
        for e in MOCK_EVENTS:
            if e["id"] == event_id:
                return Event(**e)
        raise HTTPException(status_code=404, detail=f"Event '{event_id}' not found.")
        
    try:
        response = db.table("events").select("*, sources(*), event_domains(domains(slug))").eq("id", event_id).execute()
        if not response.data:
            raise HTTPException(status_code=404, detail=f"Event '{event_id}' not found.")
            
        return map_db_event_to_pydantic(response.data[0])
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching event {event_id} from Supabase: {e}")
        raise HTTPException(status_code=500, detail="Database error")
