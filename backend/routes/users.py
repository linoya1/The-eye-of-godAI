from fastapi import APIRouter, Request, HTTPException, status, Depends
from pydantic import BaseModel
import requests

from backend.db.supabase import get_or_create_user_profile, get_user_interests, set_user_interests, get_supabase, SUPABASE_URL

router = APIRouter(prefix="/api/me", tags=["users"])


class PreferencesIn(BaseModel):
    interests: list[str]


def get_current_user_from_token(request: Request) -> dict:
    """Validate Supabase access token by calling Supabase /auth/v1/user endpoint.

    Returns dict with keys 'id', 'email', 'user_metadata' etc., or raises HTTPException.
    """
    auth = request.headers.get('authorization') or request.headers.get('Authorization')
    if not auth or not auth.lower().startswith('bearer '):
        print("[DEBUG users.py] Missing Authorization header")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Authorization header")
    token = auth.split(' ', 1)[1]
    print(f"[DEBUG users.py] Authorization header found, token length: {len(token)}")

    # Call Supabase auth endpoint to validate token
    try:
        url = SUPABASE_URL.rstrip('/') + '/auth/v1/user'
        print(f"[DEBUG users.py] Validating token at {url}")
        resp = requests.get(url, headers={'Authorization': f'Bearer {token}'}, timeout=5)
        print(f"[DEBUG users.py] Token validation response: {resp.status_code}")
        if resp.status_code != 200:
            print(f"[DEBUG users.py] Token validation failed: {resp.text}")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        user_data = resp.json()
        print(f"[DEBUG users.py] Token validated for user: {user_data.get('email')}")
        return user_data
    except HTTPException:
        raise
    except Exception as e:
        print(f"[DEBUG users.py] Token validation error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get('/preferences')
def read_preferences(request: Request, user: dict = Depends(get_current_user_from_token)):
    """Return the current user's saved domain interests."""
    auth_uid = user.get('id')
    email = user.get('email')
    profile = get_or_create_user_profile(auth_uid, email=email)
    if not profile:
        raise HTTPException(status_code=500, detail='Unable to access user profile')

    interests = get_user_interests(profile['id'])
    if interests is None:
        raise HTTPException(status_code=500, detail='Unable to fetch interests')

    return {'user_id': profile['id'], 'interests': interests}


@router.post('/preferences')
def update_preferences(payload: PreferencesIn, request: Request, user: dict = Depends(get_current_user_from_token)):
    """Set the user's domain preferences. Expects a JSON array of domain slugs.

    Validates domain slugs against `domains` table before inserting.
    """
    auth_uid = user.get('id')
    email = user.get('email')
    full_name = user.get('user_metadata', {}).get('full_name') if user.get('user_metadata') else None
    print(f"[DEBUG users.py] POST /preferences - auth_uid={auth_uid}, email={email}, full_name={full_name}")

    profile = get_or_create_user_profile(auth_uid, email=email, full_name=full_name)
    print(f"[DEBUG users.py] Profile created/fetched: {profile}")
    if not profile:
        print(f"[DEBUG users.py] Failed to create/fetch profile")
        raise HTTPException(status_code=500, detail='Unable to access user profile')

    # Validate domain slugs
    db = get_supabase()
    if not db:
        print(f"[DEBUG users.py] Database not configured")
        raise HTTPException(status_code=500, detail='Database not configured')

    requested = payload.interests
    print(f"[DEBUG users.py] Requested interests: {requested}")
    # Fetch existing domain slugs
    try:
        res = db.table('domains').select('slug').in_('slug', requested).execute()
        valid = [r['slug'] for r in res.data] if res.data else []
        print(f"[DEBUG users.py] Valid domain slugs after validation: {valid}")
    except Exception as e:
        print(f"[DEBUG users.py] Domain validation failed: {e}")
        raise HTTPException(status_code=500, detail=f'Failed to validate domains: {e}')

    # Only use valid slugs
    if not set(valid).issuperset(set(requested)):
        invalid = list(set(requested) - set(valid))
        print(f"[DEBUG users.py] Invalid domain slugs: {invalid}")
        raise HTTPException(status_code=400, detail={'invalid_domains': invalid})

    ok = set_user_interests(profile['id'], valid)
    print(f"[DEBUG users.py] set_user_interests result: {ok}")
    if not ok:
        print(f"[DEBUG users.py] Failed to set preferences")
        raise HTTPException(status_code=500, detail='Failed to set preferences')

    print(f"[DEBUG users.py] Preferences saved successfully for user_id={profile['id']}")
    return {'user_id': profile['id'], 'interests': valid}
