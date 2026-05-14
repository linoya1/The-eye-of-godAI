from fastapi import APIRouter
from backend.models.schemas import Insight
from backend.data.mock_data import MOCK_INSIGHTS
from backend.db.supabase import get_supabase

router = APIRouter()

@router.get("/insights", response_model=list[Insight], tags=["Insights"])
def get_insights():
    """
    Returns daily domain insight summaries.
    Reads from Supabase if configured, otherwise falls back to mock data.
    """
    db = get_supabase()
    
    if not db:
        return [Insight(**i) for i in MOCK_INSIGHTS]
        
    try:
        # Join with domains table to get the human-readable domain name
        response = db.table("insights").select("*, domains(name)").order("date", desc=True).execute()
        
        insights = []
        for i in response.data:
            # Map the flat DB row + join into the Pydantic shape
            domain_name = "Unknown Domain"
            if i.get("domains") and i["domains"].get("name"):
                domain_name = i["domains"]["name"]
                
            insights.append(Insight(
                domain_slug=i["domain_slug"],
                domain_name=domain_name,
                summary_text=i["summary_text"],
                top_event_ids=i.get("top_event_ids") or [],
                momentum_delta=float(i.get("momentum_delta") or 0.0),
                date=i.get("date", "")
            ))
            
        return insights
        
    except Exception as e:
        print(f"Error fetching insights from Supabase: {e}")
        return []
