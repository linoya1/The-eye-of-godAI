#!/usr/bin/env python
"""
Focused, non-destructive tests for the patched ingest_anthropic.py.

Tests:
 1. Syntax / import check
 2. fetch_rss_entries() with a mock that simulates 16 entries in the first source
    -> verifies every source is attempted and per-source limit is respected
 3. Round-robin / fair ordering
 4. In-run URL deduplication
 5. Defensive content handling (message.content is None or empty)
 6. Title-based fallback when article content is short
 7. generate_summary_with_groq() with a real API call (skipped when key absent)

No records are inserted into the production database.
"""

import sys
import os
import json
import importlib
import types
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PASS = 0
FAIL = 0


def ok(msg: str):
    global PASS
    PASS += 1
    print(f"  OK  {msg}")


def fail(msg: str):
    global FAIL
    FAIL += 1
    print(f"  FAIL {msg}")


# ---------------------------------------------------------------------------
# Test 1: module imports without crashing
# ---------------------------------------------------------------------------
def test_import():
    print("\n[1] Module import")
    try:
        from backend import ingest_anthropic as m
        ok("backend.ingest_anthropic imported successfully")
        return m
    except Exception as e:
        fail(f"Import failed: {e}")
        import traceback
        traceback.print_exc()
        return None


# ---------------------------------------------------------------------------
# Helper: build a fake feedparser entry
# ---------------------------------------------------------------------------
def make_entry(title: str, link: str, source_id: str = "s5", source_name: str = "Test Source"):
    e = types.SimpleNamespace(
        title=title,
        link=link,
        summary="Some summary text",
        published="2026-01-01T00:00:00",
        content=None,
    )
    e._source_id = source_id
    e._source_name = source_name
    return e


def make_feed(entries):
    f = types.SimpleNamespace(entries=entries, bozo=False)
    return f


# ---------------------------------------------------------------------------
# Test 2: per-source limit -- first source with 16 entries must not block others
# ---------------------------------------------------------------------------
def test_per_source_limit(m):
    print("\n[2] Per-source limit and all-sources-attempted")
    from backend.ingest_anthropic import FEED_SOURCES, MAX_ARTICLES_PER_SOURCE

    # Build a feedparser.parse stub that returns different sizes per source
    call_count = [0]
    source_names_called = []

    def fake_parse(url):
        src = FEED_SOURCES[call_count[0] % len(FEED_SOURCES)]
        source_names_called.append(src["name"])
        call_count[0] += 1

        if src["name"] == "Anthropic Research":
            # Simulate 16 entries -- much more than MAX_ARTICLES_PER_SOURCE
            entries = [
                make_entry(f"Article {i}", f"https://anthropic.com/article-{i}", "s5", "Anthropic Research")
                for i in range(16)
            ]
        elif src["name"] in ("Anthropic Engineering", "Anthropic News"):
            entries = [
                make_entry(f"Eng {i}", f"https://anthropic.com/eng-{i}", "s5", src["name"])
                for i in range(3)
            ]
        else:
            entries = [
                make_entry(f"Other {i}", f"https://example.com/{src['source_id']}-{i}", src["source_id"], src["name"])
                for i in range(2)
            ]

        return make_feed(entries)

    with patch("feedparser.parse", side_effect=fake_parse):
        results = m.fetch_rss_entries()

    total_sources = len(FEED_SOURCES)
    if len(source_names_called) == total_sources:
        ok(f"All {total_sources} sources were attempted (called feedparser.parse {len(source_names_called)} times)")
    else:
        fail(f"Only {len(source_names_called)}/{total_sources} sources were attempted: {source_names_called}")

    # Check that Anthropic Research contributed at most MAX_ARTICLES_PER_SOURCE
    anthropic_count = sum(
        1 for e in results
        if getattr(e, "_source_name", "") == "Anthropic Research"
    )
    if anthropic_count <= MAX_ARTICLES_PER_SOURCE:
        ok(f"Anthropic Research contributed {anthropic_count} entries (<= MAX_ARTICLES_PER_SOURCE={MAX_ARTICLES_PER_SOURCE})")
    else:
        fail(f"Anthropic Research contributed {anthropic_count} entries (> MAX_ARTICLES_PER_SOURCE={MAX_ARTICLES_PER_SOURCE})")

    # Check that multiple sources are represented
    source_set = {getattr(e, "_source_name", "?") for e in results}
    if len(source_set) > 1:
        ok(f"Multiple sources represented in results: {source_set}")
    else:
        fail(f"Only one source represented: {source_set}")

    return results


# ---------------------------------------------------------------------------
# Test 3: round-robin ordering -- first candidate should not all be from source 0
# ---------------------------------------------------------------------------
def test_round_robin_ordering(m):
    print("\n[3] Round-robin / interleaved ordering")
    from backend.ingest_anthropic import FEED_SOURCES, MAX_ARTICLES_PER_SOURCE

    call_idx = [0]

    def fake_parse_even(url):
        src = FEED_SOURCES[call_idx[0] % len(FEED_SOURCES)]
        call_idx[0] += 1
        entries = [
            make_entry(f"{src['name']} art {i}", f"https://x.com/{src['source_id']}-{i}", src["source_id"], src["name"])
            for i in range(MAX_ARTICLES_PER_SOURCE)
        ]
        return make_feed(entries)

    with patch("feedparser.parse", side_effect=fake_parse_even):
        results = m.fetch_rss_entries()

    if len(results) >= 2:
        first_src = getattr(results[0], "_source_name", "?")
        second_src = getattr(results[1], "_source_name", "?")
        if first_src != second_src:
            ok(f"Round-robin confirmed: results[0] is '{first_src}', results[1] is '{second_src}'")
        else:
            fail(f"First two results are both from '{first_src}' -- round-robin may not be working")
    else:
        fail(f"Too few results to verify ordering ({len(results)} returned)")


# ---------------------------------------------------------------------------
# Test 4: in-run URL deduplication
# ---------------------------------------------------------------------------
def test_url_deduplication(m):
    print("\n[4] In-run URL deduplication")
    from backend.ingest_anthropic import FEED_SOURCES, MAX_ARTICLES_PER_SOURCE

    call_idx = [0]
    DUPE_URL = "https://shared.com/duplicate-article"

    def fake_parse_dup(url):
        src = FEED_SOURCES[call_idx[0] % len(FEED_SOURCES)]
        call_idx[0] += 1
        entries = [
            make_entry(DUPE_URL, DUPE_URL, src["source_id"], src["name"]),  # same URL in every source
            make_entry(f"Unique {src['name']}", f"https://unique.com/{src['source_id']}", src["source_id"], src["name"]),
        ]
        return make_feed(entries)

    with patch("feedparser.parse", side_effect=fake_parse_dup):
        results = m.fetch_rss_entries()

    dupe_count = sum(1 for e in results if getattr(e, "link", "") == DUPE_URL)
    if dupe_count == 1:
        ok(f"Duplicate URL appeared only once in results (dedup working)")
    else:
        fail(f"Duplicate URL appeared {dupe_count} times in results")


# ---------------------------------------------------------------------------
# Test 5: Defensive handling when message.content is None
# ---------------------------------------------------------------------------
def test_empty_content_fallback(m):
    print("\n[5] Defensive handling of None message.content")

    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = None  # <-- None
    mock_response.choices[0].finish_reason = "stop"
    mock_response.usage = None

    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_response

    title = "Claude 4 Achieves Record Benchmark"
    article_content = "Anthropic released Claude 4 today with significant improvements in reasoning ability."
    result = m.generate_summary_with_groq(mock_client, title, article_content)

    if result and len(result) > 0:
        ok(f"Fallback returned non-empty result ({len(result)} chars): '{result[:80]}'")
    else:
        fail(f"Fallback returned empty/None: {repr(result)}")

    # Verify it is NOT None or empty string
    if result is None:
        fail("Result is None -- critical failure")
    elif result.strip() == "":
        fail("Result is blank -- critical failure")
    else:
        ok("Result is not None and not blank")


# ---------------------------------------------------------------------------
# Test 6: Empty-string content fallback
# ---------------------------------------------------------------------------
def test_empty_string_content_fallback(m):
    print("\n[6] Defensive handling of empty-string message.content")

    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = ""  # <-- empty string
    mock_response.choices[0].finish_reason = "stop"
    mock_response.usage = None

    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_response

    title = "OpenAI Announces o4"
    article_content = "OpenAI has announced the next generation model with improved capabilities."
    result = m.generate_summary_with_groq(mock_client, title, article_content)

    if result and len(result) > 0:
        ok(f"Fallback for empty-string content returned ({len(result)} chars): '{result[:80]}'")
    else:
        fail(f"Fallback for empty string returned empty/None: {repr(result)}")


# ---------------------------------------------------------------------------
# Test 7: Title-based stub when article content is too short
# ---------------------------------------------------------------------------
def test_title_stub_fallback(m):
    print("\n[7] Title-based stub when article content < 20 chars")
    mock_client = MagicMock()
    result = m.generate_summary_with_groq(mock_client, "AI Breakthrough Today", "short")
    if "latest update" in result.lower() or "source" in result.lower():
        ok(f"Title-based stub returned (no Groq call made): '{result}'")
    else:
        fail(f"Expected title-based stub, got: '{result}'")
    # Confirm Groq was NOT called
    if not mock_client.chat.completions.create.called:
        ok("Groq API was NOT called for short content (expected)")
    else:
        fail("Groq API was unexpectedly called for short content")


# ---------------------------------------------------------------------------
# Test 8: AI keyword detection is not broken
# ---------------------------------------------------------------------------
def test_ai_keyword_detection(m):
    print("\n[8] AI keyword detection")
    # Positive case
    if m.has_ai_keywords("New Claude Model Released", "Anthropic releases Claude 4 with enhanced AI capabilities"):
        ok("Keyword match: 'claude' detected")
    else:
        fail("Keyword match failed for obvious AI content")

    # Negative case
    if not m.has_ai_keywords("Cooking Tips", "How to make pasta in 30 minutes with fresh ingredients"):
        ok("Non-AI content correctly rejected")
    else:
        fail("Non-AI content incorrectly accepted")


# ---------------------------------------------------------------------------
# Test 9: Live Groq API call (skipped when key absent)
# ---------------------------------------------------------------------------
def test_live_groq_summary(m):
    print("\n[9] Live Groq API call (skipped when GROQ_API_KEY absent)")
    from dotenv import load_dotenv
    from pathlib import Path
    load_dotenv(dotenv_path=Path("backend/.env"))
    key = os.getenv("GROQ_API_KEY")
    if not key:
        print("  SKIP  GROQ_API_KEY not set -- skipping live Groq test")
        return

    try:
        from groq import Groq
        client = Groq(api_key=key)
        title = "Anthropic Releases Claude"
        content = (
            "Anthropic today released a new version of Claude with improved reasoning and coding abilities. "
            "The model demonstrates state-of-the-art performance on several benchmarks including MMLU and HumanEval."
        )
        result = m.generate_summary_with_groq(client, title, content)

        if result and len(result.strip()) > 0:
            ok(f"Live Groq summary returned {len(result)} chars: '{result[:100]}'")
        else:
            fail(f"Live Groq returned empty summary: {repr(result)}")

        # Ensure no reasoning leakage (reasoning format="hidden" should suppress it)
        suspicious_phrases = ["<think>", "</think>", "let me think", "i need to analyze"]
        leaked = [p for p in suspicious_phrases if p.lower() in result.lower()]
        if not leaked:
            ok("No reasoning text leaked into the summary")
        else:
            fail(f"Possible reasoning text found in summary: {leaked}")

    except Exception as e:
        fail(f"Live Groq call raised: {e}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    print("=" * 60)
    print("INGEST ANTHROPIC PATCH -- FOCUSED TEST SUITE")
    print("=" * 60)

    m = test_import()
    if m is None:
        print("\nAborting: module could not be imported.")
        sys.exit(1)

    test_per_source_limit(m)
    test_round_robin_ordering(m)
    test_url_deduplication(m)
    test_empty_content_fallback(m)
    test_empty_string_content_fallback(m)
    test_title_stub_fallback(m)
    test_ai_keyword_detection(m)
    test_live_groq_summary(m)

    print(f"\n{'=' * 60}")
    print(f"RESULTS: {PASS} passed, {FAIL} failed")
    print("=" * 60)
    sys.exit(1 if FAIL > 0 else 0)


if __name__ == "__main__":
    main()
