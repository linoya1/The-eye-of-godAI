import logging
from fastapi import APIRouter
from backend.models.schemas import Domain
from backend.data.mock_data import MOCK_DOMAINS
from backend.db.supabase import get_supabase

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/domains", response_model=list[Domain], tags=["Domains"])
def get_domains():
    """
    Returns all AI domains.
    Tries to fetch from Supabase. If missing, empty, or errors out, returns mock data.
    """
    db = get_supabase()
    
    if not db:
        logger.warning("No Supabase client found. Falling back to mock domains.")
        return [Domain(**d) for d in MOCK_DOMAINS]
        
    try:
        logger.info("Executing Supabase query: select * from domains")
        response = db.table("domains").select("*").execute()
        
        # If Supabase table is completely empty, it might be uninitialized.
        if not response.data:
            logger.warning("Supabase domains table is empty. Returning mock data.")
            return [Domain(**d) for d in MOCK_DOMAINS]
            
        return [Domain(**d) for d in response.data]
    except Exception as e:
        logger.error(f"Supabase connection/query failed: {str(e)[:100]}")
        logger.warning("Falling back to mock domains due to error.")
        return [Domain(**d) for d in MOCK_DOMAINS]
