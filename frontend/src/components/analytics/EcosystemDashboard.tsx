import type { AnalyticsEcosystem } from '../../types';

type Props = {
  ecosystem: AnalyticsEcosystem;
};

function scoreClass(value: number) {
  if (value >= 7) return 'strong';
  if (value >= 4.5) return 'medium';
  return 'soft';
}

function EntityRank({
  title,
  items,
  accent,
}: {
  title: string;
  items: AnalyticsEcosystem['organizations'];
  accent: 'org' | 'model';
}) {
  const max = Math.max(1, ...items.map(item => item.count));

  return (
    <section className="card analytics-subcard">
      <div className="analytics-subcard-header">
        <div>
          <h4>{title}</h4>
          <p>{accent === 'org' ? 'Who is driving the event stream' : 'Which model families dominate the signal'}</p>
        </div>
      </div>
      <div className="analytics-entity-stack">
        {items.map(item => (
          <article key={item.name} className="analytics-entity-row">
            <div className="analytics-entity-head">
              <span className="analytics-entity-name">{item.name}</span>
              <span className="analytics-entity-count">{item.count} events</span>
            </div>
            <div className="analytics-entity-bar-track">
              <div className="analytics-entity-bar-fill" style={{ width: `${(item.count / max) * 100}%` }} />
            </div>
            <div className="analytics-entity-metrics">
              <span className={`analytics-metric-chip ${scoreClass(item.avg_breakthrough)}`}>Breakthrough {item.avg_breakthrough.toFixed(2)}</span>
              <span className={`analytics-metric-chip ${scoreClass(item.avg_risk)}`}>Risk {item.avg_risk.toFixed(2)}</span>
              <span className="analytics-metric-chip soft">Momentum {item.avg_momentum.toFixed(2)}</span>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

export default function EcosystemDashboard({ ecosystem }: Props) {
  const topOrg = ecosystem.organizations[0];
  const topFamily = ecosystem.model_families[0];

  return (
    <section className="analytics-ecosystem-shell">
      <div className="card analytics-section-intro">
        <div>
          <p className="analytics-eyebrow">Ecosystem comparison</p>
          <h4>Backend entity signals</h4>
          <p>
            The backend clusters the stream by source organization and inferred model family so the dashboard can explain who is shaping the current AI surface.
          </p>
        </div>
        {(topOrg || topFamily) && (
          <div className="analytics-callout-strip">
            {topOrg && <span className="analytics-callout">Top org: {topOrg.name}</span>}
            {topFamily && <span className="analytics-callout">Top family: {topFamily.name}</span>}
          </div>
        )}
      </div>

      <div className="analytics-ecosystem-grid">
        <EntityRank title="Organizations" items={ecosystem.organizations.slice(0, 6)} accent="org" />
        <EntityRank title="Model families" items={ecosystem.model_families.slice(0, 6)} accent="model" />
      </div>
    </section>
  );
}
