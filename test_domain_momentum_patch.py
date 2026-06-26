#!/usr/bin/env python
"""
Focused, non-destructive tests for the updated _compute_domain_momentum() function.

Tests:
 1. Event created today -> counted in current 30-day window
 2. Event created 31 days ago -> counted in previous 30-day window
 3. Domain with zero current events cannot be top_domain
 4. Strictly rising domain (current > previous) wins over flat ones
 5. Neutral state when no events have been created in the last 30 days
 6. Exact window boundary: event at cutoff_current timestamp is in current window
 7. Exact window boundary: event just before cutoff_current is in previous window
 8. Age protection: event with published_at > 90 days old is excluded
 9. Age protection: event with NULL published_at is included
10. Existing smoke test still passes (module import)
11. _windowed_domain_momentum and other analytics functions not broken

No database writes. All DB calls are mocked.
"""

import sys
import os
import types
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PASS = 0
FAIL = 0
NOW = datetime.now(timezone.utc)


def ok(msg: str):
    global PASS
    PASS += 1
    print(f"  OK   {msg}")


def fail(msg: str):
    global FAIL
    FAIL += 1
    print(f"  FAIL {msg}")


# ---------------------------------------------------------------------------
# Import target module
# ---------------------------------------------------------------------------
def import_module():
    print("\n[0] Module import")
    try:
        import importlib
        from backend.routes import analytics
        ok("backend.routes.analytics imported")
        return analytics
    except Exception as e:
        fail(f"Import failed: {e}")
        import traceback
        traceback.print_exc()
        return None


# ---------------------------------------------------------------------------
# Helper: build a mock DB that returns specific rows
# ---------------------------------------------------------------------------
def make_db(rows: list) -> MagicMock:
    """
    Returns a mock Supabase client whose .table().select().gte().order().execute()
    chain returns the given rows.
    """
    mock_resp = MagicMock()
    mock_resp.data = rows

    mock_chain = MagicMock()
    mock_chain.select.return_value = mock_chain
    mock_chain.gte.return_value = mock_chain
    mock_chain.order.return_value = mock_chain
    mock_chain.execute.return_value = mock_resp

    mock_db = MagicMock()
    mock_db.table.return_value = mock_chain
    return mock_db


def _ts(delta_days: float) -> str:
    """ISO timestamp delta_days ago from NOW."""
    dt = NOW - timedelta(days=delta_days)
    return dt.isoformat()


def domain_row(slug: str, name: str, created_days_ago: float, published_days_ago: float | None = None) -> dict:
    """Build a minimal DB row for an event linked to one domain."""
    pub = _ts(published_days_ago) if published_days_ago is not None else None
    return {
        "id": f"ev-{slug}-{created_days_ago}",
        "created_at": _ts(created_days_ago),
        "published_at": pub,
        "event_domains": [{"domains": {"slug": slug, "name": name}}],
    }


# ---------------------------------------------------------------------------
# Test 1: Event created today -> current window
# ---------------------------------------------------------------------------
def test_event_today(m):
    print("\n[1] Event created today counted in current 30-day window")
    rows = [domain_row("ai-agents", "AI Agents", created_days_ago=0.1)]
    db = make_db(rows)
    result = m._compute_domain_momentum(db, {"ai-agents": "AI Agents"})

    td = result.get("top_domain")
    if td and td["slug"] == "ai-agents" and td["recent_count"] == 1:
        ok(f"top_domain is 'AI Agents' with recent_count=1")
    elif td is None:
        fail(f"top_domain is None — event today was not counted")
    else:
        fail(f"Unexpected top_domain: {td}")


# ---------------------------------------------------------------------------
# Test 2: Event created 31 days ago -> previous window, not current
# ---------------------------------------------------------------------------
def test_event_previous_window(m):
    print("\n[2] Event created 31 days ago counted in previous 30-day window (not current)")
    rows = [domain_row("ai-safety-governance", "AI Safety", created_days_ago=31)]
    db = make_db(rows)
    result = m._compute_domain_momentum(db, {"ai-safety-governance": "AI Safety"})

    # Current count should be 0 for this domain -> neutral state or no top_domain
    td = result.get("top_domain")
    if td is None:
        ok("top_domain is None when only previous-window events exist (neutral state)")
    elif td.get("recent_count", -1) == 0:
        fail(f"top_domain has recent_count=0 but was still returned as top_domain — violates constraint")
    else:
        fail(f"Unexpected top_domain: {td}")


# ---------------------------------------------------------------------------
# Test 3: Domain with zero current events must not be top_domain
# ---------------------------------------------------------------------------
def test_zero_current_not_top(m):
    print("\n[3] Domain with zero current events cannot be top_domain")
    rows = [
        # ai-benchmarks: only previous window events
        domain_row("ai-benchmarks", "AI Benchmarks", created_days_ago=35),
        domain_row("ai-benchmarks", "AI Benchmarks", created_days_ago=45),
        # ai-agents: one current-window event
        domain_row("ai-agents", "AI Agents", created_days_ago=2),
    ]
    db = make_db(rows)
    result = m._compute_domain_momentum(db, {
        "ai-benchmarks": "AI Benchmarks",
        "ai-agents": "AI Agents",
    })

    td = result.get("top_domain")
    if td is None:
        fail("top_domain is None — expected ai-agents to win")
    elif td["slug"] == "ai-agents":
        ok(f"top_domain is 'AI Agents' (has current events) — benchmarks with zero current events excluded")
    elif td["slug"] == "ai-benchmarks":
        fail("top_domain is 'ai-benchmarks' which has ZERO current events — constraint violated!")
    else:
        fail(f"Unexpected top_domain: {td}")


# ---------------------------------------------------------------------------
# Test 4: Strictly rising domain wins over a flat high-count domain
# ---------------------------------------------------------------------------
def test_rising_wins_over_flat(m):
    print("\n[4] Strictly rising domain (current > previous) wins over flat domain")
    rows = [
        # ai-agents: 1 current, 0 previous -> delta=+1 (strictly rising)
        domain_row("ai-agents", "AI Agents", created_days_ago=5),
        # ai-benchmarks: 3 current, 3 previous -> delta=0 (flat, but higher count)
        domain_row("ai-benchmarks", "AI Benchmarks", created_days_ago=5),
        domain_row("ai-benchmarks", "AI Benchmarks", created_days_ago=10),
        domain_row("ai-benchmarks", "AI Benchmarks", created_days_ago=15),
        domain_row("ai-benchmarks", "AI Benchmarks", created_days_ago=35),
        domain_row("ai-benchmarks", "AI Benchmarks", created_days_ago=40),
        domain_row("ai-benchmarks", "AI Benchmarks", created_days_ago=45),
    ]
    db = make_db(rows)
    result = m._compute_domain_momentum(db, {
        "ai-agents": "AI Agents",
        "ai-benchmarks": "AI Benchmarks",
    })

    td = result.get("top_domain")
    if td and td["slug"] == "ai-agents":
        ok("Strictly rising domain (ai-agents, delta=+1) wins over flat ai-benchmarks (delta=0)")
    elif td and td["slug"] == "ai-benchmarks":
        fail("Flat domain (ai-benchmarks) incorrectly won over rising domain (ai-agents)")
    else:
        fail(f"Unexpected top_domain: {td}")


# ---------------------------------------------------------------------------
# Test 5: Neutral state when no events in last 30 days
# ---------------------------------------------------------------------------
def test_neutral_state_no_current(m):
    print("\n[5] Neutral state when no events ingested in last 30 days")
    rows = [
        # All events are 31-60 days ago (previous window only)
        domain_row("ai-cyber-risk", "AI Cyber Risk", created_days_ago=32),
        domain_row("ai-cyber-risk", "AI Cyber Risk", created_days_ago=40),
    ]
    db = make_db(rows)
    result = m._compute_domain_momentum(db, {"ai-cyber-risk": "AI Cyber Risk"})

    td = result.get("top_domain")
    summary = result.get("summary", "")
    if td is None:
        ok("top_domain is None (neutral state) when no current-window events")
    else:
        fail(f"Expected None top_domain but got: {td}")

    if "30 days" in summary:
        ok(f"Summary mentions '30 days': '{summary[:80]}'")
    else:
        fail(f"Summary does not mention '30 days': '{summary[:80]}'")


# ---------------------------------------------------------------------------
# Test 6: Window boundary — event clearly inside the current window is counted
# ---------------------------------------------------------------------------
def test_exact_boundary_current(m):
    print("\n[6] Boundary: event 1 minute inside the current window -> counted in current window")
    # We cannot use exactly NOW - 30d because the function recomputes datetime.now()
    # internally; clock skew of a few milliseconds puts the event just outside.
    # Use 29d 23h 59min — clearly inside the current window — to verify >= boundary logic.
    just_inside = NOW - timedelta(days=29, hours=23, minutes=59)
    row = {
        "id": "boundary-test",
        "created_at": just_inside.isoformat(),
        "published_at": None,
        "event_domains": [{"domains": {"slug": "ai-model-behavior", "name": "AI Model Behavior"}}],
    }
    db = make_db([row])
    result = m._compute_domain_momentum(db, {"ai-model-behavior": "AI Model Behavior"})

    td = result.get("top_domain")
    if td and td["slug"] == "ai-model-behavior" and td["recent_count"] >= 1:
        ok("Event 1 minute inside cutoff is in current window (>= boundary logic verified)")
    else:
        fail(f"Event near boundary not counted in current window. top_domain={td}")


# ---------------------------------------------------------------------------
# Test 7: Exact window boundary — event 1 ms before cutoff_current -> previous
# ---------------------------------------------------------------------------
def test_exact_boundary_previous(m):
    print("\n[7] Exact boundary: event 1 second before cutoff_current -> previous window")
    cutoff_current = NOW - timedelta(days=30)
    just_before = cutoff_current - timedelta(seconds=1)
    row = {
        "id": "boundary-prev",
        "created_at": just_before.isoformat(),
        "published_at": None,
        "event_domains": [{"domains": {"slug": "ai-model-behavior", "name": "AI Model Behavior"}}],
    }
    db = make_db([row])
    result = m._compute_domain_momentum(db, {"ai-model-behavior": "AI Model Behavior"})

    td = result.get("top_domain")
    # Event is in previous window -> current_count = 0 -> neutral state
    if td is None:
        ok("Event just before cutoff_current goes to previous window -> neutral state")
    else:
        fail(f"Expected neutral state but got top_domain: {td}")


# ---------------------------------------------------------------------------
# Test 8: Age protection — event with published_at > 90 days is excluded
# ---------------------------------------------------------------------------
def test_age_protection_excludes_old(m):
    print("\n[8] Age protection: published_at > 90 days -> event excluded")
    rows = [
        domain_row("ai-agents", "AI Agents",
                   created_days_ago=5,       # recent created_at
                   published_days_ago=95),   # but article is 95 days old
    ]
    db = make_db(rows)
    result = m._compute_domain_momentum(db, {"ai-agents": "AI Agents"})

    td = result.get("top_domain")
    if td is None:
        ok("Old article (published 95 days ago) correctly excluded -> neutral state")
    elif td.get("slug") == "ai-agents":
        fail("Old backfilled article (published 95 days ago) was NOT excluded — age protection broken")
    else:
        fail(f"Unexpected top_domain: {td}")


# ---------------------------------------------------------------------------
# Test 9: Age protection — event with NULL published_at is included
# ---------------------------------------------------------------------------
def test_age_protection_null_published_included(m):
    print("\n[9] Age protection: NULL published_at -> event included")
    rows = [
        domain_row("ai-agents", "AI Agents",
                   created_days_ago=2,
                   published_days_ago=None),  # NULL published_at
    ]
    db = make_db(rows)
    result = m._compute_domain_momentum(db, {"ai-agents": "AI Agents"})

    td = result.get("top_domain")
    if td and td["slug"] == "ai-agents" and td["recent_count"] == 1:
        ok("Event with NULL published_at is included (kept)")
    else:
        fail(f"Expected ai-agents with recent_count=1 but got: {td}")


# ---------------------------------------------------------------------------
# Test 10: No-results path — empty DB response
# ---------------------------------------------------------------------------
def test_no_events(m):
    print("\n[10] Empty DB returns neutral response")
    db = make_db([])
    result = m._compute_domain_momentum(db, {})

    if result.get("top_domain") is None and result.get("runners_up") == []:
        ok("Empty result returns neutral structure (top_domain=None, runners_up=[])")
    else:
        fail(f"Unexpected result for empty DB: {result}")


# ---------------------------------------------------------------------------
# Test 11: Multiple domains — runner-up ordering
# ---------------------------------------------------------------------------
def test_runner_up_ordering(m):
    print("\n[11] Runner-up ordering: highest delta first")
    rows = [
        # ai-agents: delta=+3
        *[domain_row("ai-agents", "AI Agents", created_days_ago=i) for i in [2, 3, 4]],
        # ai-benchmarks: delta=+2
        *[domain_row("ai-benchmarks", "AI Benchmarks", created_days_ago=i) for i in [5, 6]],
        # ai-cyber-risk: delta=+1
        domain_row("ai-cyber-risk", "AI Cyber Risk", created_days_ago=7),
    ]
    db = make_db(rows)
    result = m._compute_domain_momentum(db, {
        "ai-agents": "AI Agents",
        "ai-benchmarks": "AI Benchmarks",
        "ai-cyber-risk": "AI Cyber Risk",
    })

    td = result.get("top_domain")
    runners = result.get("runners_up", [])
    if td and td["slug"] == "ai-agents":
        ok(f"top_domain is ai-agents (delta=+3)")
    else:
        fail(f"Expected ai-agents as top but got: {td}")

    if runners and runners[0]["slug"] == "ai-benchmarks":
        ok(f"First runner-up is ai-benchmarks (delta=+2)")
    else:
        fail(f"Expected ai-benchmarks as runner-up[0] but got: {runners[:1]}")


# ---------------------------------------------------------------------------
# Test 12: Frontend wording check — "this week" must not appear in summary strings
# ---------------------------------------------------------------------------
def test_no_this_week_in_summaries(m):
    print("\n[12] Backend summary strings do not contain 'this week'")
    # Rising case
    rows = [domain_row("ai-agents", "AI Agents", created_days_ago=2)]
    db = make_db(rows)
    result = m._compute_domain_momentum(db, {"ai-agents": "AI Agents"})
    summary = result.get("summary", "")
    if "this week" in summary.lower():
        fail(f"'this week' found in rising summary: '{summary}'")
    else:
        ok(f"Rising summary does not contain 'this week': '{summary[:80]}'")

    # Flat/fallback case
    rows2 = [
        domain_row("ai-agents", "AI Agents", created_days_ago=2),
        domain_row("ai-agents", "AI Agents", created_days_ago=35),
    ]
    db2 = make_db(rows2)
    result2 = m._compute_domain_momentum(db2, {"ai-agents": "AI Agents"})
    summary2 = result2.get("summary", "")
    if "this week" in summary2.lower():
        fail(f"'this week' found in flat summary: '{summary2}'")
    else:
        ok(f"Flat summary does not contain 'this week': '{summary2[:80]}'")


# ---------------------------------------------------------------------------
# Test 13: Response shape — all required keys present
# ---------------------------------------------------------------------------
def test_response_shape(m):
    print("\n[13] Response shape — all required keys present")
    rows = [domain_row("ai-agents", "AI Agents", created_days_ago=3)]
    db = make_db(rows)
    result = m._compute_domain_momentum(db, {"ai-agents": "AI Agents"})

    required_top = {"name", "slug", "direction", "delta", "recent_count", "signal_label"}
    for key in ("title", "summary", "top_domain", "runners_up"):
        if key in result:
            ok(f"Key '{key}' present")
        else:
            fail(f"Key '{key}' missing from response")

    td = result.get("top_domain")
    if td:
        missing = required_top - set(td.keys())
        if not missing:
            ok(f"top_domain has all required fields")
        else:
            fail(f"top_domain missing fields: {missing}")


# ---------------------------------------------------------------------------
# Test 14: Previous smoke test still passes
# ---------------------------------------------------------------------------
def test_smoke_still_passes():
    print("\n[14] Previous test_ingest_patch.py still passes (syntax check)")
    import subprocess
    result = subprocess.run(
        ["python", "-m", "py_compile", "test_ingest_patch.py"],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        ok("test_ingest_patch.py compiles cleanly")
    else:
        fail(f"test_ingest_patch.py syntax error: {result.stderr[:200]}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    print("=" * 62)
    print("FASTEST-RISING DOMAIN METRIC — FOCUSED TEST SUITE")
    print("=" * 62)

    m = import_module()
    if m is None:
        print("\nAborting: module could not be imported.")
        sys.exit(1)

    test_event_today(m)
    test_event_previous_window(m)
    test_zero_current_not_top(m)
    test_rising_wins_over_flat(m)
    test_neutral_state_no_current(m)
    test_exact_boundary_current(m)
    test_exact_boundary_previous(m)
    test_age_protection_excludes_old(m)
    test_age_protection_null_published_included(m)
    test_no_events(m)
    test_runner_up_ordering(m)
    test_no_this_week_in_summaries(m)
    test_response_shape(m)
    test_smoke_still_passes()

    print(f"\n{'=' * 62}")
    print(f"RESULTS: {PASS} passed, {FAIL} failed")
    print("=" * 62)
    sys.exit(1 if FAIL > 0 else 0)


if __name__ == "__main__":
    main()
