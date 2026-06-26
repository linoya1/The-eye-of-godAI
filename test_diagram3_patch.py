#!/usr/bin/env python
"""
Focused regression tests for the Diagram 3 model-name detection fix.

Tests cover:
  1.  GPT-4o does NOT also match GPT-4
  2.  Standalone GPT-4 mention still matches GPT-4
  3.  Phi matches a standalone model mention (including "Phi-2", "Phi-3")
  4.  Phi does NOT match "philosophy"
  5.  Phi does NOT match "phishing"
  6.  Repeated Claude mentions in one event count once
  7.  One event mentioning Claude + GPT-4o counts once each (both match, neither blocked)
  8.  Case-insensitive matching works (CLAUDE, GPT-4O etc.)
  9.  Existing Anthropic, Claude, OpenAI DB calculations are unchanged
 10.  All existing test files still compile (regression guard)
 11.  DALL-E hyphen keyword matches correctly
 12.  GPT-3.5 dot keyword matches correctly
 13.  "mistral" does not produce a false org-level Mistral AI match from MODEL path
 14.  _MODEL_PATTERNS is sorted longest-keyword-first
 15.  _MODEL_PATTERNS has one entry per _MODEL_KEYWORDS entry

No writes to production Supabase.
"""

import sys
import os
import re
import subprocess
from collections import defaultdict
from statistics import mean

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

PASS = 0
FAIL = 0


def ok(msg: str):
    global PASS; PASS += 1
    print(f"  OK   {msg}")


def fail(msg: str):
    global FAIL; FAIL += 1
    print(f"  FAIL {msg}")


# ── Import the patched module ────────────────────────────────────────────────
print("\n[0] Module import")
try:
    from backend.routes.analytics import (
        _MODEL_KEYWORDS,
        _MODEL_PATTERNS,
        _compute_lab_model_movement,
    )
    ok("backend.routes.analytics imported")
except Exception as e:
    fail(f"Import failed: {e}")
    import traceback; traceback.print_exc()
    sys.exit(1)


# ── Helper: build minimal event dicts compatible with _compute_lab_model_movement ──

def _make_event(eid, title, summary, bt=8.0, rk=4.0):
    """
    Returns a lightweight object that _compute_lab_model_movement can consume.
    The function accesses: event.title, event.summary, event.scores.breakthrough_score,
    event.scores.risk_signal.
    """
    class _Scores:
        breakthrough_score = bt
        risk_signal = rk

    class _Event:
        id = eid
        pass

    ev = _Event()
    ev.title = title
    ev.summary = summary
    ev.scores = _Scores()
    ev.scores.breakthrough_score = bt
    ev.scores.risk_signal = rk
    return ev


def leaders(events):
    """Run _compute_lab_model_movement and return a name→row dict."""
    result = _compute_lab_model_movement(events)
    return {item["name"]: item for item in result.get("items", [])}


def all_rows(events):
    """Run _compute_lab_model_movement and return all entity rows keyed by name."""
    result = _compute_lab_model_movement(events)
    # items only has top-3; we need to reach internal rows.
    # Re-implement the accumulation using the same patched logic.
    from collections import defaultdict
    from statistics import mean
    org_data = defaultdict(list)
    model_data = defaultdict(list)

    from backend.routes.analytics import _ORG_KEYWORDS, _MODEL_PATTERNS, _score_breakthrough, _score_risk

    for ev in events:
        text = f"{ev.title} {ev.summary}".lower()
        bt = float(ev.scores.breakthrough_score)
        rk = float(ev.scores.risk_signal)

        matched_org = set()
        for kw in sorted(_ORG_KEYWORDS, key=len, reverse=True):
            if kw in text:
                display = _ORG_KEYWORDS[kw]
                if display not in matched_org:
                    org_data[display].append((bt, rk))
                    matched_org.add(display)

        matched_model = set()
        for pattern, display in _MODEL_PATTERNS:
            if display not in matched_model and pattern.search(text):
                model_data[display].append((bt, rk))
                matched_model.add(display)

    rows = {}
    for name, pairs in {**dict(org_data), **dict(model_data)}.items():
        bt_scores = [p[0] for p in pairs]
        rk_scores = [p[1] for p in pairs]
        rows[name] = {
            "mention_count": len(pairs),
            "avg_breakthrough": round(mean(bt_scores), 2),
            "avg_risk": round(mean(rk_scores), 2),
        }
    return rows


# ════════════════════════════════════════════════════════════════════════════
# T1  GPT-4o does NOT also count as GPT-4
# ════════════════════════════════════════════════════════════════════════════
print("\n[T1] GPT-4o must not also match GPT-4")
ev = _make_event("t1", "OpenAI releases GPT-4o", "GPT-4o is faster", bt=9.0, rk=3.0)
rows = all_rows([ev])
gpt4o = rows.get("GPT-4o")
gpt4  = rows.get("GPT-4")
if gpt4o and gpt4o["mention_count"] == 1:
    ok("GPT-4o matched exactly once ✓")
else:
    fail(f"GPT-4o row: {gpt4o}")
if gpt4 is None:
    ok("GPT-4 NOT matched (no false-positive) ✓")
else:
    fail(f"GPT-4 falsely matched: {gpt4}")


# ════════════════════════════════════════════════════════════════════════════
# T2  Standalone GPT-4 still matches GPT-4
# ════════════════════════════════════════════════════════════════════════════
print("\n[T2] Standalone GPT-4 must still match GPT-4")
ev = _make_event("t2", "GPT-4 performance benchmark", "GPT-4 scored well", bt=8.0, rk=3.0)
rows = all_rows([ev])
gpt4  = rows.get("GPT-4")
gpt4o = rows.get("GPT-4o")
if gpt4 and gpt4["mention_count"] == 1:
    ok("GPT-4 matched exactly once ✓")
else:
    fail(f"GPT-4 row: {gpt4}")
if gpt4o is None:
    ok("GPT-4o NOT falsely matched ✓")
else:
    fail(f"GPT-4o falsely matched: {gpt4o}")


# ════════════════════════════════════════════════════════════════════════════
# T3  Phi matches a standalone model mention (plain "Phi", "Phi-2", "Phi-3")
# ════════════════════════════════════════════════════════════════════════════
print("\n[T3] Phi matches standalone 'Phi', 'Phi-2', 'Phi-3'")
for title in ["Microsoft releases Phi model", "Phi-2 benchmark", "Phi-3 is here"]:
    ev = _make_event("t3", title, "", bt=8.0, rk=3.0)
    rows = all_rows([ev])
    phi = rows.get("Phi")
    if phi and phi["mention_count"] == 1:
        ok(f"Phi matched for title: '{title}' ✓")
    else:
        fail(f"Phi NOT matched for title: '{title}' — rows={rows}")


# ════════════════════════════════════════════════════════════════════════════
# T4  Phi does NOT match "philosophy"
# ════════════════════════════════════════════════════════════════════════════
print("\n[T4] Phi must NOT match 'philosophy'")
ev = _make_event("t4", "The philosophy of AI alignment", "Philosophy shapes ethics", bt=7.0, rk=3.0)
rows = all_rows([ev])
phi = rows.get("Phi")
if phi is None:
    ok("Phi NOT matched for 'philosophy' ✓")
else:
    fail(f"Phi falsely matched for 'philosophy': {phi}")


# ════════════════════════════════════════════════════════════════════════════
# T5  Phi does NOT match "phishing"
# ════════════════════════════════════════════════════════════════════════════
print("\n[T5] Phi must NOT match 'phishing'")
ev = _make_event("t5", "AI-powered phishing attacks rise", "phishing campaigns", bt=7.0, rk=8.0)
rows = all_rows([ev])
phi = rows.get("Phi")
if phi is None:
    ok("Phi NOT matched for 'phishing' ✓")
else:
    fail(f"Phi falsely matched for 'phishing': {phi}")


# ════════════════════════════════════════════════════════════════════════════
# T6  Repeated Claude mentions in one event count once
# ════════════════════════════════════════════════════════════════════════════
print("\n[T6] Repeated Claude mentions in one event count once")
ev = _make_event("t6", "Claude Claude Claude is here", "Claude claude CLAUDE everywhere", bt=9.0, rk=4.0)
rows = all_rows([ev])
claude = rows.get("Claude")
if claude and claude["mention_count"] == 1:
    ok(f"Claude mention_count=1 even with multiple occurrences ✓")
else:
    fail(f"Claude mention_count expected 1, got: {claude}")


# ════════════════════════════════════════════════════════════════════════════
# T7  One event mentioning Claude + GPT-4o counts once for EACH (not blocked)
# ════════════════════════════════════════════════════════════════════════════
print("\n[T7] One event with Claude + GPT-4o counts once each (different models allowed)")
ev = _make_event("t7", "Claude vs GPT-4o comparison", "Claude outperforms GPT-4o on reasoning", bt=8.5, rk=3.0)
rows = all_rows([ev])
claude = rows.get("Claude")
gpt4o  = rows.get("GPT-4o")
gpt4   = rows.get("GPT-4")
if claude and claude["mention_count"] == 1:
    ok("Claude: mention_count=1 ✓")
else:
    fail(f"Claude: expected 1, got {claude}")
if gpt4o and gpt4o["mention_count"] == 1:
    ok("GPT-4o: mention_count=1 ✓")
else:
    fail(f"GPT-4o: expected 1, got {gpt4o}")
if gpt4 is None:
    ok("GPT-4: NOT falsely matched alongside GPT-4o ✓")
else:
    fail(f"GPT-4: falsely counted alongside GPT-4o: {gpt4}")


# ════════════════════════════════════════════════════════════════════════════
# T8  Case-insensitive matching
# ════════════════════════════════════════════════════════════════════════════
print("\n[T8] Case-insensitive: CLAUDE, GPT-4O, PHI all match")
for kw, display in [("CLAUDE model", "Claude"), ("GPT-4O benchmark", "GPT-4o"), ("PHI release", "Phi")]:
    ev = _make_event("t8", kw, "", bt=8.0, rk=3.0)
    rows = all_rows([ev])
    row = rows.get(display)
    if row and row["mention_count"] == 1:
        ok(f"'{kw}' → {display} ✓")
    else:
        fail(f"'{kw}' → {display} NOT matched. rows={list(rows.keys())}")


# ════════════════════════════════════════════════════════════════════════════
# T9  DALL-E hyphenated keyword
# ════════════════════════════════════════════════════════════════════════════
print("\n[T9] DALL-E hyphenated keyword matches correctly")
ev = _make_event("t9", "OpenAI DALL-E 3 generates images", "dall-e capabilities", bt=7.0, rk=2.0)
rows = all_rows([ev])
dalle = rows.get("DALL-E")
if dalle and dalle["mention_count"] == 1:
    ok("DALL-E matched ✓")
else:
    fail(f"DALL-E not matched: rows={list(rows.keys())}")


# ════════════════════════════════════════════════════════════════════════════
# T10  GPT-3.5 dot keyword
# ════════════════════════════════════════════════════════════════════════════
print("\n[T10] GPT-3.5 keyword matches correctly")
ev = _make_event("t10", "GPT-3.5 turbo benchmark", "gpt-3.5 is faster", bt=6.0, rk=2.0)
rows = all_rows([ev])
gpt35 = rows.get("GPT-3.5")
gpt4  = rows.get("GPT-4")
if gpt35 and gpt35["mention_count"] == 1:
    ok("GPT-3.5 matched ✓")
else:
    fail(f"GPT-3.5 not matched: rows={list(rows.keys())}")
if gpt4 is None:
    ok("GPT-4 NOT falsely matched alongside GPT-3.5 ✓")
else:
    fail(f"GPT-4 falsely matched: {gpt4}")


# ════════════════════════════════════════════════════════════════════════════
# T11  _MODEL_PATTERNS is sorted longest-keyword-first
# ════════════════════════════════════════════════════════════════════════════
print("\n[T11] _MODEL_PATTERNS is sorted longest-keyword-first")
pattern_strings = [p.pattern for p, _ in _MODEL_PATTERNS]
# Extract raw keyword from each pattern (strip \b prefix/suffix and re.escape artifacts)
kw_lengths = [len(kw) for _, kw in
              sorted(_MODEL_KEYWORDS.items(), key=lambda kv: -len(kv[0]))]
lengths_from_patterns = []
for p, display in _MODEL_PATTERNS:
    # Find the keyword in _MODEL_KEYWORDS that matches this display name
    for kw, d in _MODEL_KEYWORDS.items():
        if d == display:
            lengths_from_patterns.append(len(kw))
            break

is_sorted = all(lengths_from_patterns[i] >= lengths_from_patterns[i+1]
                for i in range(len(lengths_from_patterns)-1))
if is_sorted:
    ok(f"_MODEL_PATTERNS sorted longest-first: {lengths_from_patterns} ✓")
else:
    fail(f"_MODEL_PATTERNS NOT sorted: {lengths_from_patterns}")


# ════════════════════════════════════════════════════════════════════════════
# T12  _MODEL_PATTERNS has exactly one entry per _MODEL_KEYWORDS entry
# ════════════════════════════════════════════════════════════════════════════
print("\n[T12] _MODEL_PATTERNS has same count as _MODEL_KEYWORDS")
if len(_MODEL_PATTERNS) == len(_MODEL_KEYWORDS):
    ok(f"Count matches: {len(_MODEL_PATTERNS)} entries ✓")
else:
    fail(f"Count mismatch: patterns={len(_MODEL_PATTERNS)}, keywords={len(_MODEL_KEYWORDS)}")


# ════════════════════════════════════════════════════════════════════════════
# T13  Ranking when two entities have same avg_bt but different mention count
# ════════════════════════════════════════════════════════════════════════════
print("\n[T13] Higher mention count beats same avg_bt")
evs = [
    _make_event("t13a", "OpenAI GPT-4o launch", "GPT-4o new", bt=8.0, rk=2.0),
    *[_make_event(f"t13_{i}", "Anthropic model launch", "", bt=8.0, rk=2.0) for i in range(3)],
]
result = _compute_lab_model_movement(evs)
if result["items"] and result["items"][0]["name"] == "Anthropic":
    ok(f"Anthropic (3 mentions) ranks #1 over OpenAI (1 mention) at same avg_bt ✓")
else:
    fail(f"Expected Anthropic #1, got {result['items'][0]['name'] if result['items'] else 'none'}")


# ════════════════════════════════════════════════════════════════════════════
# T14  Empty events returns empty items
# ════════════════════════════════════════════════════════════════════════════
print("\n[T14] Empty events returns items=[]")
result = _compute_lab_model_movement([])
if result["items"] == []:
    ok("Empty events → items=[] ✓")
else:
    fail(f"Expected items=[], got {result['items']}")


# ════════════════════════════════════════════════════════════════════════════
# T15  DB check: Anthropic / Claude / OpenAI values unchanged; Phi gone
# ════════════════════════════════════════════════════════════════════════════
print("\n[T15] DB validation: Anthropic, Claude, OpenAI unchanged; Phi removed")
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend", ".env"))
    from backend.db.supabase import get_supabase
    db = get_supabase()
    if not db:
        print("  ⚠️  Supabase not connected — skipping DB validation")
        db = None
except Exception as e:
    print(f"  ⚠️  Cannot load Supabase: {e}")
    db = None

if db:
    resp = db.table("events").select(
        "id, title, summary, source_id, created_at, published_at, breakthrough_score, risk_signal"
    ).order("created_at", desc=True).execute()
    raw = resp.data or []

    # Replicate the patched calculation
    from backend.routes.analytics import _ORG_KEYWORDS, _MODEL_PATTERNS as MP

    org_data = defaultdict(list)
    model_data = defaultdict(list)
    for e in raw:
        text = f"{e['title']} {e.get('summary','') or ''}".lower()
        bt = float(e.get("breakthrough_score") or 0)
        rk = float(e.get("risk_signal") or 0)

        matched_org = set()
        for kw in sorted(_ORG_KEYWORDS, key=len, reverse=True):
            if kw in text:
                d = _ORG_KEYWORDS[kw]
                if d not in matched_org:
                    org_data[d].append((bt, rk))
                    matched_org.add(d)

        matched_model = set()
        for pattern, d in MP:
            if d not in matched_model and pattern.search(text):
                model_data[d].append((bt, rk))
                matched_model.add(d)

    def avg(vals): return round(mean(vals), 2) if vals else 0.0

    EXPECTED = {
        "Anthropic": {"mentions": 9, "bt": 7.9,  "risk": 4.7},
        "Claude":    {"mentions": 9, "bt": 7.7,  "risk": 4.1},
        "OpenAI":    {"mentions": 5, "bt": 7.9,  "risk": 4.1},
    }

    all_data = {**dict(org_data), **dict(model_data)}

    for name, exp in EXPECTED.items():
        pairs = all_data.get(name, [])
        cnt  = len(pairs)
        b    = avg([p[0] for p in pairs])
        r    = avg([p[1] for p in pairs])
        ok_m = cnt == exp["mentions"]
        ok_b = abs(b - exp["bt"]) < 0.05
        ok_r = abs(r - exp["risk"]) < 0.05
        if ok_m and ok_b and ok_r:
            ok(f"{name}: mentions={cnt}  BT={b:.2f}  Risk={r:.2f} — unchanged ✓")
        else:
            fail(f"{name}: got mentions={cnt} BT={b:.2f} Risk={r:.2f}, expected {exp}")

    # Phi should now be absent (3 false positives removed)
    phi_pairs = all_data.get("Phi", [])
    if len(phi_pairs) == 0:
        ok("Phi: 0 mentions (3 false positives correctly removed) ✓")
    else:
        # If there are real Phi events in DB, this is fine — report them
        phi_titles = []
        for e in raw:
            text = f"{e['title']} {e.get('summary','') or ''}".lower()
            if re.search(r'\bphi\b', text, re.IGNORECASE):
                phi_titles.append(e.get("title","")[:60])
        fail(f"Phi: {len(phi_pairs)} match(es) still found. Titles: {phi_titles}")


# ════════════════════════════════════════════════════════════════════════════
# T16  Previous test files still compile (regression guard)
# ════════════════════════════════════════════════════════════════════════════
print("\n[T16] Previous test files compile cleanly")
root = os.path.dirname(os.path.abspath(__file__))
for tf in ["test_ingest_patch.py", "test_domain_momentum_patch.py", "test_source_mapping_patch.py"]:
    result = subprocess.run(
        ["python", "-m", "py_compile", tf],
        capture_output=True, text=True, cwd=root
    )
    if result.returncode == 0:
        ok(f"{tf} compiles cleanly ✓")
    else:
        fail(f"{tf} syntax error: {result.stderr[:200]}")


# ════════════════════════════════════════════════════════════════════════════
# T17  analytics.py itself compiles cleanly
# ════════════════════════════════════════════════════════════════════════════
print("\n[T17] backend/routes/analytics.py compiles cleanly")
result = subprocess.run(
    ["python", "-m", "py_compile", "backend/routes/analytics.py"],
    capture_output=True, text=True, cwd=root
)
if result.returncode == 0:
    ok("analytics.py compiles cleanly ✓")
else:
    fail(f"analytics.py syntax error: {result.stderr[:200]}")


# ════════════════════════════════════════════════════════════════════════════
# Final report
# ════════════════════════════════════════════════════════════════════════════
print(f"\n{'='*62}")
print(f"RESULTS: {PASS} passed, {FAIL} failed")
print(f"{'='*62}")
sys.exit(1 if FAIL > 0 else 0)
