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
