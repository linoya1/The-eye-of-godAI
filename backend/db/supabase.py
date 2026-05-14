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
    print("Warning: SUPABASE_URL or SUPABASE_KEY missing in .env. Using fallback data.")

def get_supabase() -> Client | None:
    """Returns the initialized Supabase client, or None if not configured."""
    return supabase
