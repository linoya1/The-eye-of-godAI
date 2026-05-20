from pydantic import BaseModel


class Source(BaseModel):
    name: str
    credibility_score: float


class EventScore(BaseModel):
    breakthrough_score: float
    risk_signal: float
    evidence_level: str
    impact_areas: list[str]
    trend_momentum: float


class Event(BaseModel):
    id: str
    title: str
    summary: str
    url: str
    published_at: str
    source: Source
    domains: list[str]
    scores: EventScore


class Domain(BaseModel):
    id: str
    name: str
    slug: str
    description: str
    icon: str


class Insight(BaseModel):
    domain_slug: str
    domain_name: str
    summary_text: str
    top_event_ids: list[str]
    momentum_delta: float
    date: str


class HealthResponse(BaseModel):
    status: str
    version: str
    message: str


class AnalyticsDatePoint(BaseModel):
    date: str
    event_count: int
    avg_breakthrough: float
    avg_risk: float
    avg_momentum: float


class AnalyticsScatterPoint(BaseModel):
    id: str
    title: str
    domain: str
    source: str
    breakthrough: float
    risk: float
    momentum: float
    evidence_level: str
    url: str


class EvidenceDistributionItem(BaseModel):
    label: str
    count: int
    share: float


class EmergingTopicItem(BaseModel):
    id: str
    title: str
    domain: str
    source: str
    breakthrough: float
    risk: float
    momentum: float
    evidence_level: str
    url: str
    signal: str


class DomainMomentumItem(BaseModel):
    slug: str
    name: str
    recent_count: int
    recent_avg_momentum: float
    previous_avg_momentum: float
    delta: float
    direction: str
    top_event_ids: list[str]
    summary: str


class EcosystemEntityItem(BaseModel):
    name: str
    count: int
    avg_breakthrough: float
    avg_risk: float
    avg_momentum: float
    high_risk_count: int
    high_breakthrough_count: int
    top_event_ids: list[str]


class AnalyticsOverview(BaseModel):
    window_days: int
    total_events: int
    total_domains: int
    evidence_distribution: list[EvidenceDistributionItem]
    emerging_topics: list[EmergingTopicItem]
    notable_shifts: list[str]


class AnalyticsTrends(BaseModel):
    window_days: int
    timeline: list[AnalyticsDatePoint]
    risk_breakthrough_points: list[AnalyticsScatterPoint]


class AnalyticsDomainMomentum(BaseModel):
    window_days: int
    domains: list[DomainMomentumItem]


class AnalyticsEcosystem(BaseModel):
    window_days: int
    organizations: list[EcosystemEntityItem]
    model_families: list[EcosystemEntityItem]


class AnalyticsInsight(BaseModel):
    title: str
    summary: str
    confidence: str
    category: str


class AnalyticsDashboardResponse(BaseModel):
    overview: AnalyticsOverview
    trends: AnalyticsTrends
    domain_momentum: AnalyticsDomainMomentum
    ecosystem: AnalyticsEcosystem
    insights: list[AnalyticsInsight]
