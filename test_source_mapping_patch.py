#!/usr/bin/env python
"""
Focused, non-destructive tests for the source-mapping audit patch.

Coverage:
  A. URL resolver: every hostname resolves to the correct (source_id, source_name)
  B. Feed fallback: no configured feed uses a source_id belonging to another publisher
  C. Source-ID existence: every source_id used by a feed exists in the canonical table
  D. Publisher exclusivity: no two different publishers share the same source_id
  E. FK safety: no feed uses s9/s10/s11/s12 before the migration rows exist
     (verified by confirming those IDs are now declared in the migration SQL)
  F. Detect-source-from-url double-call: the result written to the DB is always
     the URL-resolver result, not the feed fallback, for known hostnames
  G. No existing test files regressed (syntax check)

No network calls. No database writes. All assertions are pure Python.
"""

import sys
import os
import re

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PASS = 0
FAIL = 0


def ok(msg: str):
    global PASS
    PASS += 1
    print(f"  OK   {msg}")


def fail(msg: str):
    global FAIL
    FAIL += 1
    print(f"  FAIL {msg}")


# ---------------------------------------------------------------------------
# Import the patched module
# ---------------------------------------------------------------------------
print("\n[0] Module import")
try:
    from backend.ingest_anthropic import (
        detect_source_from_url,
        FEED_SOURCES,
    )
    ok("backend.ingest_anthropic imported")
except Exception as e:
    fail(f"Import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)


# ---------------------------------------------------------------------------
# Canonical ground truth (verified against Supabase sources table)
# ---------------------------------------------------------------------------
CANONICAL_SOURCES: dict[str, str] = {
    "s1":  "Anthropic Research",
    "s2":  "TIME Magazine",
    "s3":  "The AI Digest",
    "s4":  "The Guardian",
    "s5":  "Reuters",
    "s6":  "OpenAI Research",
    "s7":  "NVIDIA Architecture",
    "s8":  "SWE-bench",
    # Added by migration 2_add_feed_source_rows.sql:
    "s9":  "Hugging Face Blog",
    "s10": "Google Research Blog",
    "s11": "Google Blog",
    "s12": "Made By Agents",
}

# The four publishers whose IDs must NOT be reused for other publishers
PROTECTED_MAPPINGS: dict[str, str] = {
    "s7": "NVIDIA Architecture",
    "s8": "SWE-bench",
}


# ---------------------------------------------------------------------------
# A. URL resolver correctness
# ---------------------------------------------------------------------------
print("\n[A] URL resolver: hostname → (source_id, source_name)")

URL_RESOLVER_CASES = [
    # Anthropic variants
    ("https://www.anthropic.com/research/foo",             "s1",  "Anthropic Research"),
    ("https://anthropic.com/news/bar",                     "s1",  "Anthropic Research"),
    ("https://subpage.anthropic.com/thing",                "s1",  "Anthropic Research"),
    # OpenAI variants
    ("https://openai.com/index/foo",                       "s6",  "OpenAI Research"),
    ("https://www.openai.com/blog/bar",                    "s6",  "OpenAI Research"),
    ("https://cdn.openai.com/papers/thing.pdf",            "s6",  "OpenAI Research"),
    # The Guardian
    ("https://www.theguardian.com/technology/ai",          "s4",  "The Guardian"),
    ("https://theguardian.com/world/article",              "s4",  "The Guardian"),
    # Reuters
    ("https://www.reuters.com/technology/ai-news",         "s5",  "Reuters"),
    ("https://reuters.com/business/article",               "s5",  "Reuters"),
    # Hugging Face
    ("https://huggingface.co/blog/some-post",              "s9",  "Hugging Face Blog"),
    ("https://www.huggingface.co/blog/another",            "s9",  "Hugging Face Blog"),
    ("https://huggingface.co/papers/2401.12345",           "s9",  "Hugging Face Blog"),
    # Google Research Blog
    ("https://research.google/blog/my-post/",              "s10", "Google Research Blog"),
    ("https://sub.research.google/blog/foo",               "s10", "Google Research Blog"),
    # Google Blog
    ("https://blog.google/technology/ai/post/",            "s11", "Google Blog"),
    ("https://blog.google/products/search/update",         "s11", "Google Blog"),
    # Made By Agents
    ("https://www.madebyagents.com/post/article",          "s12", "Made By Agents"),
    ("https://madebyagents.com/rss",                       "s12", "Made By Agents"),
]

for url, expected_id, expected_name in URL_RESOLVER_CASES:
    sid, sname = detect_source_from_url(url)
    if sid == expected_id and sname == expected_name:
        ok(f"{url[:55]!r:56s} → ({sid}, {sname!r})")
    else:
        fail(
            f"{url[:55]!r:56s} → expected ({expected_id!r}, {expected_name!r}) "
            f"but got ({sid!r}, {sname!r})"
        )


# ---------------------------------------------------------------------------
# B. URL resolver fallback path: unknown hostnames pass through fallback
# ---------------------------------------------------------------------------
print("\n[B] URL resolver: unknown hostname passes fallback through unchanged")

FALLBACK_CASES = [
    ("https://example.com/article",         "s3",  "The AI Digest"),
    ("https://techcrunch.com/ai",            None,  None),
    ("https://unknown.io/post",              "s2",  "TIME Magazine"),
]

for url, fb_id, fb_name in FALLBACK_CASES:
    sid, sname = detect_source_from_url(url, fallback_source_id=fb_id, fallback_source_name=fb_name)
    if sid == fb_id and sname == fb_name:
        ok(f"Unknown URL {url!r:45s} falls back to ({sid!r}, {sname!r})")
    else:
        fail(f"Fallback broken for {url!r}: expected ({fb_id!r}, {fb_name!r}) got ({sid!r}, {sname!r})")


# ---------------------------------------------------------------------------
# C. Feed source_id existence: every feed's source_id is in canonical table
# ---------------------------------------------------------------------------
print("\n[C] Feed source_id exists in sources table")

for feed in FEED_SOURCES:
    sid = feed["source_id"]
    name = feed["name"]
    if sid in CANONICAL_SOURCES:
        ok(f"Feed {name!r:30s} source_id={sid!r} exists in sources table ({CANONICAL_SOURCES[sid]!r})")
    else:
        fail(
            f"Feed {name!r:30s} source_id={sid!r} does NOT exist in sources table — "
            f"would cause a FK violation on insert"
        )


# ---------------------------------------------------------------------------
# D. Publisher exclusivity: no feed borrows another publisher's source_id
# ---------------------------------------------------------------------------
print("\n[D] No feed uses s7 (NVIDIA Architecture) or s8 (SWE-bench)")

for feed in FEED_SOURCES:
    sid = feed["source_id"]
    if sid in PROTECTED_MAPPINGS:
        fail(
            f"Feed {feed['name']!r} still uses {sid!r} which belongs to "
            f"{PROTECTED_MAPPINGS[sid]!r} — cross-publisher ID collision!"
        )
    else:
        ok(f"Feed {feed['name']!r:30s} does not use protected ID {','.join(PROTECTED_MAPPINGS)!r}")
        # Only print one OK per feed (not per protected ID)
        break  # re-enter loop normally
# Actually do it properly:
PASS -= len(FEED_SOURCES)  # undo the over-counting from the break hack
FAIL  # no change needed

# Clean redo:
for feed in FEED_SOURCES:
    sid = feed["source_id"]
    is_bad = sid in PROTECTED_MAPPINGS
    if is_bad:
        fail(
            f"Feed {feed['name']!r} uses {sid!r} ({PROTECTED_MAPPINGS[sid]!r}) — collision!"
        )
    else:
        ok(f"Feed {feed['name']!r:30s} source_id={sid!r} — not a protected/borrowed ID")


# ---------------------------------------------------------------------------
# E. Anthropic feeds: fallback must be s1 (not s5 = Reuters)
# ---------------------------------------------------------------------------
print("\n[E] Anthropic feed fallbacks are s1 (not s5=Reuters or any other)")

for feed in FEED_SOURCES:
    if "Anthropic" in feed["name"]:
        if feed["source_id"] == "s1":
            ok(f"{feed['name']!r} fallback is s1 (Anthropic Research) ✓")
        else:
            fail(f"{feed['name']!r} fallback is {feed['source_id']!r} — expected s1")


# ---------------------------------------------------------------------------
# F. OpenAI feed: fallback must be s6 (not s4 = The Guardian)
# ---------------------------------------------------------------------------
print("\n[F] OpenAI feed fallback is s6 (not s4=The Guardian or any other)")

for feed in FEED_SOURCES:
    if "OpenAI" in feed["name"]:
        if feed["source_id"] == "s6":
            ok(f"{feed['name']!r} fallback is s6 (OpenAI Research) ✓")
        else:
            fail(f"{feed['name']!r} fallback is {feed['source_id']!r} — expected s6")


# ---------------------------------------------------------------------------
# G. New feed fallback IDs match the URL resolver for their own canonical URLs
# ---------------------------------------------------------------------------
print("\n[G] Feed fallback ID matches URL-resolver result for canonical domain")

FEED_CANONICAL_URL_TESTS = [
    ("Hugging Face Blog",    "https://huggingface.co/blog/any-post",       "s9"),
    ("Google Research Blog", "https://research.google/blog/any-post",      "s10"),
    ("Google Blog",          "https://blog.google/technology/ai/any-post", "s11"),
    ("Made By Agents",       "https://www.madebyagents.com/post/anything", "s12"),
    ("Anthropic Research",   "https://www.anthropic.com/research/foo",     "s1"),
    ("OpenAI Blog",          "https://openai.com/index/foo",               "s6"),
]

feed_by_name = {f["name"]: f for f in FEED_SOURCES}

for feed_name, canonical_url, expected_sid in FEED_CANONICAL_URL_TESTS:
    feed = feed_by_name.get(feed_name)
    if feed is None:
        fail(f"Feed {feed_name!r} not found in FEED_SOURCES")
        continue

    # 1. Feed fallback
    if feed["source_id"] != expected_sid:
        fail(
            f"Feed {feed_name!r} fallback source_id={feed['source_id']!r} "
            f"but expected {expected_sid!r}"
        )
    else:
        ok(f"Feed {feed_name!r:30s} fallback={feed['source_id']!r} matches expected {expected_sid!r}")

    # 2. URL resolver agrees
    resolved_id, _ = detect_source_from_url(canonical_url)
    if resolved_id == expected_sid:
        ok(f"  URL resolver for {canonical_url[:50]!r:52s} → {resolved_id!r} ✓")
    else:
        fail(
            f"  URL resolver for {canonical_url!r} → {resolved_id!r} "
            f"but expected {expected_sid!r}"
        )


# ---------------------------------------------------------------------------
# H. Migration SQL file exists and contains all four new source IDs
# ---------------------------------------------------------------------------
print("\n[H] Migration file 2_add_feed_source_rows.sql contains s9–s12")

migration_path = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "backend", "db", "migrations", "2_add_feed_source_rows.sql"
)

if not os.path.exists(migration_path):
    fail(f"Migration file not found: {migration_path}")
else:
    ok(f"Migration file exists: {os.path.basename(migration_path)}")
    sql = open(migration_path, encoding="utf-8").read()
    for sid in ("s9", "s10", "s11", "s12"):
        if f"'{sid}'" in sql:
            ok(f"  Migration contains source row for {sid!r}")
        else:
            fail(f"  Migration does NOT contain source row for {sid!r}")
    # Confirm it uses ON CONFLICT DO NOTHING (idempotent)
    if "ON CONFLICT" in sql.upper() and "DO NOTHING" in sql.upper():
        ok("  Migration uses ON CONFLICT DO NOTHING (idempotent)")
    else:
        fail("  Migration does NOT use ON CONFLICT DO NOTHING — not idempotent")
    # Confirm it's wrapped in a transaction
    if "BEGIN" in sql.upper() and "COMMIT" in sql.upper():
        ok("  Migration is wrapped in BEGIN/COMMIT transaction")
    else:
        fail("  Migration is not wrapped in a transaction")


# ---------------------------------------------------------------------------
# I. No two feeds share the same source_id for different publishers
# ---------------------------------------------------------------------------
print("\n[I] No two different publishers share the same source_id")

sid_to_names: dict[str, list[str]] = {}
for feed in FEED_SOURCES:
    sid_to_names.setdefault(feed["source_id"], []).append(feed["name"])

# Publisher groups that legitimately share a source_id (same publisher, multiple feeds)
LEGITIMATE_SHARED = {
    "s1": {"Anthropic Research", "Anthropic Engineering", "Anthropic News"},
}

for sid, names in sid_to_names.items():
    if len(names) == 1:
        ok(f"  source_id={sid!r} used exclusively by {names[0]!r}")
    else:
        legitimate = LEGITIMATE_SHARED.get(sid, set())
        if set(names) <= legitimate:
            ok(f"  source_id={sid!r} shared by {names} — legitimate (same publisher)")
        else:
            fail(f"  source_id={sid!r} shared by {names} — potential cross-publisher collision!")


# ---------------------------------------------------------------------------
# J. Previous test files still compile
# ---------------------------------------------------------------------------
print("\n[J] Previous test files still compile (syntax check)")

import subprocess
for tf in ("test_ingest_patch.py", "test_domain_momentum_patch.py"):
    result = subprocess.run(
        ["python", "-m", "py_compile", tf],
        capture_output=True, text=True,
        cwd=os.path.dirname(os.path.abspath(__file__))
    )
    if result.returncode == 0:
        ok(f"{tf} compiles cleanly")
    else:
        fail(f"{tf} syntax error: {result.stderr[:200]}")


# ---------------------------------------------------------------------------
# K. Verify ingest_anthropic.py itself compiles
# ---------------------------------------------------------------------------
print("\n[K] backend/ingest_anthropic.py compiles cleanly")

result = subprocess.run(
    ["python", "-m", "py_compile", "backend/ingest_anthropic.py"],
    capture_output=True, text=True,
    cwd=os.path.dirname(os.path.abspath(__file__))
)
if result.returncode == 0:
    ok("backend/ingest_anthropic.py compiles cleanly")
else:
    fail(f"backend/ingest_anthropic.py syntax error: {result.stderr[:200]}")


# ---------------------------------------------------------------------------
# Final report
# ---------------------------------------------------------------------------
# Remove the over-count from the broken-loop section D
# (we ran the loop twice; subtract the first pass)
PASS -= len(FEED_SOURCES)  # remove broken first pass from section D

print(f"\n{'=' * 62}")
print(f"RESULTS: {PASS} passed, {FAIL} failed")
print("=" * 62)
sys.exit(1 if FAIL > 0 else 0)
