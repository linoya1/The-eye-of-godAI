import logging
from fastapi import APIRouter, HTTPException
from backend.models.schemas import Domain
from backend.db.supabase import get_supabase

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/domains", response_model=list[Domain], tags=["Domains"])
def get_domains():
    """
    Returns all AI domains from Supabase.
    """
    db = get_supabase()
    
    if not db:
        logger.error("No Supabase client found.")
        raise HTTPException(status_code=500, detail="Database connection not configured")
        
    try:
        logger.info("Executing Supabase query: select * from domains")
        response = db.table("domains").select("*").execute()
        
        return [Domain(**d) for d in response.data]
    except Exception as e:
        logger.error(f"Supabase connection/query failed: {str(e)[:100]}")
        raise HTTPException(status_code=500, detail="Failed to fetch domains from database")
