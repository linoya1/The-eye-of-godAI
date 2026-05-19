import axios from 'axios';
import type { AIEvent, Domain, Insight } from '../types';

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
