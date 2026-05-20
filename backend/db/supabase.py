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
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY")
# Backward-compatible alias used by existing imports.
SUPABASE_KEY = SUPABASE_SERVICE_ROLE_KEY or SUPABASE_ANON_KEY

# Initialize the Supabase client only if the credentials exist
supabase: Client | None = None

if SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY:
    try:
        # Prevent indefinite hanging by adding a 5-second timeout
        options = ClientOptions(postgrest_client_timeout=5)
        supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, options=options)
        logger.info("Supabase client initialized successfully with service-role key and timeout.")
    except Exception as e:
        logger.error(f"Failed to initialize Supabase client: {e}")
        supabase = None
else:
    if SUPABASE_URL and SUPABASE_ANON_KEY and not SUPABASE_SERVICE_ROLE_KEY:
        logger.warning("SUPABASE_SERVICE_ROLE_KEY missing in .env. Privileged database connection not available.")
    else:
        logger.warning("SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY missing in .env. Database connection not available.")

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


def check_event_exists(url: str | None = None, title: str | None = None, published_at: str | None = None) -> bool:
    """
    Check if an event exists by URL, title, or published_at. Returns True if any match.

    This performs safe, best-effort checks and never raises on DB errors (fail-forward).
    """
    db = get_supabase()
    if not db:
        logger.debug("Dedup check: Supabase not connected, allowing insert attempt")
        return False
    try:
        # Check by URL first (fast, indexed)
        if url:
            res = db.table("events").select("id").eq("url", url).limit(1).execute()
            if res.data:
                logger.debug("Dedup check: URL already exists in DB")
                return True

        # Check by title
        if title:
            try:
                res = db.table("events").select("id").eq("title", title).limit(1).execute()
                if res.data:
                    logger.debug("Dedup check: Title already exists in DB")
                    return True
            except Exception:
                # Some DBs may store slightly different title encodings; ignore errors
                pass

        # Check by published_at (exact match)
        if published_at:
            try:
                res = db.table("events").select("id").eq("published_at", published_at).limit(1).execute()
                if res.data:
                    logger.debug("Dedup check: published_at already exists in DB")
                    return True
            except Exception:
                pass

        return False
    except Exception as e:
        logger.warning(f"Dedup check failed: {e}")
        return False

def get_or_create_user_profile(auth_uid: str, email: str | None = None, full_name: str | None = None) -> dict | None:
    """Get or create a user_profiles row for the given Supabase auth UID.

    Returns the user_profiles row as a dict, or None if DB not configured/failed.
    """
    db = get_supabase()
    if not db:
        logger.debug("Supabase not connected: cannot get/create user profile")
        return None

    try:
        # Try to find existing profile by auth_uid
        print(f"[DEBUG supabase.py] Looking for existing profile: auth_uid={auth_uid}")
        res = db.table('user_profiles').select('*').eq('auth_uid', auth_uid).limit(1).execute()
        if res.data and len(res.data) > 0:
            print(f"[DEBUG supabase.py] Found existing profile: {res.data[0]}")
            return res.data[0]

        # Insert new profile
        payload = {'auth_uid': auth_uid, 'email': email, 'full_name': full_name}
        print(f"[DEBUG supabase.py] Creating new profile: {payload}")
        upsert = db.table('user_profiles').insert(payload).execute()
        print(f"[DEBUG supabase.py] Insert response: {upsert.data}")
        if upsert.data and len(upsert.data) > 0:
            print(f"[DEBUG supabase.py] Profile created: {upsert.data[0]}")
            return upsert.data[0]
        print(f"[DEBUG supabase.py] Insert returned empty data")
        return None
    except Exception as e:
        logger.warning(f"Failed to get or create user_profile for {auth_uid}: {e}")
        print(f"[DEBUG supabase.py] Error creating profile: {e}")
        return None


def get_user_interests(user_id: str) -> list[str] | None:
    """Return a list of domain_slugs for the given user_id."""
    db = get_supabase()
    if not db:
        logger.debug("Supabase not connected: cannot get user interests")
        return None

    try:
        res = db.table('user_interests').select('domain_slug').eq('user_id', user_id).execute()
        if res.data is None:
            return []
        return [r['domain_slug'] for r in res.data]
    except Exception as e:
        logger.warning(f"Failed to fetch user_interests for {user_id}: {e}")
        return None


def set_user_interests(user_id: str, domain_slugs: list[str]) -> bool:
    """Replace user interests for user_id with the provided list of domain_slugs.

    This performs a transaction-like replace: delete existing and insert new.
    Returns True on success.
    """
    db = get_supabase()
    if not db:
        logger.debug("Supabase not connected: cannot set user interests")
        return False

    try:
        # Delete existing
        print(f"[DEBUG supabase.py] Deleting existing interests for user_id={user_id}")
        db.table('user_interests').delete().eq('user_id', user_id).execute()

        # Insert new interests
        inserts = []
        for slug in domain_slugs:
            inserts.append({'user_id': user_id, 'domain_slug': slug})

        if inserts:
            print(f"[DEBUG supabase.py] Inserting {len(inserts)} interests: {inserts}")
            result = db.table('user_interests').insert(inserts).execute()
            print(f"[DEBUG supabase.py] Insert result: {result.data}")

        print(f"[DEBUG supabase.py] Interests set successfully for user_id={user_id}")
        return True
    except Exception as e:
        logger.warning(f"Failed to set user_interests for {user_id}: {e}")
        print(f"[DEBUG supabase.py] Error setting interests: {e}")
        return False
