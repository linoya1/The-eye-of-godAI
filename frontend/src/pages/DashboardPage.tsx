import { useState, useEffect } from 'react';
import Navbar from '../components/Navbar';
import EventCard from '../components/EventCard';
import { fetchEvents, fetchDomains, fetchInsights } from '../api/client';
import type { AIEvent, Domain, Insight } from '../types';
import ScoreLegend from '../components/ScoreLegend';
export default function DashboardPage() {
  const [events, setEvents] = useState<AIEvent[]>([]);
  const [domains, setDomains] = useState<Domain[]>([]);
  const [insights, setInsights] = useState<Insight[]>([]);
  const [activeFilter, setActiveFilter] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    Promise.all([fetchDomains(), fetchInsights()])
      .then(([d, i]) => { setDomains(d); setInsights(i); })
      .catch(() => setError('Could not load domains. Is the backend running?'));

    fetchEvents()
      .then(setEvents)
      .catch(() => setError('Could not load events. Is the backend running on port 8000?'))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    fetchEvents(activeFilter ?? undefined)
      .then(setEvents)
      .catch(() => {});
  }, [activeFilter]);

  return (
    <>
      <Navbar showAuth={false} />
      <div className="page container">
        <div className="section-header">
          <div>
            <h2>Your AI Intelligence Dashboard</h2>
            <p className="section-subtitle">
              {activeFilter
                ? `Showing events for: ${activeFilter.replace(/-/g, ' ')}`
                : 'Showing all recent AI events across all domains'}
            </p>
          </div>
        </div>

        <div className="dashboard-layout">
          <aside className="dashboard-sidebar">
            <p className="sidebar-title">Filter by Domain</p>
            <button
              className={`domain-filter-btn ${activeFilter === null ? 'active' : ''}`}
              onClick={() => setActiveFilter(null)}
            >
              🌐 All Domains
            </button>
            {domains.map(d => (
              <button
                key={d.slug}
                className={`domain-filter-btn ${activeFilter === d.slug ? 'active' : ''}`}
                onClick={() => setActiveFilter(activeFilter === d.slug ? null : d.slug)}
              >
                {d.icon} {d.name}
              </button>
            ))}

            {insights.length > 0 && (
              <div style={{ marginTop: 28 }}>
                <p className="sidebar-title">Today's Insights</p>
                {insights.map(ins => (
                  <div key={ins.domain_slug} className="card insight-panel">
                    <div className="insight-domain">{ins.domain_name}</div>
                    <p className="insight-text">{ins.summary_text}</p>
                    <div className="momentum-bar">
                      <span className="momentum-label">Momentum:</span>
                      <span className={`momentum-value ${ins.momentum_delta >= 0 ? 'up' : 'dn'}`}>
                        {ins.momentum_delta >= 0 ? '↑' : '↓'} {Math.abs(ins.momentum_delta * 100).toFixed(0)}%
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </aside>

          <main className="dashboard-main">
            {loading && (
              <div className="loading-state">
                <div className="loading-spinner" />
                <p>Loading AI events…</p>
              </div>
            )}
            {error && <div className="error-state">⚠️ {error}</div>}
            {!loading && !error && (
              <>
                <ScoreLegend />
                <div className="events-grid">
                {events.length === 0 ? (
                  <p style={{ color: 'var(--text-muted)', textAlign: 'center', padding: 40 }}>
                    No events found for this domain filter.
                  </p>
                ) : (
                  events.map(event => <EventCard key={event.id} event={event} />)
                )}
              </div>
              </>
            )}
          </main>
        </div>
      </div>
    </>
  );
}
