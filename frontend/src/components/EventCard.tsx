import type { AIEvent } from '../types';
import ScoreBadge from './ScoreBadge';

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

export default function EventCard({ event }: { event: AIEvent }) {
  return (
    <article id={`event-${event.id}`} className="card event-card">
      <div className="event-card-header">
        <div>
          <div className="event-source">{event.source.name}</div>
          <div className="event-credibility">Credibility: {(event.source.credibility_score * 100).toFixed(0)}%</div>
        </div>
        <div className="event-date">{formatDate(event.published_at)}</div>
      </div>
      <h3 className="event-title">{event.title}</h3>
      <p className="event-summary">{event.summary}</p>
      <div className="event-scores">
        <ScoreBadge type="breakthrough" value={event.scores.breakthrough_score} />
        <ScoreBadge type="risk"         value={event.scores.risk_signal} />
        <ScoreBadge type="evidence"     value={event.scores.evidence_level} />
        <ScoreBadge type="momentum"     value={event.scores.trend_momentum} />
      </div>
      <div className="event-domains">
        {event.domains.map(d => <span key={d} className="domain-pill">{d.replace(/-/g,' ')}</span>)}
      </div>
      <div className="event-meta">
        <div/>
        <a href={event.url} target="_blank" rel="noopener noreferrer" className="event-link" onClick={e => e.stopPropagation()}>
          Read source →
        </a>
      </div>
    </article>
  );
}
