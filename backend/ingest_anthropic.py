#!/usr/bin/env python
"""
AI News RSS → Gemini Scoring → Supabase Pipeline (Phase 2a MVP)

SAFETY & ISOLATION:
- Completely standalone script (no app integration)
- Fail-safe deduplication (skip if URL exists)
- No deletion/modification of existing events
- No changes to database schema
- Can fail without affecting dashboard
"""

import os
import json
import uuid
import logging
from datetime import datetime
from pathlib import Path

import feedparser
from google import genai
from dotenv import load_dotenv

from backend.db.supabase import get_supabase, check_event_exists_by_url

# ============================================================================
# LOGGING
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# ============================================================================
# CONFIG
# ============================================================================

env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
RSS_FEED_URL = "https://news.ycombinator.com/rss"
SOURCE_ID = "s3"  # The AI Digest (seed data source)
MAX_ARTICLES_PER_RUN = 3  # Testing phase: limit to 3 articles

VALID_DOMAINS = ["ai-model-behavior", "ai-software-engineering", "ai-cyber-risk", "ai-benchmarks", "ai-agents", "ai-safety-governance"]
VALID_EVIDENCE_LEVELS = ["Peer-Reviewed Research", "Technical Report", "News Report", "Company Announcement", "Official Release", "Benchmark", "Empirical Benchmark", "Rumor"]

# ============================================================================
# SETUP
# ============================================================================

def validate_environment():
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not in .env")
    logger.info("✅ Environment: GEMINI_API_KEY configured")

def setup_gemini_client():
    try:
        # Initialize google-genai Client with API key
        client = genai.Client(api_key=GEMINI_API_KEY)
        logger.info("✅ Gemini: Initialized (google-genai)")
        return client
    except Exception as e:
        logger.error(f"❌ Failed to initialize Gemini: {e}")
        raise

# ============================================================================
# RSS
# ============================================================================

def fetch_rss_entries():
    logger.info(f"\n📡 Fetching RSS feed: {RSS_FEED_URL}")
    try:
        feed = feedparser.parse(RSS_FEED_URL)
        if not feed.entries:
            logger.warning("   No entries found")
            return []
        entries = feed.entries[:MAX_ARTICLES_PER_RUN]
        logger.info(f"   ✅ Fetched {len(entries)} entries")
        return entries
    except Exception as e:
        logger.error(f"   ❌ Failed: {e}")
        return []

# ============================================================================
# GEMINI SCORING
# ============================================================================

def score_article_with_gemini(client, title: str, summary: str, url: str) -> dict | None:
    
    prompt = f"""You are an AI intelligence analyst. Analyze this article and return ONLY a JSON object (no markdown).

Title: {title}
Summary: {summary[:1000]}
URL: {url}

Return ONLY this JSON:
{{
  "breakthrough_score": <float 0-10>,
  "risk_signal": <float 0-10>,
  "evidence_level": "<one of: Peer-Reviewed Research, Technical Report, News Report, Company Announcement, Official Release, Benchmark, Empirical Benchmark, Rumor>",
  "impact_areas": <list of 2-4 strings>,
  "trend_momentum": <float -1.0 to 1.0>,
  "domain_slugs": <list of 1-2 from: ai-model-behavior, ai-software-engineering, ai-cyber-risk, ai-benchmarks, ai-agents, ai-safety-governance>
}}"""
    
    try:
        logger.info("   🤖 Calling Gemini...")
        # Use google-genai Client API
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        
        scores_json = json.loads(response.text)
        logger.info(f"   ✅ Scores: breakthrough={scores_json.get('breakthrough_score')}, risk={scores_json.get('risk_signal')}")
        return scores_json
        
    except json.JSONDecodeError as e:
        logger.warning(f"   ❌ Invalid JSON: {e}")
        return None
    except Exception as e:
        logger.warning(f"   ❌ Gemini error: {e}")
        return None

# ============================================================================
# VALIDATION
# ============================================================================

def validate_scores(scores: dict | None) -> bool:
    if not scores or not isinstance(scores, dict):
        logger.warning("   ❌ Not a dict")
        return False
    
    required_keys = ["breakthrough_score", "risk_signal", "evidence_level", "impact_areas", "trend_momentum", "domain_slugs"]
    missing = set(required_keys) - set(scores.keys())
    if missing:
        logger.warning(f"   ❌ Missing: {missing}")
        return False
    
    if scores["evidence_level"] not in VALID_EVIDENCE_LEVELS:
        logger.warning(f"   ❌ Invalid evidence_level")
        return False
    
    if not isinstance(scores["domain_slugs"], list) or len(scores["domain_slugs"]) not in [1, 2]:
        logger.warning(f"   ❌ Invalid domain_slugs")
        return False
    
    for domain in scores["domain_slugs"]:
        if domain not in VALID_DOMAINS:
            logger.warning(f"   ❌ Invalid domain")
            return False
    
    try:
        bs = float(scores["breakthrough_score"])
        rs = float(scores["risk_signal"])
        tm = float(scores["trend_momentum"])
        
        if not (0 <= bs <= 10) or not (0 <= rs <= 10) or not (-1.0 <= tm <= 1.0):
            logger.warning("   ❌ Scores out of range")
            return False
    except (ValueError, TypeError):
        logger.warning("   ❌ Numeric conversion failed")
        return False
    
    logger.info("   ✅ Validation passed")
    return True

# ============================================================================
# DATABASE
# ============================================================================

def insert_event_to_supabase(title: str, summary: str, url: str, published_at: str, scores: dict) -> bool:
    
    db = get_supabase()
    if not db:
        logger.warning("   ❌ Supabase not connected")
        return False
    
    if check_event_exists_by_url(url):
        logger.info("   ⏭️  Already in DB")
        return False
    
    event_id = str(uuid.uuid4())
    
    try:
        logger.info("   📝 Inserting event...")
        db.table("events").insert({
            "id": event_id,
            "title": title,
            "summary": summary,
            "url": url,
            "published_at": published_at,
            "source_id": SOURCE_ID,
            "breakthrough_score": float(scores["breakthrough_score"]),
            "risk_signal": float(scores["risk_signal"]),
            "evidence_level": scores["evidence_level"],
            "impact_areas": scores["impact_areas"],
            "trend_momentum": float(scores["trend_momentum"]),
        }).execute()
        logger.info(f"   ✅ Event inserted")
    except Exception as e:
        logger.warning(f"   ❌ Insert failed: {e}")
        return False
    
    try:
        logger.info(f"   🔗 Linking domains...")
        for domain_slug in scores["domain_slugs"]:
            domain_result = db.table("domains").select("id").eq("slug", domain_slug).execute()
            if not domain_result.data:
                logger.warning(f"      Domain not found: {domain_slug}")
                continue
            
            domain_id = domain_result.data[0]["id"]
            db.table("event_domains").insert({
                "event_id": event_id,
                "domain_id": domain_id
            }).execute()
            logger.info(f"      ✅ Linked: {domain_slug}")
    except Exception as e:
        logger.warning(f"   ⚠️  Domain linking failed: {e}")
        return True  # Event inserted, partial success
    
    return True

# ============================================================================
# MAIN
# ============================================================================

def main():
    print("\n" + "="*70)
    print("🚀 AI NEWS RSS → GEMINI SCORING → SUPABASE PIPELINE")
    print("Phase 2a MVP - Manual Trigger Only")
    print("="*70)
    
    try:
        validate_environment()
    except ValueError as e:
        logger.error(f"❌ {e}")
        return
    
    try:
        client = setup_gemini_client()
    except Exception as e:
        logger.error(f"❌ {e}")
        return
    
    entries = fetch_rss_entries()
    if not entries:
        logger.error("❌ No articles to process")
        return
    
    # Initialize counters
    fetched_count = len(entries)
    analyzed_count = 0
    inserted_count = 0
    duplicate_count = 0
    skipped_count = 0
    failed_count = 0
    
    for i, entry in enumerate(entries, 1):
        logger.info(f"\n[{i}/{fetched_count}] {entry.title[:70]}...")
        
        title = entry.title
        url = entry.link
        summary = entry.summary if hasattr(entry, 'summary') else ""
        published_at = entry.published if hasattr(entry, 'published') else datetime.now().isoformat()
        
        if len(summary) > 2000:
            summary = summary[:2000]
        
        # Check for duplicate BEFORE calling Gemini
        if check_event_exists_by_url(url):
            logger.info("   ⏭️  Duplicate (already in DB)")
            duplicate_count += 1
            continue
        
        # Score with Gemini (count as analyzed)
        scores = score_article_with_gemini(client, title, summary, url)
        analyzed_count += 1
        
        # Validate scores
        if not validate_scores(scores):
            failed_count += 1
            continue
        
        # Insert to database
        if insert_event_to_supabase(title, summary, url, published_at, scores):
            inserted_count += 1
        else:
            skipped_count += 1
    
    # Final Summary Report
    print(f"\n" + "="*70)
    print(f"✅ PIPELINE COMPLETE")
    print(f"   Fetched:     {fetched_count}")
    print(f"   Analyzed:    {analyzed_count}")
    print(f"   Inserted:    {inserted_count}")
    print(f"   Duplicates:  {duplicate_count}")
    print(f"   Skipped:     {skipped_count}")
    print(f"   Failed:      {failed_count}")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()
