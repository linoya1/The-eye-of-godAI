#!/usr/bin/env python
"""AI News RSS → Groq Scoring → Supabase Pipeline (Phase 2a MVP)

ENHANCED: Prioritized Anthropic/Claude Coverage with Lightweight RSS
- Anthropic Research/Engineering/News via community-maintained Olshansk RSS feeds
- Improved keyword prioritization for Constitutional AI, reasoning systems, agents
- All sources remain lightweight RSS-based (no JavaScript rendering, no heavy scraping)

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
import time
import re
from datetime import datetime
from pathlib import Path
import feedparser
from groq import Groq
from dotenv import load_dotenv
from backend.db.supabase import get_supabase, check_event_exists
import urllib.request
import urllib.error

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

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Prioritized AI-focused sources (lightweight RSS/feed parsing only)
# NOTE: Anthropic RSS sources use Olshansk/rss-feeds community feed generator
# These are maintained community-generated RSS feeds from Anthropic's non-RSS-native content
FEED_SOURCES = [
    # Anthropic-focused sources (community-maintained, lightweight RSS)
    {
        "name": "Anthropic Research",
        "url": "https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_anthropic_research.xml",
        "source_id": "s5",
        "type": "rss"
    },
    {
        "name": "Anthropic Engineering",
        "url": "https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_anthropic_engineering.xml",
        "source_id": "s5",
        "type": "rss"
    },
    {
        "name": "Anthropic News",
        "url": "https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_anthropic_news.xml",
        "source_id": "s5",
        "type": "rss"
    },

    # New high-quality AI sources (RSS preferred)
    {
        "name": "Hugging Face Blog",
        "url": "https://huggingface.co/blog/feed.xml",
        "source_id": "s7",
        "type": "rss"
    },
    {
        "name": "Google Research Blog",
        "url": "https://research.google/blog/",
        "source_id": "s8",
        "type": "html_parse"  # Try HTML parse if RSS unavailable
    },
    {
        "name": "Google Blog",
        "url": "https://blog.google/rss/",
        "source_id": "s9",
        "type": "rss"
    },
    {
        "name": "Made By Agents",
        "url": "https://www.madebyagents.com/rss",
        "source_id": "s10",
        "type": "rss"
    },

    # Fallback: OpenAI Blog
    {
        "name": "OpenAI Blog",
        "url": "https://openai.com/news/rss.xml",
        "source_id": "s4",
        "type": "rss"
    },
]

MAX_ARTICLES_PER_RUN = 1  # Production: 1 article per run (cost-efficient with Groq)
GROQ_MODEL = "llama-3.1-8b-instant"  # Groq's free tier instant model
GROQ_CALL_DELAY = 0.5  # Safety delay between API calls (seconds)

# AI Relevance Keywords - must contain at least one to proceed
# Prioritized for: Anthropic, Claude, agents, reasoning, safety, autonomous systems
AI_KEYWORDS = {
    # Anthropic & Claude focus
    "anthropic", "claude", "claude 3", "claude code", "codebase ai", "sonnet", "opus", "haiku",
    
    # Constitutional AI & safety
    "constitutional ai", "rlhf", "ai safety", "safety", "alignment", "governance",
    
    # AI agents & autonomous systems
    "ai agents", "agents", "autonomous", "reasoning", "agent systems", "agentic",
    "multi-agent", "subagent", "autonomous coding", "autonomous engineering",
    
    # Advanced capabilities
    "reasoning systems", "inference optimization", "inference", "inference speed",
    "model behavior", "prompt optimization", "reasoning benchmark", "benchmark",
    
    # General AI
    "ai", "artificial intelligence", "llm", "gpt", "gemini", "openai",
    "reasoning", "benchmark", "alignment", "inference",
    "model", "deep learning", "machine learning", "cybersecurity",
    "robotics", "neural network", "transformer", "prompt injection", "language model",
    "vision", "multimodal", "embeddings", "fine-tuning", "training", "llama", "mistral",
    "groq", "xai", "grok", "reinforcement learning"
}

# Additional user-requested keywords (ensure presence)
AI_KEYWORDS.update({
    "agent", "agents", "benchmark", "eval", "evaluation", "alignment", "security",
    "infrastructure", "framework", "open-source", "coding", "reasoning", "inference",
    "autonomous", "llm", "ai model"
})

VALID_DOMAINS = ["ai-model-behavior", "ai-software-engineering", "ai-cyber-risk", "ai-benchmarks", "ai-agents", "ai-safety-governance"]
VALID_EVIDENCE_LEVELS = ["Peer-Reviewed Research", "Technical Report", "News Report", "Company Announcement", "Official Release", "Benchmark", "Empirical Benchmark", "Rumor"]

# ============================================================================
# SETUP
# ============================================================================

def validate_environment():
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY not in .env")
    logger.info("✅ Environment: GROQ_API_KEY configured")

def setup_groq_client():
    try:
        # Initialize Groq Client with API key
        client = Groq(api_key=GROQ_API_KEY)
        logger.info(f"✅ Groq: Initialized ({GROQ_MODEL})")
        return client
    except Exception as e:
        logger.error(f"❌ Failed to initialize Groq: {e}")
        raise

# ============================================================================
# RSS PARSING
# ============================================================================

def fetch_rss_entries():
    """Fetch RSS entries from all configured sources (lightweight).

    Behavior:
    - Try `feedparser.parse` for each source.
    - If `type` == "html_parse", attempt a lightweight HTML anchor extractor.
    - Aggregate entries from all sources up to `MAX_ARTICLES_PER_RUN` total.
    """

    aggregated = []
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    for source in FEED_SOURCES:
        if len(aggregated) >= MAX_ARTICLES_PER_RUN:
            break

        logger.info(f"\n📡 Trying {source['name']}: {source['url'][:60]}...")
        try:
            feed = feedparser.parse(source['url'])
            if feed.entries:
                for entry in feed.entries:
                    entry._source_id = source["source_id"]
                    entry._source_name = source["name"]
                    aggregated.append(entry)
                    if len(aggregated) >= MAX_ARTICLES_PER_RUN:
                        break
                logger.info(f"   ✅ Fetched {len(feed.entries)} from {source['name']}")
                continue

            # If no RSS entries and HTML parsing is allowed, try lightweight HTML parse
            if source.get("type") == "html_parse":
                try:
                    req = urllib.request.Request(source['url'])
                    for k, v in headers.items():
                        req.add_header(k, v)
                    with urllib.request.urlopen(req, timeout=8) as resp:
                        html = resp.read().decode('utf-8', errors='ignore')

                    # Simple anchor extractor: <a href="...">Title</a>
                    pattern = r'<a[^>]+href=[\'\"](?P<href>[^\'\"]+)[\'\"][^>]*>(?P<text>[^<]{10,200})</a>'
                    matches = re.finditer(pattern, html, flags=re.IGNORECASE)
                    for m in matches:
                        href = m.group('href')
                        text = m.group('text').strip()
                        # Skip short/generic
                        if len(text) < 20:
                            continue
                        url = href
                        if url.startswith('/'):
                            # Make absolute
                            base = source['url'].rstrip('/')
                            url = base + url
                        entry = type('Entry', (), {
                            'title': text,
                            'link': url,
                            'summary': text,
                            'published': None
                        })()
                        entry._source_id = source["source_id"]
                        entry._source_name = source["name"]
                        aggregated.append(entry)
                        if len(aggregated) >= MAX_ARTICLES_PER_RUN:
                            break

                    if aggregated:
                        logger.info(f"   ✅ Extracted {len(aggregated)} articles from {source['name']} (html_parse)")
                        continue
                except Exception as e:
                    logger.warning(f"   ⏭️  HTML parse failed for {source['name']}: {e}")

            logger.warning(f"   ⏭️  No entries in {source['name']}")

        except Exception as e:
            logger.warning(f"   ⏭️  {source['name']} failed: {e}")

    if not aggregated:
        logger.error("❌ All sources exhausted, no articles found")
    return aggregated[:MAX_ARTICLES_PER_RUN]

# ============================================================================
# FILTERING & CLEANING
# ============================================================================

def clean_html(text: str) -> str:
    """Remove HTML tags from text."""
    if not text:
        return ""
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Decode HTML entities
    text = text.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
    text = text.replace('&quot;', '"').replace('&#39;', "'")
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def clean_title(title: str) -> str:
    """Strip common malformed date/title concatenations from headlines."""
    if not title:
        return ""
    # Remove trailing month-day-year patterns like ' - May 19, 2026' or '| May 19, 2026'
    months = r'Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|January|February|March|April|June|July|August|September|October|November|December'
    title = re.sub(rf'\s*[\-|\|]\s*(?:{months})\s+\d{{1,2}},\s*\d{{4}}$', '', title)
    # Remove ISO-like dates at end 'YYYY-MM-DD'
    title = re.sub(r'\s*\d{4}-\d{2}-\d{2}$', '', title)
    return title.strip()

def extract_article_content(entry) -> str:
    """Extract article content from RSS entry (content > summary > empty)."""
    # Try full content first
    if hasattr(entry, 'content') and entry.content:
        # entry.content is typically a list of dicts with 'value' key
        if isinstance(entry.content, list) and len(entry.content) > 0:
            content_text = entry.content[0].get('value', '')
            if content_text:
                cleaned = clean_html(content_text)
                return cleaned[:2000]  # Limit to first 2000 chars
    
    # Fall back to summary
    if hasattr(entry, 'summary') and entry.summary:
        cleaned = clean_html(entry.summary)
        return cleaned[:1000]
    
    # No content available
    return ""

def generate_summary_with_groq(client, title: str, content: str) -> str:
    """Generate a concise 2-3 sentence summary from title + article content."""
    
    if not content or len(content) < 20:
        # Fallback: generate summary from title metadata if no content
        return f"Latest update on {title.split(':')[0].lower()}. Check the source for complete details."
    
    prompt = f"""Generate a concise 2-3 sentence summary of this article. 
Focus on:
- What happened or what was discovered
- Why it matters for AI/tech industry
- Key implications or findings

DO NOT just repeat the headline. Write like a brief intelligence update.
Keep it factual, readable, and under 150 words.

TITLE: {title}

CONTENT: {content}

Return ONLY the summary text (no quotes, no markdown, just plain text)."""
    
    try:
        logger.info(f"   ✍️  Generating summary with Groq...")
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,  # Slightly higher for natural language variation
            max_tokens=300
        )
        
        summary = response.choices[0].message.content.strip()
        logger.info(f"   ✅ Summary generated ({len(summary)} chars)")
        return summary
        
    except Exception as e:
        logger.warning(f"   ⚠️  Summary generation failed: {e}")
        # Fallback: return first 150 chars of content
        return content[:150] + "..."

def has_ai_keywords(title: str, summary: str) -> bool:
    """Check if content contains AI-related keywords."""
    if not title or not summary:
        return False
    text = (title + " " + summary).lower()
    for keyword in AI_KEYWORDS:
        if keyword in text:
            logger.info(f"   ✅ AI keyword found: '{keyword}'")
            return True
    logger.info(f"   ⏭️  No AI keywords detected")
    return False

def check_relevance_gate(client, title: str, summary: str, url: str) -> bool:
    """Ask LLM if this is a meaningful AI intelligence event (must be >= 7/10)."""
    
    prompt = f"""Is this article about a meaningful AI intelligence event, breakthrough, or risk signal?
Rate relevance to AI systems, capabilities, safety, or industry: 0-10 scale.

Title: {title}
Summary: {summary[:500]}

Return ONLY this JSON:
{{"relevance_score": <float 0-10>, "reason": "<brief reason>"}}"""
    
    try:
        logger.info(f"   🔍 Checking AI relevance gate...")
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=200
        )
        
        response_text = response.choices[0].message.content
        relevance_data = json.loads(response_text)
        relevance_score = float(relevance_data.get("relevance_score", 0))
        reason = relevance_data.get("reason", "")
        
        if relevance_score >= 7.0:
            logger.info(f"   ✅ Relevance gate passed: {relevance_score}/10 - {reason}")
            return True
        else:
            logger.info(f"   ⏭️  Relevance gate rejected: {relevance_score}/10 - {reason}")
            return False
        
    except Exception as e:
        logger.warning(f"   ⚠️  Relevance check failed, assuming relevant: {e}")
        return True  # Fail-forward: if check fails, allow article

# ============================================================================
# GROQ SCORING
# ============================================================================

def score_article_with_groq(client, title: str, summary: str, url: str) -> dict | None:
    
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
        logger.info(f"   🤖 Calling Groq ({GROQ_MODEL})...")
        # Use Groq Client API with messages interface
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,  # Lower temperature for more deterministic JSON output
            max_tokens=500
        )
        
        response_text = response.choices[0].message.content
        scores_json = json.loads(response_text)
        logger.info(f"   ✅ Scores: breakthrough={scores_json.get('breakthrough_score')}, risk={scores_json.get('risk_signal')}")
        return scores_json
        
    except json.JSONDecodeError as e:
        logger.warning(f"   ❌ Invalid JSON from Groq: {e}")
        return None
    except Exception as e:
        error_str = str(e)
        if "429" in error_str or "rate" in error_str.lower():
            logger.error(f"   ❌ GROQ RATE LIMIT (429): Quota exceeded or rate limit hit")
            logger.error(f"      API returned: {error_str[:100]}...")
            return None
        logger.warning(f"   ❌ Groq error: {error_str[:100]}")
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

def insert_event_to_supabase(title: str, summary: str, url: str, published_at: str, scores: dict, source_id: str = None) -> bool:
    
    if source_id is None:
        source_id = "s4"  # Default fallback to OpenAI Blog
    
    db = get_supabase()
    if not db:
        logger.warning("   ❌ Supabase not connected")
        return False
    
    if check_event_exists(url=url, title=title, published_at=published_at):
        logger.info("   ⏭️  Already in DB (url/title/published_at match)")
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
            "source_id": source_id,
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
    print("🚀 AI NEWS RSS → GROQ SCORING → SUPABASE PIPELINE")
    print("Phase 2a MVP - Manual Trigger Only")
    print("="*70)
    
    try:
        validate_environment()
    except ValueError as e:
        logger.error(f"❌ {e}")
        return
    
    try:
        client = setup_groq_client()
    except Exception as e:
        logger.error(f"❌ {e}")
        return
    
    entries = fetch_rss_entries()
    if not entries:
        logger.error("❌ No articles to process")
        return
    
    # Initialize counters
    fetched_count = len(entries)
    filtered_count = 0  # Passed AI keyword filter
    analyzed_count = 0  # Sent to LLM
    inserted_count = 0
    duplicate_count = 0
    skipped_count = 0
    failed_count = 0
    source_used = None  # Track which source provided the article
    
    for i, entry in enumerate(entries, 1):
        logger.info(f"\n[{i}/{fetched_count}] {entry.title[:70]}...")
        
        # Get source metadata
        source_id = getattr(entry, '_source_id', 's4')  # Default to OpenAI Blog
        source_name = getattr(entry, '_source_name', 'OpenAI Blog')
        if source_used is None:
            source_used = source_name
        
        title = clean_title(entry.title)
        url = entry.link
        published_at = entry.published if hasattr(entry, 'published') else datetime.now().isoformat()
        
        # Check for duplicate EARLY (before expensive Groq calls)
        if check_event_exists(url=url, title=title, published_at=published_at):
            logger.info("   ⏭️  Duplicate (already in DB)")
            duplicate_count += 1
            continue
        
        # Extract article content from RSS entry
        logger.info(f"   📄 Extracting article content...")
        article_content = extract_article_content(entry)
        
        # Generate summary from title + content using Groq (BEFORE keyword filtering)
        logger.info(f"   ✍️  Generating summary...")
        generated_summary = generate_summary_with_groq(client, title, article_content)
        time.sleep(GROQ_CALL_DELAY)
        
        # Use generated summary for all downstream checks
        summary = generated_summary
        
        # AI Relevance Filter: Check for AI keywords (keyword-based pre-filter)
        if not has_ai_keywords(title, summary):
            logger.info("   ⏭️  Skipped: No AI keywords")
            skipped_count += 1
            continue
        
        filtered_count += 1
        
        # Relevance Gate: Ask LLM if this is a meaningful AI event (must be >= 7/10)
        if not check_relevance_gate(client, title, summary, url):
            logger.info("   ⏭️  Failed relevance gate")
            skipped_count += 1
            time.sleep(GROQ_CALL_DELAY)
            continue
        
        # Score with Groq (count as analyzed after passing gates)
        scores = score_article_with_groq(client, title, summary, url)
        analyzed_count += 1
        
        # Safety delay between Groq calls to respect rate limits
        time.sleep(GROQ_CALL_DELAY)
        
        # Validate scores
        if not validate_scores(scores):
            failed_count += 1
            continue
        
        # Sanitize summary and ensure it is not identical to the title
        sanitized_summary = clean_html(summary)
        if sanitized_summary.strip().lower() == title.strip().lower() or title.strip().lower() in sanitized_summary.strip().lower()[:120]:
            # Fallback: use leading content snippet (avoid repeating the headline)
            if article_content:
                fallback = clean_html(article_content)
                sanitized_summary = (fallback[:140].rsplit('.', 1)[0] + '.') if '.' in fallback[:140] else fallback[:140] + '...'
            else:
                sanitized_summary = f"Update: {title.split('-')[0].strip()} — see source for details."

        # Insert to database with source metadata
        if insert_event_to_supabase(title, sanitized_summary, url, published_at, scores, source_id):
            inserted_count += 1
        else:
            skipped_count += 1
    
    # Final Summary Report
    print(f"\n" + "="*70)
    print(f"✅ PIPELINE COMPLETE")
    print(f"   Source:      {source_used or 'None'}")
    print(f"   Fetched:     {fetched_count}")
    print(f"   Filtered:    {filtered_count} (passed AI keyword filter)")
    print(f"   Analyzed:    {analyzed_count}")
    print(f"   Inserted:    {inserted_count}")
    print(f"   Duplicates:  {duplicate_count}")
    print(f"   Skipped:     {skipped_count}")
    print(f"   Failed:      {failed_count}")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()
