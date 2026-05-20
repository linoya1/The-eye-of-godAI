import { useMemo } from 'react';
import type {
  AnalyticsDashboardResponse,
  AnalyticsDomainMomentum,
  AnalyticsTrends,
  EvidenceDistributionItem,
  EmergingTopicItem,
} from '../../types';
import EcosystemDashboard from './EcosystemDashboard';
import KPICard from './KPICard';
import LeaderboardCard from './LeaderboardCard';
import InsightCard from './InsightCard';

type Props = {
  data: AnalyticsDashboardResponse;
  activeFilterLabel?: string;
};

function buildPath(points: number[], width: number, height: number, padding: number) {
  if (points.length === 0) {
    return '';
  }

  const min = Math.min(...points);
  const max = Math.max(...points);
  const range = Math.max(1, max - min);

  return points
    .map((value, index) => {
      const x = padding + (index / Math.max(1, points.length - 1)) * (width - padding * 2);
      const y = height - padding - ((value - min) / range) * (height - padding * 2);
      return `${index === 0 ? 'M' : 'L'} ${x.toFixed(1)} ${y.toFixed(1)}`;
    })
    .join(' ');
}

function TrendLineChart({ points }: { points: AnalyticsTrends['timeline'] }) {
  const values = points.map(point => point.event_count);
  const width = 760;
  const height = 220;
  const padding = 28;
  const path = buildPath(values, width, height, padding);

  return (
    <div className="analytics-chart-wrap">
      <svg className="analytics-chart" viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Event trend line chart">
        <defs>
          <linearGradient id="trendFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="rgba(6,182,212,0.35)" />
            <stop offset="100%" stopColor="rgba(6,182,212,0.02)" />
          </linearGradient>
        </defs>
        <line x1={padding} y1={padding} x2={padding} y2={height - padding} className="analytics-axis" />
        <line x1={padding} y1={height - padding} x2={width - padding} y2={height - padding} className="analytics-axis" />
        <path
          d={`${path} L ${width - padding} ${height - padding} L ${padding} ${height - padding} Z`}
          fill="url(#trendFill)"
        />
        <path d={path} fill="none" className="analytics-line analytics-line--primary" />
        {points.map((point, index) => {
          const x = padding + (index / Math.max(1, points.length - 1)) * (width - padding * 2);
          const y = height - padding - ((point.event_count - Math.min(...values)) / Math.max(1, Math.max(...values) - Math.min(...values))) * (height - padding * 2);
          return <circle key={point.date} cx={x} cy={y} r="4.5" className="analytics-point analytics-point--primary" />;
        })}
      </svg>
      <div className="analytics-chart-caption">
        {points.length > 0 ? (
          <>
            <span>Latest slice</span>
            <strong>{points[points.length - 1].date}</strong>
            <span>{points[points.length - 1].event_count} events</span>
          </>
        ) : (
          <span>No timeline data available yet.</span>
        )}
      </div>
      <div className="analytics-metric-strip">
        {points.length > 0 && (
          <>
            <span className="analytics-metric-pill">Breakthrough {points[points.length - 1].avg_breakthrough.toFixed(2)}</span>
            <span className="analytics-metric-pill">Risk {points[points.length - 1].avg_risk.toFixed(2)}</span>
            <span className="analytics-metric-pill">Momentum {points[points.length - 1].avg_momentum.toFixed(2)}</span>
          </>
        )}
      </div>
    </div>
  );
}

function ScatterPlot({ points }: { points: AnalyticsTrends['risk_breakthrough_points'] }) {
  const width = 760;
  const height = 260;
  const padding = 30;

  return (
    <div className="analytics-chart-wrap">
      <svg className="analytics-chart" viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Risk versus breakthrough scatter plot">
        <rect x={padding} y={padding} width={width - padding * 2} height={height - padding * 2} className="analytics-scatter-frame" />
        <line x1={padding} y1={height / 2} x2={width - padding} y2={height / 2} className="analytics-axis analytics-axis--grid" />
        <line x1={width / 2} y1={padding} x2={width / 2} y2={height - padding} className="analytics-axis analytics-axis--grid" />
        <text x={padding} y={padding - 8} className="analytics-axis-label">High breakthrough</text>
        <text x={width - padding - 108} y={padding - 8} className="analytics-axis-label">High risk</text>
        <text x={padding} y={height - 10} className="analytics-axis-label">Low risk</text>
        <text x={width - padding - 120} y={height - 10} className="analytics-axis-label">Low breakthrough</text>
        {points.map(point => {
          const cx = padding + (point.breakthrough / 10) * (width - padding * 2);
          const cy = height - padding - (point.risk / 10) * (height - padding * 2);
          const alpha = Math.min(1, 0.35 + Math.abs(point.momentum) / 6);
          return (
            <g key={point.id}>
              <circle cx={cx} cy={cy} r="7" className="analytics-point analytics-point--scatter" style={{ opacity: alpha }}>
                <title>{`${point.title} | ${point.domain} | ${point.evidence_level}`}</title>
              </circle>
            </g>
          );
        })}
      </svg>
      <div className="analytics-chart-caption">
        <span>Points are ranked by combined signal, so the upper-right quadrant surfaces the most consequential events first.</span>
      </div>
    </div>
  );
}

function DistributionBars({ items }: { items: EvidenceDistributionItem[] }) {
  const max = Math.max(1, ...items.map(item => item.share));

  return (
    <div className="analytics-bar-stack">
      {items.map(item => (
        <div key={item.label} className="analytics-bar-row">
          <div className="analytics-bar-row-head">
            <span>{item.label}</span>
            <strong>{Math.round(item.share * 100)}%</strong>
          </div>
          <div className="analytics-bar-track">
            <div className="analytics-bar-fill analytics-bar-fill--cyan" style={{ width: `${(item.share / max) * 100}%` }} />
          </div>
        </div>
      ))}
    </div>
  );
}

function MomentumShifts({ items }: { items: AnalyticsDomainMomentum['domains'] }) {
  const max = Math.max(0.1, ...items.map(item => Math.abs(item.delta)));

  return (
    <div className="analytics-bar-stack">
      {items.map(item => (
        <article key={item.slug} className="analytics-bar-row analytics-domain-row">
          <div className="analytics-bar-row-head">
            <span>{item.name}</span>
            <strong className={item.direction === 'up' ? 'analytics-signal-up' : item.direction === 'down' ? 'analytics-signal-down' : ''}>
              {item.direction === 'up' ? '▲' : item.direction === 'down' ? '▼' : '•'} {item.delta.toFixed(2)}
            </strong>
          </div>
          <div className="analytics-bar-track">
            <div
              className={`analytics-bar-fill ${item.direction === 'up' ? 'analytics-bar-fill--up' : item.direction === 'down' ? 'analytics-bar-fill--down' : 'analytics-bar-fill--muted'}`}
              style={{ width: `${(Math.abs(item.delta) / max) * 100}%` }}
            />
          </div>
          <p className="analytics-row-summary">{item.summary}</p>
        </article>
      ))}
    </div>
  );
}

function EmergingTopicCards({ items }: { items: EmergingTopicItem[] }) {
  return (
    <div className="analytics-topic-grid">
      {items.map(item => (
        <article key={item.id} className="card analytics-topic-card">
          <div className="analytics-topic-top">
            <span className="analytics-topic-signal">{item.signal}</span>
            <span className="analytics-topic-domain">{item.domain}</span>
          </div>
          <h5>{item.title}</h5>
          <p>{item.source}</p>
          <div className="analytics-topic-metrics">
            <span>Breakthrough {item.breakthrough.toFixed(1)}</span>
            <span>Risk {item.risk.toFixed(1)}</span>
            <span>Momentum {item.momentum.toFixed(2)}</span>
          </div>
        </article>
      ))}
    </div>
  );
}

export default function AnalyticsDashboard({
  data,
  activeFilterLabel,
}: Props) {
  const { overview, trends, domainMomentum, ecosystem, insights } = data;
  const narrative = useMemo(() => {
    if (overview.notable_shifts.length > 0) {
      return overview.notable_shifts[0];
    }
    return 'The backend analytics layer has not identified a strong directional shift yet.';
  }, [overview.notable_shifts]);

  const latestTimelinePoint = trends.timeline.at(-1);
  const previousTimelinePoint = trends.timeline.at(-2);
  const eventDelta =
    latestTimelinePoint && previousTimelinePoint
      ? (latestTimelinePoint.event_count - previousTimelinePoint.event_count) / Math.max(1, previousTimelinePoint.event_count)
      : null;
  const topMomentumDomain = domainMomentum.domains[0];
  const topSignal = trends.risk_breakthrough_points[0];
  const topSource = ecosystem.organizations[0];
  const topFamily = ecosystem.model_families[0];

  return (
    <section className="analytics-shell">
      <div className="card analytics-hero-card">
        <div>
          <p className="analytics-eyebrow">Backend intelligence layer</p>
          <h3>{activeFilterLabel ? `Focused analytics for ${activeFilterLabel}` : 'Intelligence view across the full AI stream'}</h3>
          <p className="analytics-hero-copy">{narrative}</p>
        </div>
        <div className="analytics-callout-strip">
          {overview.notable_shifts.slice(0, 3).map(shift => (
            <span key={shift} className="analytics-callout">
              {shift}
            </span>
          ))}
          {topSource && <span className="analytics-callout">Top source: {topSource.name}</span>}
          {topFamily && <span className="analytics-callout">Top family: {topFamily.name}</span>}
        </div>
      </div>

      <div className="analytics-kpi-grid">
        <KPICard title="Events in window" value={overview.total_events} delta={eventDelta}>
          ●
        </KPICard>
        <KPICard title="Domains tracked" value={overview.total_domains}>
          ◌
        </KPICard>
        <KPICard
          title="Top momentum shift"
          value={topMomentumDomain ? `${topMomentumDomain.name}` : 'No signal'}
          delta={topMomentumDomain ? topMomentumDomain.delta / 10 : null}
        >
          {topMomentumDomain ? (topMomentumDomain.direction === 'up' ? '▲' : topMomentumDomain.direction === 'down' ? '▼' : '•') : '·'}
        </KPICard>
        <KPICard
          title="Highest-signal event"
          value={topSignal ? `${topSignal.breakthrough.toFixed(1)} / ${topSignal.risk.toFixed(1)}` : 'No event'}
        >
          ⚡
        </KPICard>
      </div>

      <div className="analytics-grid analytics-grid--two">
        <div className="card analytics-panel-card">
          <div className="analytics-card-header">
            <div>
              <h4>Trend detection</h4>
              <p>Event volume and score momentum over the latest window</p>
            </div>
            <span>{overview.window_days} days</span>
          </div>
          <TrendLineChart points={trends.timeline} />
        </div>

        <div className="card analytics-panel-card">
          <div className="analytics-card-header">
            <div>
              <h4>Risk vs breakthrough</h4>
              <p>Backend-ranked events in the highest-signal quadrant</p>
            </div>
            <span>{trends.risk_breakthrough_points.length} events</span>
          </div>
          <ScatterPlot points={trends.risk_breakthrough_points} />
        </div>
      </div>

      <div className="analytics-grid analytics-grid--two">
        <LeaderboardCard
          title="Momentum leaders"
          items={domainMomentum.domains.slice(0, 6).map(item => ({ key: item.name, score: item.delta }))}
        />
        <LeaderboardCard
          title="Source leaders"
          items={ecosystem.organizations.slice(0, 6).map(item => ({ key: item.name, count: item.count }))}
        />
      </div>

      <div className="analytics-grid analytics-grid--three">
        <div className="card analytics-panel-card">
          <div className="analytics-card-header">
            <div>
              <h4>Domain momentum shifts</h4>
              <p>Which areas are accelerating, cooling, or flattening</p>
            </div>
          </div>
          <MomentumShifts items={domainMomentum.domains.slice(0, 6)} />
        </div>

        <div className="card analytics-panel-card">
          <div className="analytics-card-header">
            <div>
              <h4>Evidence quality</h4>
              <p>How the current stream is distributed across evidence levels</p>
            </div>
            <span>{overview.total_events} events</span>
          </div>
          <DistributionBars items={overview.evidence_distribution} />
        </div>

        <div className="card analytics-panel-card">
          <div className="analytics-card-header">
            <div>
              <h4>Emerging topics</h4>
              <p>Signals that deserve attention before they become obvious</p>
            </div>
          </div>
          <EmergingTopicCards items={overview.emerging_topics.slice(0, 4)} />
        </div>
      </div>

      <EcosystemDashboard ecosystem={ecosystem} />

      <div className="card analytics-panel-card">
        <div className="analytics-card-header">
          <div>
            <h4>Intelligence takeaways</h4>
            <p>Concise backend-generated interpretations of the signal surface</p>
          </div>
        </div>
        <div className="analytics-insight-grid">
          {insights.map(insight => (
            <InsightCard
              key={`${insight.category}-${insight.title}`}
              title={insight.title}
              summary={insight.summary}
              confidence={insight.confidence}
              category={insight.category}
            />
          ))}
        </div>
      </div>
    </section>
  );
}
