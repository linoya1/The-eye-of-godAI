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
  domain_slug?: string;
  domain_name?: string;
  source_name?: string;
  author?: string;
  summary_text?: string;
  description?: string;
  body?: string;
  tags?: string[];
  breakthrough?: number;
  risk?: number;
  momentum?: number;
  created_at?: string;
  timestamp?: string;
  created?: string;
  createdAt?: string;
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

export interface AnalyticsDatePoint {
  date: string;
  event_count: number;
  avg_breakthrough: number;
  avg_risk: number;
  avg_momentum: number;
}

export interface AnalyticsScatterPoint {
  id: string;
  title: string;
  domain: string;
  source: string;
  breakthrough: number;
  risk: number;
  momentum: number;
  evidence_level: string;
  url: string;
}

export interface EvidenceDistributionItem {
  label: string;
  count: number;
  share: number;
}

export interface EmergingTopicItem {
  id: string;
  title: string;
  domain: string;
  source: string;
  breakthrough: number;
  risk: number;
  momentum: number;
  evidence_level: string;
  url: string;
  signal: string;
}

export interface DomainMomentumItem {
  slug: string;
  name: string;
  recent_count: number;
  recent_avg_momentum: number;
  previous_avg_momentum: number;
  delta: number;
  direction: 'up' | 'down' | 'flat' | string;
  top_event_ids: string[];
  summary: string;
}

export interface EcosystemEntityItem {
  name: string;
  count: number;
  avg_breakthrough: number;
  avg_risk: number;
  avg_momentum: number;
  high_risk_count: number;
  high_breakthrough_count: number;
  top_event_ids: string[];
}

export interface AnalyticsOverview {
  window_days: number;
  total_events: number;
  total_domains: number;
  evidence_distribution: EvidenceDistributionItem[];
  emerging_topics: EmergingTopicItem[];
  notable_shifts: string[];
}

export interface AnalyticsTrends {
  window_days: number;
  timeline: AnalyticsDatePoint[];
  risk_breakthrough_points: AnalyticsScatterPoint[];
}

export interface AnalyticsDomainMomentum {
  window_days: number;
  domains: DomainMomentumItem[];
}

export interface AnalyticsEcosystem {
  window_days: number;
  organizations: EcosystemEntityItem[];
  model_families: EcosystemEntityItem[];
}

export interface AnalyticsInsight {
  title: string;
  summary: string;
  confidence: 'high' | 'medium' | 'low' | string;
  category: string;
}

export interface AnalyticsDashboardResponse {
  overview: AnalyticsOverview;
  trends: AnalyticsTrends;
  domain_momentum: AnalyticsDomainMomentum;
  ecosystem: AnalyticsEcosystem;
  insights: AnalyticsInsight[];
}

// --- Intelligence Summary (new simplified analytics) ---

export interface RiskBreakthroughChartPoint {
  week: string;
  event_count: number;
  avg_breakthrough: number;
  avg_risk: number;
}

export interface RiskBreakthroughSection {
  title: string;
  summary: string;
  chart_points: RiskBreakthroughChartPoint[];
}

export interface DomainMomentumSectionItem {
  name: string;
  slug: string;
  direction: 'up' | 'down' | 'flat' | string;
  delta: number;
  recent_count: number;
  signal_label: string;
}

export interface DomainMomentumSection {
  title: string;
  summary: string;
  top_domain: DomainMomentumSectionItem | null;
  runners_up: DomainMomentumSectionItem[];
}

export interface LabModelItem {
  name: string;
  mention_count: number;
  avg_breakthrough: number;
  avg_risk: number;
  type: 'lab' | 'model' | string;
  signal_label: string;
}

export interface LabModelSection {
  title: string;
  summary: string;
  items: LabModelItem[];
}

export interface IntelligenceSummaryResponse {
  risk_breakthrough: RiskBreakthroughSection;
  domain_momentum: DomainMomentumSection;
  lab_model_movement: LabModelSection;
}
