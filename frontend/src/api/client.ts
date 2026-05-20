import axios from 'axios';
import type {
  AIEvent,
  AnalyticsDashboardResponse,
  AnalyticsDomainMomentum,
  AnalyticsEcosystem,
  AnalyticsInsight,
  AnalyticsOverview,
  AnalyticsTrends,
  Domain,
  Insight,
  IntelligenceSummaryResponse,
} from '../types';


const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({ baseURL: BASE_URL, timeout: 10000 });

export async function fetchEvents(domain?: string): Promise<AIEvent[]> {
  const params = domain ? { domain } : {};
  const res = await api.get<AIEvent[]>('/events', { params });
  return res.data;
}

export async function fetchEventById(id: string): Promise<AIEvent> {
  const res = await api.get<AIEvent>(`/events/${id}`);
  return res.data;
}

export async function fetchDomains(): Promise<Domain[]> {
  const res = await api.get<Domain[]>('/domains');
  return res.data;
}

export async function fetchInsights(): Promise<Insight[]> {
  const res = await api.get<Insight[]>('/insights');
  return res.data;
}

export async function fetchAnalyticsOverview(domain?: string): Promise<AnalyticsOverview> {
  const params = domain ? { domain } : {};
  const res = await api.get<AnalyticsOverview>('/analytics/overview', { params });
  return res.data;
}

export async function fetchAnalyticsTrends(domain?: string): Promise<AnalyticsTrends> {
  const params = domain ? { domain } : {};
  const res = await api.get<AnalyticsTrends>('/analytics/trends', { params });
  return res.data;
}

export async function fetchAnalyticsDomainMomentum(domain?: string): Promise<AnalyticsDomainMomentum> {
  const params = domain ? { domain } : {};
  const res = await api.get<AnalyticsDomainMomentum>('/analytics/domain-momentum', { params });
  return res.data;
}

export async function fetchAnalyticsEcosystem(domain?: string): Promise<AnalyticsEcosystem> {
  const params = domain ? { domain } : {};
  const res = await api.get<AnalyticsEcosystem>('/analytics/ecosystem', { params });
  return res.data;
}

export async function fetchAnalyticsInsights(domain?: string): Promise<AnalyticsInsight[]> {
  const params = domain ? { domain } : {};
  const res = await api.get<AnalyticsInsight[]>('/analytics/insights', { params });
  return res.data;
}

export async function fetchAnalyticsDashboard(domain?: string): Promise<AnalyticsDashboardResponse> {
  const params = domain ? { domain } : {};
  const res = await api.get<AnalyticsDashboardResponse>('/analytics/dashboard', { params });
  return res.data;
}

export async function getPreferences(token?: string): Promise<string[]> {
  const headers = token ? { Authorization: `Bearer ${token}` } : {};
  const res = await api.get<{ user_id: string; interests: string[] }>('/api/me/preferences', { headers });
  return res.data.interests || [];
}

export async function setPreferences(token: string, interests: string[]): Promise<{ user_id: string; interests: string[] }> {
  const headers = token ? { Authorization: `Bearer ${token}` } : {};
  const res = await api.post<{ user_id: string; interests: string[] }>('/api/me/preferences', { interests }, { headers });
  return res.data;
}

export async function fetchIntelligenceSummary(): Promise<IntelligenceSummaryResponse> {
  const res = await api.get<IntelligenceSummaryResponse>('/analytics/intelligence-summary');
  return res.data;
}
