import os
from dotenv import load_dotenv
from supabase import create_client, Client, ClientOptions
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Load environment variables from backend/.env
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_ANON_KEY")

# Initialize the Supabase client only if the credentials exist
supabase: Client | None = None

if SUPABASE_URL and SUPABASE_KEY:
    try:
        # Prevent indefinite hanging by adding a 5-second timeout
        options = ClientOptions(postgrest_client_timeout=5)
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY, options=options)
        logger.info("Supabase client initialized successfully with timeout.")
    except Exception as e:
        logger.error(f"Failed to initialize Supabase client: {e}")
        supabase = None
else:
    logger.warning("SUPABASE_URL or SUPABASE_KEY missing in .env. Database connection not available.")

def get_supabase() -> Client | None:
    """Returns the initialized Supabase client, or None if not configured."""
    return supabase


def check_event_exists_by_url(url: str) -> bool:
    """
    Check if an event with the given URL already exists in the database.
    Used by ingestion pipeline for deduplication.
    
    Args:
        url (str): Event URL to check
    
    Returns:
        bool: True if event exists, False otherwise
    
    This is a SAFE deduplication check:
    - If DB is down, returns False (allows insert attempt to fail gracefully)
    - If URL is malformed, returns False (allows insert attempt)
    - Only queries one row (SELECT id LIMIT 1 is fast)
    """
    db = get_supabase()
    if not db:
        logger.debug(f"Dedup check: Supabase not connected, allowing insert attempt")
        return False
    
    try:
        result = db.table("events").select("id").eq("url", url).limit(1).execute()
        exists = len(result.data) > 0
        if exists:
            logger.debug(f"Dedup check: URL already exists in DB")
        return exists
    except Exception as e:
        # Log but don't fail: if dedup check fails, allow insert attempt (fail-forward)
        logger.warning(f"Dedup check failed for URL {url}: {e}")
        return False
