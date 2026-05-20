import { useState, useEffect } from 'react';
import Navbar from '../components/Navbar';
import { fetchDomains, fetchEvents, fetchIntelligenceSummary } from '../api/client';
import type { AIEvent, Domain, IntelligenceSummaryResponse } from '../types';
import ScoreLegend from '../components/ScoreLegend';
import EventCard from '../components/EventCard';
import IntelligenceSummary from '../components/IntelligenceSummary';
import TopResearchSignals from '../components/TopResearchSignals';


export default function DashboardPage() {
  const [events, setEvents] = useState<AIEvent[]>([]);
  const [domains, setDomains] = useState<Domain[]>([]);
  const [intelligence, setIntelligence] = useState<IntelligenceSummaryResponse | null>(null);
  const [activeFilter, setActiveFilter] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [intelLoading, setIntelLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [intelError, setIntelError] = useState<string | null>(null);

  // Fetch domains + events (re-runs when filter changes)
  useEffect(() => {
    let cancelled = false;
    const domain = activeFilter ?? undefined;

    setLoading(true);
    setError(null);

    Promise.all([fetchDomains(), fetchEvents(domain)])
      .then(([d, e]) => {
        if (cancelled) return;
        setDomains(d);
        setEvents(e);
      })
      .catch(() => {
        if (!cancelled) {
          setError('Could not load events. Is the backend running on port 8000?');
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => { cancelled = true; };
  }, [activeFilter]);

  // Fetch intelligence summary once (not filter-dependent)
  useEffect(() => {
    let cancelled = false;
    setIntelLoading(true);
    setIntelError(null);

    fetchIntelligenceSummary()
      .then(data => { if (!cancelled) setIntelligence(data); })
      .catch(() => {
        if (!cancelled)
          setIntelError('Could not load intelligence summary from the backend.');
      })
      .finally(() => { if (!cancelled) setIntelLoading(false); });

    return () => { cancelled = true; };
  }, []);

  return (
    <>
      <Navbar showAuth={true} />
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
          </aside>

          <main className="dashboard-main">
            {/* ── Intelligence Summary (3 backend analytics) ── */}
            {intelLoading && (
              <div className="intel-loading">
                <div className="loading-spinner" />
                Analysing your AI event database…
              </div>
            )}
            {intelError && (
              <div className="intel-error">⚠️ {intelError}</div>
            )}
            {!intelLoading && !intelError && intelligence && (
              <IntelligenceSummary data={intelligence} />
            )}

            {/* ── Top Research Signals (curated, static) ── */}
            <TopResearchSignals visibleEventIds={events.map(e => e.id)} />

            {/* ── Event feed ── */}
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
                <div className="event-feed-header">
                  <h4 className="event-feed-title">Recent signal stream</h4>
                  <span className="event-feed-count">{events.length} events</span>
                </div>
                {events.length === 0 ? (
                  <p className="event-feed-empty">No events found for this domain filter.</p>
                ) : (
                  <div className="events-grid">
                    {events.map(event => (
                      <EventCard key={event.id} event={event} />
                    ))}
                  </div>
                )}
              </>
            )}
          </main>
        </div>
      </div>
    </>
  );
}
