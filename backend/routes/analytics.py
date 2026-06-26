from __future__ import annotations

import math
import re
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from statistics import mean

from fastapi import APIRouter, HTTPException, Query

from backend.db.supabase import get_supabase
from backend.models.schemas import (
    AnalyticsDatePoint,
    AnalyticsDomainMomentum,
    AnalyticsEcosystem,
    AnalyticsInsight,
    AnalyticsOverview,
    AnalyticsDashboardResponse,
    AnalyticsScatterPoint,
    AnalyticsTrends,
    DomainMomentumItem,
    EcosystemEntityItem,
    EvidenceDistributionItem,
    EmergingTopicItem,
)
from backend.routes.events import map_db_event_to_pydantic

router = APIRouter(prefix="/analytics", tags=["Analytics"])

WINDOW_DAYS = 28
MOMENTUM_WINDOW_DAYS = 7
RISING_DOMAIN_WINDOW_DAYS = 30   # rolling window for Fastest-Rising AI Domain metric
RISING_DOMAIN_OLD_ARTICLE_DAYS = 90  # exclude events whose published_at is older than this

MODEL_TOKEN_PATTERNS: dict[str, re.Pattern[str]] = {
    "GPT": re.compile(r"\bgpt(?:-?4o|-?4|-?3\.5)?\b", re.IGNORECASE),
    "Claude": re.compile(r"\bclaude(?:-?[23])?\b", re.IGNORECASE),
    "Llama": re.compile(r"\bllama(?:-?2)?\b", re.IGNORECASE),
    "Mistral": re.compile(r"\bmistral\b", re.IGNORECASE),
    "Gemini": re.compile(r"\bgemini\b", re.IGNORECASE),
    "PaLM": re.compile(r"\bpalm\b|\bbard\b", re.IGNORECASE),
    "Mixtral": re.compile(r"\bmixtral\b", re.IGNORECASE),
    "OPT": re.compile(r"\bopt\b", re.IGNORECASE),
}


def _parse_iso_date(raw: str | None) -> datetime | None:
    if not raw:
        return None

    value = raw.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None

    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _event_date(event) -> datetime | None:
    return _parse_iso_date(event.published_at)


def _window_bounds(window_days: int) -> tuple[datetime, datetime]:
    bounded_days = max(1, window_days)
    today = datetime.now(timezone.utc).date()
    start_day = today - timedelta(days=bounded_days - 1)
    start = datetime.combine(start_day, datetime.min.time(), tzinfo=timezone.utc)
    end = datetime.combine(today, datetime.max.time(), tzinfo=timezone.utc)
    return start, end


def _event_in_window(event, window_start: datetime, window_end: datetime) -> bool:
    event_dt = _event_date(event)
    return bool(event_dt and window_start <= event_dt <= window_end)


def _score_breakthrough(event) -> float:
    return float(event.scores.breakthrough_score)


def _score_risk(event) -> float:
    return float(event.scores.risk_signal)


def _score_momentum(event) -> float:
    return float(event.scores.trend_momentum)


def _domain_map(db) -> dict[str, str]:
    response = db.table("domains").select("slug,name").execute()
    return {row["slug"]: row.get("name") or row["slug"] for row in response.data or []}


def _fetch_events(db, domain: str | None = None, window_days: int = WINDOW_DAYS):
    query = db.table("events").select("*, sources(*), event_domains(domains(slug,name))").order("published_at", desc=True)
    response = query.execute()
    window_start, window_end = _window_bounds(window_days)
    events = []
    for row in response.data or []:
        mapped = map_db_event_to_pydantic(row)
        if domain and domain not in mapped.domains:
            continue
        if not _event_in_window(mapped, window_start, window_end):
            continue
        events.append(mapped)
    return events


def _primary_domain_label(event, domain_names: dict[str, str]) -> str:
    if event.domains:
        slug = event.domains[0]
        return domain_names.get(slug, slug)
    return "Unknown"


def _all_domain_labels(event, domain_names: dict[str, str]) -> list[str]:
    labels = [domain_names.get(slug, slug) for slug in event.domains]
    return labels or ["Unknown"]


def _model_family(text: str) -> str:
    for family, pattern in MODEL_TOKEN_PATTERNS.items():
        if pattern.search(text):
            return family
    return "Unspecified"


def _event_signal_score(event) -> float:
    breakthrough = _score_breakthrough(event)
    risk = _score_risk(event)
    momentum = abs(_score_momentum(event))
    impact_boost = min(1.0, 0.15 * len(event.scores.impact_areas))
    return breakthrough * 0.44 + risk * 0.34 + math.log1p(momentum) * 2.2 + impact_boost


def _event_quadrant(event) -> str:
    breakthrough = _score_breakthrough(event)
    risk = _score_risk(event)
    if breakthrough >= 7 and risk >= 7:
        return "high-risk / high-breakthrough"
    if breakthrough >= 7 and risk < 5:
        return "capability gain"
    if breakthrough < 5 and risk >= 7:
        return "risk escalation"
    return "mixed signal"


def _evidence_distribution(events) -> list[EvidenceDistributionItem]:
    counts = Counter((event.scores.evidence_level or "Unspecified") for event in events)
    total = max(1, sum(counts.values()))
    return [
        EvidenceDistributionItem(label=label, count=count, share=round(count / total, 3))
        for label, count in counts.most_common()
    ]


def _timeline(events, window_days: int = WINDOW_DAYS) -> list[AnalyticsDatePoint]:
    if not events:
        return []

    grouped: dict[str, list] = defaultdict(list)
    for event in events:
        event_dt = _event_date(event)
        if not event_dt:
            continue
        grouped[event_dt.date().isoformat()].append(event)

    points: list[AnalyticsDatePoint] = []
    start_day = datetime.now(timezone.utc).date() - timedelta(days=max(1, window_days) - 1)
    for offset in range(max(1, window_days)):
        current_day = (start_day + timedelta(days=offset)).isoformat()
        day_events = grouped.get(current_day, [])
        breakthrough_values = [_score_breakthrough(event) for event in day_events]
        risk_values = [_score_risk(event) for event in day_events]
        momentum_values = [_score_momentum(event) for event in day_events]
        points.append(
            AnalyticsDatePoint(
                date=current_day,
                event_count=len(day_events),
                avg_breakthrough=round(mean(breakthrough_values) if breakthrough_values else 0.0, 2),
                avg_risk=round(mean(risk_values) if risk_values else 0.0, 2),
                avg_momentum=round(mean(momentum_values) if momentum_values else 0.0, 2),
            )
        )
    return points


def _risk_breakthrough_points(events, domain_names: dict[str, str]) -> list[AnalyticsScatterPoint]:
    ranked = sorted(events, key=_event_signal_score, reverse=True)[:15]
    points: list[AnalyticsScatterPoint] = []
    for event in ranked:
        points.append(
            AnalyticsScatterPoint(
                id=event.id,
                title=event.title,
                domain=_primary_domain_label(event, domain_names),
                source=event.source.name,
                breakthrough=round(_score_breakthrough(event), 2),
                risk=round(_score_risk(event), 2),
                momentum=round(_score_momentum(event), 2),
                evidence_level=event.scores.evidence_level,
                url=event.url,
            )
        )
    return points


def _emerging_topics(events, domain_names: dict[str, str]) -> list[EmergingTopicItem]:
    ranked = sorted(events, key=_event_signal_score, reverse=True)[:6]
    topics: list[EmergingTopicItem] = []
    for event in ranked:
        topics.append(
            EmergingTopicItem(
                id=event.id,
                title=event.title,
                domain=_primary_domain_label(event, domain_names),
                source=event.source.name,
                breakthrough=round(_score_breakthrough(event), 2),
                risk=round(_score_risk(event), 2),
                momentum=round(_score_momentum(event), 2),
                evidence_level=event.scores.evidence_level,
                url=event.url,
                signal=_event_quadrant(event),
            )
        )
    return topics


def _windowed_domain_momentum(events, domain_names: dict[str, str]) -> list[DomainMomentumItem]:
    today = datetime.now(timezone.utc).date()
    recent_start = today - timedelta(days=MOMENTUM_WINDOW_DAYS)
    previous_start = today - timedelta(days=MOMENTUM_WINDOW_DAYS * 2)

    grouped: dict[str, list] = defaultdict(list)
    for event in events:
        event_dt = _event_date(event)
        if not event_dt:
            continue
        event_day = event_dt.date()
        for slug in event.domains or ["unknown"]:
            grouped[slug].append((event_day, event))

    rows: list[DomainMomentumItem] = []
    for slug, samples in grouped.items():
        recent_events = [event for day, event in samples if recent_start <= day <= today]
        previous_events = [event for day, event in samples if previous_start <= day < recent_start]

        recent_avg = mean([_score_momentum(event) for event in recent_events]) if recent_events else 0.0
        previous_avg = mean([_score_momentum(event) for event in previous_events]) if previous_events else 0.0
        delta = recent_avg - previous_avg
        direction = "up" if delta > 0.1 else "down" if delta < -0.1 else "flat"
        top_event_ids = [
            event.id
            for event in sorted(recent_events, key=_event_signal_score, reverse=True)[:3]
        ]
        domain_label = domain_names.get(slug, slug)
        if direction == "up":
            summary = f"{domain_label} momentum is accelerating relative to the previous week."
        elif direction == "down":
            summary = f"{domain_label} momentum is cooling after a stronger prior window."
        else:
            summary = f"{domain_label} momentum is broadly stable across the last two windows."

        rows.append(
            DomainMomentumItem(
                slug=slug,
                name=domain_label,
                recent_count=len(recent_events),
                recent_avg_momentum=round(recent_avg, 2),
                previous_avg_momentum=round(previous_avg, 2),
                delta=round(delta, 2),
                direction=direction,
                top_event_ids=top_event_ids,
                summary=summary,
            )
        )

    return sorted(rows, key=lambda item: (abs(item.delta), item.recent_count, item.name.lower()), reverse=True)


def _ecosystem_entities(events, key_fn) -> list[EcosystemEntityItem]:
    buckets: dict[str, list] = defaultdict(list)
    for event in events:
        buckets[key_fn(event)].append(event)

    rows: list[EcosystemEntityItem] = []
    for name, items in buckets.items():
        breakthrough_values = [_score_breakthrough(event) for event in items]
        risk_values = [_score_risk(event) for event in items]
        momentum_values = [_score_momentum(event) for event in items]
        rows.append(
            EcosystemEntityItem(
                name=name,
                count=len(items),
                avg_breakthrough=round(mean(breakthrough_values) if breakthrough_values else 0.0, 2),
                avg_risk=round(mean(risk_values) if risk_values else 0.0, 2),
                avg_momentum=round(mean(momentum_values) if momentum_values else 0.0, 2),
                high_risk_count=sum(1 for value in risk_values if value >= 7),
                high_breakthrough_count=sum(1 for value in breakthrough_values if value >= 7),
                top_event_ids=[event.id for event in sorted(items, key=_event_signal_score, reverse=True)[:3]],
            )
        )

    return sorted(rows, key=lambda item: (item.count, item.avg_breakthrough), reverse=True)


def _insight_cards(events, domain_names: dict[str, str]) -> list[AnalyticsInsight]:
    cards: list[AnalyticsInsight] = []
    if not events:
        return [
            AnalyticsInsight(
                title="Waiting for new signal",
                summary="No events fell inside the current analytics window yet, so the dashboard is showing a neutral baseline.",
                confidence="low",
                category="coverage",
            )
        ]

    momentum_rows = _windowed_domain_momentum(events, domain_names)
    top_up = next((item for item in momentum_rows if item.direction == "up"), None)
    top_down = next((item for item in momentum_rows if item.direction == "down"), None)

    if top_up:
        cards.append(
            AnalyticsInsight(
                title=f"Acceleration in {top_up.name}",
                summary=f"Momentum is rising in {top_up.name} by {abs(top_up.delta):.2f} points over the comparison window, with recent events clustering around the strongest signals.",
                confidence="high" if top_up.recent_count >= 2 else "medium",
                category="trend",
            )
        )

    if top_down:
        cards.append(
            AnalyticsInsight(
                title=f"Cooling in {top_down.name}",
                summary=f"{top_down.name} is losing momentum relative to the prior window, which suggests the current cycle may be past its peak.",
                confidence="medium" if top_down.recent_count >= 2 else "low",
                category="trend",
            )
        )

    risky_breakthrough = [event for event in events if _score_breakthrough(event) >= 7 and _score_risk(event) >= 7]
    if risky_breakthrough:
        top = sorted(risky_breakthrough, key=_event_signal_score, reverse=True)[0]
        cards.append(
            AnalyticsInsight(
                title="High-risk / high-breakthrough surface",
                summary=f"{top.title} is an example of capability gains arriving alongside elevated risk, a pattern worth monitoring for dual-use spillover.",
                confidence="high",
                category="risk-vs-breakthrough",
            )
        )

    evidence_counts = Counter((event.scores.evidence_level or "Unspecified") for event in events)
    if evidence_counts:
        dominant = evidence_counts.most_common(1)[0]
        cards.append(
            AnalyticsInsight(
                title="Evidence quality concentration",
                summary=f"{dominant[0]} dominates the current sample, so the stream is leaning toward a narrow band of evidence quality rather than a balanced mix.",
                confidence="medium",
                category="evidence",
            )
        )

    source_rows = _ecosystem_entities(events, lambda event: event.source.name)
    if source_rows:
        top_source = source_rows[0]
        cards.append(
            AnalyticsInsight(
                title=f"{top_source.name} is shaping the ecosystem",
                summary=f"{top_source.name} has the densest event footprint and the strongest combined signal profile in the current sample.",
                confidence="medium" if top_source.count >= 2 else "low",
                category="ecosystem",
            )
        )

    return cards[:5]


def _build_dashboard(domain: str | None = None, window_days: int = WINDOW_DAYS):
    db = _ensure_db()
    domain_names = _domain_map(db)
    events = _fetch_events(db, domain, window_days)

    overview = AnalyticsOverview(
        window_days=window_days,
        total_events=len(events),
        total_domains=len(domain_names),
        evidence_distribution=_evidence_distribution(events),
        emerging_topics=_emerging_topics(events, domain_names),
        notable_shifts=[item.summary for item in _windowed_domain_momentum(events, domain_names)[:3]],
    )

    trends = AnalyticsTrends(
        window_days=window_days,
        timeline=_timeline(events, window_days),
        risk_breakthrough_points=_risk_breakthrough_points(events, domain_names),
    )

    domain_momentum = AnalyticsDomainMomentum(
        window_days=MOMENTUM_WINDOW_DAYS,
        domains=_windowed_domain_momentum(events, domain_names),
    )

    ecosystem = AnalyticsEcosystem(
        window_days=window_days,
        organizations=_ecosystem_entities(events, lambda event: event.source.name)[:8],
        model_families=_ecosystem_entities(
            events,
            lambda event: _model_family(f"{event.title} {event.summary} {event.source.name}"),
        )[:8],
    )

    return AnalyticsDashboardResponse(
        overview=overview,
        trends=trends,
        domain_momentum=domain_momentum,
        ecosystem=ecosystem,
        insights=_insight_cards(events, domain_names),
    )


def _ensure_db():
    db = get_supabase()
    if not db:
        raise HTTPException(status_code=500, detail="Database connection not configured")
    return db


@router.get("/overview", response_model=AnalyticsOverview)
def get_overview(
    domain: str | None = Query(default=None, description="Optional domain slug filter"),
    window_days: int = Query(default=WINDOW_DAYS, ge=7, le=90, description="Analytics window in days"),
):
    return _build_dashboard(domain, window_days).overview


@router.get("/trends", response_model=AnalyticsTrends)
def get_trends(
    domain: str | None = Query(default=None, description="Optional domain slug filter"),
    window_days: int = Query(default=WINDOW_DAYS, ge=7, le=90, description="Analytics window in days"),
):
    return _build_dashboard(domain, window_days).trends


@router.get("/domain-momentum", response_model=AnalyticsDomainMomentum)
def get_domain_momentum(
    domain: str | None = Query(default=None, description="Optional domain slug filter"),
    window_days: int = Query(default=WINDOW_DAYS, ge=7, le=90, description="Analytics window in days"),
):
    return _build_dashboard(domain, window_days).domain_momentum


@router.get("/ecosystem", response_model=AnalyticsEcosystem)
def get_ecosystem(
    domain: str | None = Query(default=None, description="Optional domain slug filter"),
    window_days: int = Query(default=WINDOW_DAYS, ge=7, le=90, description="Analytics window in days"),
):
    return _build_dashboard(domain, window_days).ecosystem


@router.get("/insights", response_model=list[AnalyticsInsight])
def get_insights(
    domain: str | None = Query(default=None, description="Optional domain slug filter"),
    window_days: int = Query(default=WINDOW_DAYS, ge=7, le=90, description="Analytics window in days"),
):
    return _build_dashboard(domain, window_days).insights


@router.get("/dashboard", response_model=AnalyticsDashboardResponse)
def get_dashboard(
    domain: str | None = Query(default=None, description="Optional domain slug filter"),
    window_days: int = Query(default=WINDOW_DAYS, ge=7, le=90, description="Analytics window in days"),
):
    return _build_dashboard(domain, window_days)


# ---------------------------------------------------------------------------
# Intelligence Summary — 3 clean backend-computed analytics
# ---------------------------------------------------------------------------

# Organisations / labs to look for (keyword → display name)
_ORG_KEYWORDS: dict[str, str] = {
    "openai": "OpenAI",
    "anthropic": "Anthropic",
    "google deepmind": "Google DeepMind",
    "deepmind": "Google DeepMind",
    "google": "Google",
    "meta ai": "Meta AI",
    "meta": "Meta AI",
    "microsoft": "Microsoft",
    "mistral": "Mistral AI",
    "nvidia": "NVIDIA",
    "amazon": "Amazon",
    "apple": "Apple",
    "hugging face": "Hugging Face",
    "stability ai": "Stability AI",
    "xai": "xAI",
    "cohere": "Cohere",
}

# Model families — keyword → display name (single source of truth)
_MODEL_KEYWORDS: dict[str, str] = {
    "gpt-4o": "GPT-4o",
    "gpt-4": "GPT-4",
    "gpt-3.5": "GPT-3.5",
    "claude": "Claude",
    "gemini": "Gemini",
    "llama": "Llama",
    "mistral": "Mistral",
    "grok": "Grok",
    "mixtral": "Mixtral",
    "phi": "Phi",
    "sora": "Sora",
    "dall-e": "DALL-E",
}

# Pre-compiled, word-boundary-anchored patterns derived from _MODEL_KEYWORDS.
# Sorted longest-keyword-first so that a specific alias (e.g. "gpt-4o") is
# evaluated before a shorter one it contains (e.g. "gpt-4").  Word boundaries
# (\b) prevent substring false-positives such as:
#   "phi" matching "philosophy" or "phishing"
#   "gpt-4" matching text that only contains "gpt-4o"
# re.escape handles hyphens and dots in keywords (gpt-4o, gpt-3.5, dall-e).
_MODEL_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\b" + re.escape(kw) + r"\b", re.IGNORECASE), display)
    for kw, display in sorted(_MODEL_KEYWORDS.items(), key=lambda kv: -len(kv[0]))
]


def _fetch_all_events(db):
    """Fetch all events without time-window filter (for sparse datasets)."""
    response = (
        db.table("events")
        .select("*, sources(*), event_domains(domains(slug,name))")
        .order("published_at", desc=True)
        .execute()
    )
    return [map_db_event_to_pydantic(row) for row in response.data or []]


def _compute_risk_breakthrough(events: list) -> dict:
    """
    Weekly averages of breakthrough_score and risk_signal over the last 8 weeks.
    Returns chart_points + an intelligence-style summary sentence.
    """
    if not events:
        return {
            "title": "Risk vs Breakthrough Trend",
            "summary": "No events found yet — ingest some articles to see the trend.",
            "chart_points": [],
        }

    # Bucket by ISO week
    weekly: dict[str, list] = defaultdict(list)
    for event in events:
        dt = _event_date(event)
        if not dt:
            continue
        week_key = dt.strftime("%Y-W%W")
        weekly[week_key].append(event)

    # Last 8 weeks (inclusive)
    today = datetime.now(timezone.utc).date()
    week_keys = sorted(
        {
            (today - timedelta(weeks=i)).strftime("%Y-W%W")
            for i in range(7, -1, -1)
        }
    )

    chart_points = []
    for wk in week_keys:
        bucket = weekly.get(wk, [])
        bt_vals = [_score_breakthrough(e) for e in bucket]
        rk_vals = [_score_risk(e) for e in bucket]
        chart_points.append(
            {
                "week": wk,
                "event_count": len(bucket),
                "avg_breakthrough": round(mean(bt_vals) if bt_vals else 0.0, 2),
                "avg_risk": round(mean(rk_vals) if rk_vals else 0.0, 2),
            }
        )

    # Generate natural-language summary
    recent = [p for p in chart_points if p["event_count"] > 0]
    if len(recent) >= 2:
        last = recent[-1]
        prev = recent[-2]
        bt_trend = "rising" if last["avg_breakthrough"] > prev["avg_breakthrough"] + 0.3 else (
            "falling" if last["avg_breakthrough"] < prev["avg_breakthrough"] - 0.3 else "stable"
        )
        rk_trend = "rising" if last["avg_risk"] > prev["avg_risk"] + 0.3 else (
            "falling" if last["avg_risk"] < prev["avg_risk"] - 0.3 else "stable"
        )
        if bt_trend == "rising" and rk_trend == "rising":
            summary = (
                f"The latest week shows both breakthrough scores and risk signals rising simultaneously "
                f"(avg breakthrough {last['avg_breakthrough']:.1f}, avg risk {last['avg_risk']:.1f}). "
                "This dual-escalation pattern suggests transformative advances arriving alongside heightened risk exposure."
            )
        elif bt_trend == "rising":
            summary = (
                f"Breakthrough scores are trending upward (avg {last['avg_breakthrough']:.1f}) while risk signals "
                f"remain {rk_trend}. The landscape is skewing toward capability gains without a proportional risk increase."
            )
        elif rk_trend == "rising":
            summary = (
                f"Risk signals are climbing (avg {last['avg_risk']:.1f}) while breakthrough scores stay {bt_trend}. "
                "Events are introducing new threat surfaces without equivalent positive capability advances."
            )
        else:
            summary = (
                f"Both breakthrough and risk scores are holding broadly stable this week "
                f"(avg breakthrough {last['avg_breakthrough']:.1f}, avg risk {last['avg_risk']:.1f}). "
                "The AI signal stream reflects a consolidation phase rather than rapid escalation."
            )
    elif len(recent) == 1:
        last = recent[-1]
        summary = (
            f"Only one active week found — breakthrough avg {last['avg_breakthrough']:.1f}, "
            f"risk avg {last['avg_risk']:.1f}. More events will sharpen this trend."
        )
    else:
        summary = "Insufficient dated events to compute a trend. Ensure published_at is populated."

    return {
        "title": "Risk vs Breakthrough Trend",
        "summary": summary,
        "chart_points": chart_points,
    }


def _domain_signal_label(delta: float, recent_count: int) -> str:
    """One concise intelligence label for a rising domain."""
    if delta >= 2.0:
        return "Accelerating fast"
    if delta >= 1.0:
        return "Strong surge"
    if delta >= 0.3:
        strength = "high activity" if recent_count >= 5 else "moderate activity"
        return f"Rising · {strength}"
    return "Slight uptick"


def _compute_domain_momentum(db, domain_names: dict[str, str]) -> dict:
    """
    Fastest-Rising AI Domain — compares the last 30 days (current) vs the
    30 days before that (previous) using events.created_at so that recently
    ingested articles are reflected immediately regardless of published_at.

    Windows:
      current  = [now - 30d, now]
      previous = [now - 60d, now - 30d)

    Age protection (optional):
      Events whose published_at exists and is older than
      RISING_DOMAIN_OLD_ARTICLE_DAYS are excluded.  Events with a NULL
      published_at are kept.

    Ranking rules:
      1. Compute (current_count - previous_count) per domain.
      2. A domain with current_count == 0 cannot be the top_domain.
      3. If no domain has current events, return a neutral state.
    """
    now = datetime.now(timezone.utc)
    cutoff_current  = now - timedelta(days=RISING_DOMAIN_WINDOW_DAYS)          # -30d
    cutoff_previous = now - timedelta(days=RISING_DOMAIN_WINDOW_DAYS * 2)      # -60d
    cutoff_old_article = now - timedelta(days=RISING_DOMAIN_OLD_ARTICLE_DAYS)  # -90d

    # --- Fetch events with created_at and published_at from the last 60 days ---
    # We need created_at (always present) + published_at (for age protection).
    # Supabase gte/lte use ISO strings.
    try:
        resp = (
            db.table("events")
            .select("id, created_at, published_at, event_domains(domains(slug, name))")
            .gte("created_at", cutoff_previous.isoformat())
            .order("created_at", desc=True)
            .execute()
        )
        rows = resp.data or []
    except Exception:
        rows = []

    if not rows:
        return {
            "title": "Fastest-Rising AI Domain",
            "summary": "No events yet — domain momentum will appear once articles are ingested.",
            "top_domain": None,
            "runners_up": [],
        }

    # --- Count events per domain per window, applying age protection ---
    current_counts:  dict[str, int] = defaultdict(int)
    previous_counts: dict[str, int] = defaultdict(int)

    for row in rows:
        created_raw  = row.get("created_at") or ""
        published_raw = row.get("published_at") or ""

        created_dt  = _parse_iso_date(created_raw)
        if not created_dt:
            continue

        # Age protection: skip events whose published_at is older than 90 days
        if published_raw:
            published_dt = _parse_iso_date(published_raw)
            if published_dt and published_dt < cutoff_old_article:
                continue  # too old — backfilled article, exclude

        # Extract domain slugs from the join
        slugs: list[str] = []
        for ed in row.get("event_domains", []):
            domain_obj = ed.get("domains") if ed else None
            if domain_obj and domain_obj.get("slug"):
                slugs.append(domain_obj["slug"])

        if not slugs:
            continue  # skip unlinked events

        in_current  = created_dt >= cutoff_current
        in_previous = cutoff_previous <= created_dt < cutoff_current

        for slug in slugs:
            if in_current:
                current_counts[slug] += 1
            elif in_previous:
                previous_counts[slug] += 1

    # --- Gather all domain slugs seen in either window ---
    all_slugs = set(current_counts) | set(previous_counts)

    if not all_slugs:
        return {
            "title": "Fastest-Rising AI Domain",
            "summary": "No events yet — domain momentum will appear once articles are ingested.",
            "top_domain": None,
            "runners_up": [],
        }

    # --- Build scored rows ---
    rows_scored: list[dict] = []
    for slug in all_slugs:
        cur  = current_counts.get(slug, 0)
        prev = previous_counts.get(slug, 0)
        delta = cur - prev
        name  = domain_names.get(slug, slug)
        rows_scored.append({
            "slug":          slug,
            "name":          name,
            "current_count": cur,
            "prev_count":    prev,
            "delta":         delta,
        })

    # --- Rank: strictly rising (delta > 0, current > 0) first ---
    rising = [
        r for r in rows_scored
        if r["delta"] > 0 and r["current_count"] > 0
    ]
    rising.sort(key=lambda r: (r["delta"], r["current_count"]), reverse=True)

    # Neutral state: no domain has current events
    has_any_current = any(r["current_count"] > 0 for r in rows_scored)
    if not has_any_current:
        return {
            "title": "Fastest-Rising AI Domain",
            "summary": (
                "No new events have been ingested in the last 30 days. "
                "Domain momentum will update once articles are processed."
            ),
            "top_domain": None,
            "runners_up": [],
        }

    # Fall back to highest current_count flat domains if nothing is strictly rising
    if not rising:
        candidates = [
            r for r in rows_scored if r["current_count"] > 0
        ]
        candidates.sort(key=lambda r: (r["current_count"], r["delta"]), reverse=True)
        candidates = candidates[:3]
        is_rising_mode = False
    else:
        candidates = rising[:3]
        is_rising_mode = True

    def _direction(r: dict) -> str:
        if r["delta"] > 0:
            return "up"
        if r["delta"] < 0:
            return "down"
        return "flat"

    def _to_item(r: dict) -> dict:
        return {
            "name":         r["name"],
            "slug":         r["slug"],
            "direction":    _direction(r),
            "delta":        r["delta"],
            "recent_count": r["current_count"],
            "signal_label": _domain_signal_label(float(r["delta"]), r["current_count"]),
        }

    top       = candidates[0]
    runners_up = candidates[1:3]

    if is_rising_mode:
        summary = (
            f"{top['name']} is the fastest-rising domain in the last 30 days, "
            f"up +{top['delta']} event{'s' if top['delta'] != 1 else ''} vs the prior 30-day window "
            f"({top['current_count']} event{'s' if top['current_count'] != 1 else ''} ingested recently)."
        )
    else:
        summary = (
            f"No domain shows a clear surge in the last 30 days. "
            f"{top['name']} leads with {top['current_count']} event{'s' if top['current_count'] != 1 else ''} ingested."
        )

    return {
        "title": "Fastest-Rising AI Domain",
        "summary": summary,
        "top_domain": _to_item(top),
        "runners_up": [_to_item(r) for r in runners_up],
    }


def _leader_signal_label(avg_bt: float, avg_rk: float, mentions: int) -> str:
    """Compact intelligence tag for a lab/model entry."""
    high_bt = avg_bt >= 7.5
    high_rk = avg_rk >= 7.0
    if high_bt and high_rk:
        return "High BT · High Risk"
    if high_bt:
        return "High Breakthrough"
    if high_rk:
        return "Risk Watch"
    if mentions >= 5:
        return "Wide Coverage"
    if avg_bt >= 6.0:
        return "Strong Signal"
    return "Active"


def _compute_lab_model_movement(events: list) -> dict:
    """
    Breakthrough Leaders: Labs & Models.
    Ranks orgs and model families by a composite influence score:
      composite = mentions * avg_breakthrough + 0.4 * avg_risk
    Returns top 3 across orgs + models combined, each with a signal_label.
    """
    if not events:
        return {
            "title": "Breakthrough Leaders: Labs & Models",
            "summary": "No events to scan — ingest articles to surface org and model signals.",
            "items": [],
        }

    # Accumulate (breakthrough, risk) pairs per entity
    org_data: dict[str, list[tuple[float, float]]] = defaultdict(list)
    model_data: dict[str, list[tuple[float, float]]] = defaultdict(list)

    for event in events:
        text = f"{event.title} {event.summary}".lower()
        bt = _score_breakthrough(event)
        rk = _score_risk(event)

        matched_org: set[str] = set()
        for kw in sorted(_ORG_KEYWORDS, key=len, reverse=True):
            if kw in text:
                display = _ORG_KEYWORDS[kw]
                if display not in matched_org:
                    org_data[display].append((bt, rk))
                    matched_org.add(display)

        # Per-event dedup set: prevents the same display name from being
        # counted more than once per event (e.g. if "claude" appears in both
        # title and summary, or via two aliases for the same model family).
        matched_model: set[str] = set()
        for pattern, display in _MODEL_PATTERNS:
            if display not in matched_model and pattern.search(text):
                model_data[display].append((bt, rk))
                matched_model.add(display)

    def _build_rows(data: dict[str, list[tuple[float, float]]], entity_type: str) -> list[dict]:
        rows = []
        for name, pairs in data.items():
            bt_scores = [p[0] for p in pairs]
            rk_scores = [p[1] for p in pairs]
            avg_bt = round(mean(bt_scores), 2)
            avg_rk = round(mean(rk_scores), 2)
            mentions = len(pairs)
            composite = mentions * avg_bt + 0.4 * avg_rk
            rows.append({
                "name": name,
                "type": entity_type,
                "mention_count": mentions,
                "avg_breakthrough": avg_bt,
                "avg_risk": avg_rk,
                "composite": composite,
                "signal_label": _leader_signal_label(avg_bt, avg_rk, mentions),
            })
        return rows

    all_rows = _build_rows(org_data, "lab") + _build_rows(model_data, "model")
    # Sort by composite influence score, take top 3
    top3 = sorted(all_rows, key=lambda r: r["composite"], reverse=True)[:3]
    # Remove the internal composite field from the response
    items = [{k: v for k, v in r.items() if k != "composite"} for r in top3]

    if items:
        leader = items[0]
        label = "lab" if leader["type"] == "lab" else "model family"
        second = items[1]["name"] if len(items) > 1 else None
        bt_adj = "exceptionally high" if leader["avg_breakthrough"] >= 8.0 else "strong" if leader["avg_breakthrough"] >= 6.5 else "moderate"
        summary = (
            f"{leader['name']} currently shows the strongest breakthrough footprint among tracked {label}s "
            f"— {bt_adj} avg breakthrough score of {leader['avg_breakthrough']:.1f} "
            f"across {leader['mention_count']} mention{'s' if leader['mention_count'] != 1 else ''}."
        )
        if second:
            summary += f" {second} follows as the next strongest breakthrough signal."
    else:
        summary = (
            "No recognised AI labs or model families detected in the current event window. "
            "The feed may contain unlabelled or niche sources."
        )

    return {
        "title": "Breakthrough Leaders: Labs & Models",
        "summary": summary,
        "items": items,
    }


@router.get("/intelligence-summary")
def get_intelligence_summary():
    """
    Returns 3 backend-computed AI intelligence insights:
    1. Risk vs Breakthrough Trend  — weekly chart + natural-language summary
    2. Fastest-Rising AI Domain    — top 1-3 rising domains with signal_label
    3. Breakthrough Leaders        — top 3 labs/models by composite influence score
    """
    db = _ensure_db()
    domain_names = _domain_map(db)
    events = _fetch_all_events(db)

    return {
        "risk_breakthrough": _compute_risk_breakthrough(events),
        # domain_momentum now queries created_at directly for accurate 30-day windows
        "domain_momentum": _compute_domain_momentum(db, domain_names),
        "lab_model_movement": _compute_lab_model_movement(events),
    }