from fastapi import APIRouter
from backend.models.schemas import Domain
from backend.data.mock_data import MOCK_DOMAINS

router = APIRouter()

@router.get("/domains", response_model=list[Domain], tags=["Domains"])
def get_domains():
    """
    Returns all 8 AI domains.
    The frontend uses this to render the Interest Questionnaire and Dashboard filters.
    In production this will come from the Supabase ai_domains table.
    """
    return [Domain(**d) for d in MOCK_DOMAINS]
