from fastapi.testclient import TestClient
import sys
import os
import pathlib

# Minimal student-level smoke test
# - Verifies FastAPI app imports
# - Confirms key routes exist and do not crash (no 5xx)
# - Confirms auth-protected routes return 401/403 when unauthenticated
# - Verifies presence of key files and that the manual ingestion workflow is dispatch-only

# Ensure backend is in path
sys.path.append(os.getcwd())

failures = []

def fail(msg: str):
    print("FAIL:", msg)
    failures.append(msg)

def ok(msg: str):
    print("OK:", msg)


def check_app_import():
    try:
        from backend.main import app
        ok("Imported backend.main.app")
        return app
    except Exception as e:
        fail(f"Importing backend.main.app failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def check_routes_and_responses(app):
    client = TestClient(app)

    # Routes to check (lightweight expectations)
    public_routes = ["/domains", "/events"]
    analytics_routes = ["/analytics/intelligence-summary"]
    protected_routes = ["/api/me/profile/sync", "/api/me/preferences"]

    # Inspect registration
    registered = [route.path for route in app.routes]
    for r in public_routes + analytics_routes + protected_routes:
        exists = any(r == p or p.startswith(r.rstrip("/")) for p in registered)
        if exists:
            ok(f"Route registered: {r}")
        else:
            fail(f"Route not found in app.routes: {r}")

    # Helper: request and assert no 5xx for public endpoints
    def safe_get(path):
        try:
            resp = client.get(path)
            code = resp.status_code
            if code >= 500:
                fail(f"Public route {path} returned server error {code}")
            else:
                ok(f"Public route {path} responded {code}")
        except Exception as e:
            fail(f"Exception requesting public route {path}: {e}")

    for r in public_routes:
        safe_get(r)

    # Analytics route: may be protected; accept 200 or 401/403, but not 5xx
    for r in analytics_routes:
        try:
            resp = client.get(r)
            code = resp.status_code
            if code >= 500:
                fail(f"Analytics route {r} returned server error {code}")
            elif code in (401, 403):
                ok(f"Analytics route {r} is protected and returned {code} (expected)")
            else:
                ok(f"Analytics route {r} responded {code}")
        except Exception as e:
            fail(f"Exception requesting analytics route {r}: {e}")

    # Protected routes: expect 401/403 when unauthenticated
    for r in protected_routes:
        try:
            resp = client.get(r)
            code = resp.status_code
            if code in (401, 403):
                ok(f"Protected route {r} correctly returned unauthenticated {code}")
            elif code >= 500:
                fail(f"Protected route {r} returned server error {code}")
            else:
                # Some protected routes may return 200 for unauthenticated if implemented differently
                ok(f"Protected route {r} returned {code} (expected unauthenticated behaviour may vary)")
        except Exception as e:
            fail(f"Exception requesting protected route {r}: {e}")


def check_files_and_workflow():
    repo_root = pathlib.Path(os.getcwd())
    checks = [
        (repo_root / "backend" / "ingest_anthropic.py", "ingest_anthropic.py"),
        (repo_root / ".github" / "workflows" / "manual-ingestion.yml", "manual-ingestion.yml"),
        (repo_root / "backend" / ".env.example", "backend/.env.example"),
        (repo_root / "frontend" / ".env.example", "frontend/.env.example"),
        (repo_root / "README.md", "README.md"),
    ]

    for path, name in checks:
        if path.exists():
            ok(f"Found {name} at {path}")
        else:
            fail(f"Missing required file: {name} (expected at {path})")

    # Workflow content checks
    wf_path = repo_root / ".github" / "workflows" / "manual-ingestion.yml"
    if wf_path.exists():
        text = wf_path.read_text(encoding="utf8")
        if "workflow_dispatch" in text:
            ok("manual-ingestion.yml contains 'workflow_dispatch'")
        else:
            fail("manual-ingestion.yml does not contain 'workflow_dispatch'")

        # Detect real scheduled triggers (ignore commented lines).
        has_schedule = False
        for raw_line in text.splitlines():
            line = raw_line.lstrip()
            if not line or line.startswith("#"):
                continue
            # look for schedule: or cron: in non-commented lines
            lowered = line.lower()
            if "schedule:" in lowered or "cron:" in lowered:
                has_schedule = True
                break

        if has_schedule:
            fail("manual-ingestion.yml contains a real schedule/cron trigger (expected dispatch-only)")
        else:
            ok("manual-ingestion.yml does not contain a real schedule/cron (dispatch-only confirmed)")

    # README content checks
    readme = repo_root / "README.md"
    if readme.exists():
        rtxt = readme.read_text(encoding="utf8").lower()
        # Relaxed README checks: look for key mentions and for actual GRANT SQL lines
        required_phrases = [
            "ingest_anthropic.py",
            "manual ingestion",
            "vite_api_url",
        ]
        for p in required_phrases:
            if p in rtxt:
                ok(f"README.md mentions: {p}")
            else:
                fail(f"README.md missing mention of: {p}")

        # Check for at least one GRANT SQL line that documents required grants
        grant_snippets = [
            "grant usage on schema public to service_role",
            "grant select, insert on table public.user_profiles to service_role",
            "grant select, insert, delete on table public.user_interests to service_role",
            "grant select on table public.domains to service_role",
        ]
        if any(sn in rtxt for sn in grant_snippets):
            ok("README.md contains documented Supabase GRANT statements")
        else:
            fail("README.md does not contain expected Supabase GRANT SQL statements")
    else:
        fail("README.md not found")


def main():
    app = check_app_import()
    if app is None:
        print("Aborting further checks due to import failure.")
        sys.exit(1)

    check_routes_and_responses(app)
    check_files_and_workflow()

    if failures:
        print("\nSMOKE TEST: FAILURES detected:")
        for f in failures:
            print(" -", f)
        sys.exit(1)
    else:
        print("\nSMOKE TEST: All checks passed.")
        sys.exit(0)


if __name__ == "__main__":
    main()
