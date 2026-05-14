export interface Source {
  name: string;
  credibility_score: number;
}

export interface EventScore {
  breakthrough_score: number;
  risk_signal: number;
  evidence_level: string;
  impact_areas: string[];
  trend_momentum: number;
}

export interface AIEvent {
  id: string;
  title: string;
  summary: string;
  url: string;
  published_at: string;
  source: Source;
  domains: string[];
  scores: EventScore;
}

export interface Domain {
  id: string;
  name: string;
  slug: string;
  description: string;
  icon: string;
}

export interface Insight {
  domain_slug: string;
  domain_name: string;
  summary_text: string;
  top_event_ids: string[];
  momentum_delta: number;
  date: string;
}
