import React from 'react';
import type {
  IntelligenceSummaryResponse,
  RiskBreakthroughChartPoint,
  DomainMomentumSectionItem,
  LabModelItem,
} from '../types';


// ─── Shared micro-primitives ─────────────────────────────────────────────────

const S = {
  // layout
  col: { display: 'flex', flexDirection: 'column' as const, gap: 8 },
  row: { display: 'flex', flexDirection: 'row' as const, alignItems: 'center' as const, gap: 8 },
  rowWrap: { display: 'flex', flexDirection: 'row' as const, flexWrap: 'wrap' as const, alignItems: 'center' as const, gap: 6 },
  between: { display: 'flex', flexDirection: 'row' as const, alignItems: 'center' as const, justifyContent: 'space-between', gap: 10 },

  // chips
  chip: (bg: string, color: string, border: string): React.CSSProperties => ({
    display: 'inline-flex',
    alignItems: 'center',
    padding: '3px 9px',
    borderRadius: 999,
    fontSize: '0.70rem',
    fontWeight: 600,
    whiteSpace: 'nowrap' as const,
    background: bg,
    color,
    border: `1px solid ${border}`,
    lineHeight: 1.4,
  }),

  rankBadge: (primary = false): React.CSSProperties => ({
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    width: 22,
    height: 22,
    borderRadius: 6,
    fontSize: '0.68rem',
    fontWeight: 800,
    flexShrink: 0,
    background: primary ? 'rgba(6,182,212,0.15)' : 'rgba(255,255,255,0.06)',
    color: primary ? '#06b6d4' : '#64748b',
    border: `1px solid ${primary ? 'rgba(6,182,212,0.25)' : 'rgba(255,255,255,0.08)'}`,
  }),

  entityName: {
    fontSize: '0.88rem',
    fontWeight: 700,
    color: '#f0f0f8',
    flex: 1,
    minWidth: 0,
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    whiteSpace: 'nowrap' as const,
  },

  row_card: {
    padding: '10px 12px',
    borderRadius: 10,
    background: 'rgba(255,255,255,0.03)',
    border: '1px solid rgba(255,255,255,0.07)',
    display: 'flex',
    flexDirection: 'column' as const,
    gap: 8,
  },

  row_card_hero: {
    padding: '12px 14px',
    borderRadius: 10,
    background: 'rgba(6,182,212,0.06)',
    border: '1px solid rgba(6,182,212,0.18)',
    display: 'flex',
    flexDirection: 'column' as const,
    gap: 8,
  },

  barTrack: {
    width: '100%',
    height: 6,
    borderRadius: 999,
    background: 'rgba(255,255,255,0.06)',
    overflow: 'hidden',
  },

  label: {
    fontSize: '0.72rem',
    color: '#64748b',
    whiteSpace: 'nowrap' as const,
  },
};

// Chip presets
const Chip = {
  up: (text: string) => (
    <span style={S.chip('rgba(16,185,129,0.12)', '#34d399', 'rgba(16,185,129,0.22)')}>{text}</span>
  ),
  flat: (text: string) => (
    <span style={S.chip('rgba(148,163,184,0.10)', '#94a3b8', 'rgba(148,163,184,0.18)')}>{text}</span>
  ),
  down: (text: string) => (
    <span style={S.chip('rgba(251,113,133,0.10)', '#fb7185', 'rgba(251,113,133,0.20)')}>{text}</span>
  ),
  cyan: (text: string) => (
    <span style={S.chip('rgba(6,182,212,0.10)', '#06b6d4', 'rgba(6,182,212,0.20)')}>{text}</span>
  ),
  purple: (text: string) => (
    <span style={S.chip('rgba(167,139,250,0.10)', '#a78bfa', 'rgba(167,139,250,0.20)')}>{text}</span>
  ),
  rose: (text: string) => (
    <span style={S.chip('rgba(251,113,133,0.10)', '#fb7185', 'rgba(251,113,133,0.18)')}>{text}</span>
  ),
  green: (text: string) => (
    <span style={S.chip('rgba(16,185,129,0.10)', '#34d399', 'rgba(16,185,129,0.18)')}>{text}</span>
  ),
  amber: (text: string) => (
    <span style={S.chip('rgba(245,158,11,0.10)', '#fbbf24', 'rgba(245,158,11,0.18)')}>{text}</span>
  ),
  muted: (text: string) => (
    <span style={S.chip('rgba(255,255,255,0.05)', '#64748b', 'rgba(255,255,255,0.10)')}>{text}</span>
  ),
};

function directionChip(dir: string, delta: number) {
  const sign = delta > 0 ? '+' : '';
  const val = `${sign}${delta.toFixed(2)}`;
  if (dir === 'up') return Chip.up(`▲ ${val}`);
  if (dir === 'down') return Chip.down(`▼ ${val}`);
  return Chip.flat(`• ${val}`);
}

function signalChip(label: string) {
  const l = label.toLowerCase();
  if (l.includes('high bt') && l.includes('risk')) return Chip.rose(label);
  if (l.includes('high break')) return Chip.cyan(label);
  if (l.includes('risk watch')) return Chip.amber(label);
  if (l.includes('wide')) return Chip.purple(label);
  if (l.includes('strong')) return Chip.green(label);
  if (l.includes('accelerating') || l.includes('surge')) return Chip.green(label);
  if (l.includes('rising')) return Chip.cyan(label);
  return Chip.muted(label);
}

// ─── Dual-line mini chart (Card 1) ──────────────────────────────────────────
function DualLineChart({ points }: { points: RiskBreakthroughChartPoint[] }) {
  const W = 560;
  const H = 110;
  const PAD = 18;

  const active = points.filter(p => p.event_count > 0);
  if (active.length < 2) {
    return (
      <p style={{ fontSize: '0.80rem', color: '#475569', margin: 0, paddingTop: 8 }}>
        Not enough weekly data yet — more events will fill this chart.
      </p>
    );
  }

  const allBt = points.map(p => p.avg_breakthrough);
  const allRk = points.map(p => p.avg_risk);
  const maxVal = Math.max(10, ...allBt, ...allRk);

  function toX(i: number) {
    return PAD + (i / Math.max(1, points.length - 1)) * (W - PAD * 2);
  }
  function toY(v: number) {
    return H - PAD - (v / maxVal) * (H - PAD * 2);
  }
  function makePath(vals: number[]) {
    return vals.map((v, i) => `${i === 0 ? 'M' : 'L'} ${toX(i).toFixed(1)} ${toY(v).toFixed(1)}`).join(' ');
  }

  const btPath = makePath(allBt);
  const rkPath = makePath(allRk);
  const lastActiveIdx = points.reduce((acc, p, i) => (p.event_count > 0 ? i : acc), -1);
  const lastPt = lastActiveIdx >= 0 ? points[lastActiveIdx] : null;

  return (
    <div style={S.col}>
      <svg viewBox={`0 0 ${W} ${H}`} style={{ width: '100%', height: 'auto', display: 'block' }}
        role="img" aria-label="Risk vs breakthrough weekly trend">
        <defs>
          <linearGradient id="btGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="rgba(6,182,212,0.28)" />
            <stop offset="100%" stopColor="rgba(6,182,212,0)" />
          </linearGradient>
          <linearGradient id="rkGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="rgba(251,113,133,0.22)" />
            <stop offset="100%" stopColor="rgba(251,113,133,0)" />
          </linearGradient>
        </defs>
        {[0.33, 0.66].map(f => (
          <line key={f} x1={PAD} y1={PAD + f * (H - PAD * 2)} x2={W - PAD} y2={PAD + f * (H - PAD * 2)}
            stroke="rgba(255,255,255,0.05)" strokeWidth="1" />
        ))}
        <path d={`${btPath} L ${toX(points.length - 1).toFixed(1)} ${H - PAD} L ${toX(0).toFixed(1)} ${H - PAD} Z`} fill="url(#btGrad)" />
        <path d={`${rkPath} L ${toX(points.length - 1).toFixed(1)} ${H - PAD} L ${toX(0).toFixed(1)} ${H - PAD} Z`} fill="url(#rkGrad)" />
        <path d={btPath} fill="none" stroke="#06b6d4" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
        <path d={rkPath} fill="none" stroke="#fb7185" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
        {lastPt && (
          <>
            <circle cx={toX(lastActiveIdx)} cy={toY(lastPt.avg_breakthrough)} r="3.5" fill="#06b6d4" stroke="#070810" strokeWidth="2" />
            <circle cx={toX(lastActiveIdx)} cy={toY(lastPt.avg_risk)} r="3.5" fill="#fb7185" stroke="#070810" strokeWidth="2" />
          </>
        )}
      </svg>

      <div style={{ ...S.row, fontSize: '0.73rem' }}>
        <span style={{ color: '#06b6d4', fontWeight: 600 }}>● Breakthrough</span>
        <span style={{ color: '#fb7185', fontWeight: 600 }}>● Risk</span>
        {lastPt && (
          <span style={{ marginLeft: 'auto', color: '#64748b' }}>
            Latest — BT {lastPt.avg_breakthrough.toFixed(1)} · Risk {lastPt.avg_risk.toFixed(1)}
          </span>
        )}
      </div>
    </div>
  );
}

// ─── Card 2: Fastest-Rising AI Domain ───────────────────────────────────────
function DomainRow({ item, rank }: { item: DomainMomentumSectionItem; rank: number }) {
  const isHero = rank === 1;

  return (
    <div style={isHero ? S.row_card_hero : S.row_card}>
      {/* Top line: rank | name | signal chip | delta chip | event count chip */}
      <div style={S.rowWrap}>
        <span style={S.rankBadge(isHero)}>#{rank}</span>
        <span style={{ ...S.entityName, flex: 'none', maxWidth: '40%' }}>{item.name}</span>
        {signalChip(item.signal_label)}
        {directionChip(item.direction, item.delta)}
        {Chip.muted(`${item.recent_count} event${item.recent_count !== 1 ? 's' : ''}`)}
      </div>
    </div>
  );
}

function DomainRisingCard({ topDomain, runnersUp }: {
  topDomain: DomainMomentumSectionItem | null;
  runnersUp: DomainMomentumSectionItem[];
}) {
  if (!topDomain) {
    return <p style={{ fontSize: '0.80rem', color: '#475569', margin: 0 }}>No domain activity ingested in the last 30 days yet.</p>;
  }

  const all = [topDomain, ...runnersUp].slice(0, 3);

  return (
    <div style={S.col}>
      {all.map((d, i) => (
        <DomainRow key={d.slug} item={d} rank={i + 1} />
      ))}
    </div>
  );
}

// ─── Card 3: Breakthrough Leaders: Labs & Models ─────────────────────────────
function LeaderRow({ item, rank, maxBt }: { item: LabModelItem; rank: number; maxBt: number }) {
  const isHero = rank === 1;

  return (
    <div style={isHero ? S.row_card_hero : S.row_card}>
      {/* Row 1: rank | name | type pill | signal badge */}
      <div style={S.rowWrap}>
        <span style={S.rankBadge(isHero)}>#{rank}</span>
        <span style={{ ...S.entityName, flex: 'none', maxWidth: '35%' }}>{item.name}</span>
        {item.type === 'lab'
          ? Chip.cyan('🏢 Lab')
          : Chip.purple('🤖 Model')}
        {signalChip(item.signal_label)}
      </div>

      {/* BT bar */}
      <div style={S.barTrack}>
        <div style={{
          height: '100%',
          borderRadius: 999,
          width: `${(item.avg_breakthrough / maxBt) * 100}%`,
          background: 'linear-gradient(90deg, #06b6d4, rgba(6,182,212,0.35))',
          transition: 'width 0.3s ease',
        }} />
      </div>

      {/* Row 2: metric chips */}
      <div style={S.rowWrap}>
        {Chip.purple(`${item.mention_count} mention${item.mention_count !== 1 ? 's' : ''}`)}
        {Chip.cyan(`BT ${item.avg_breakthrough.toFixed(1)}`)}
        {Chip.rose(`Risk ${item.avg_risk.toFixed(1)}`)}
      </div>
    </div>
  );
}

function LeadersCard({ items }: { items: LabModelItem[] }) {
  if (items.length === 0) {
    return <p style={{ fontSize: '0.80rem', color: '#475569', margin: 0 }}>No organisation signals detected yet.</p>;
  }

  const maxBt = Math.max(1, ...items.map(i => i.avg_breakthrough));

  return (
    <div style={S.col}>
      {items.map((item, idx) => (
        <LeaderRow key={`${item.type}-${item.name}`} item={item} rank={idx + 1} maxBt={maxBt} />
      ))}
    </div>
  );
}

// ─── Card shell ──────────────────────────────────────────────────────────────
function IntelCard({ icon, title, summary, children }: {
  icon: string;
  title: string;
  summary: string;
  children: React.ReactNode;
}) {
  return (
    <article className="card intel-card">
      {/* Category label row */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <span style={{ fontSize: '1.2rem', lineHeight: 1, flexShrink: 0 }}>{icon}</span>
        <span style={{
          fontSize: '0.72rem', fontWeight: 700, textTransform: 'uppercase',
          letterSpacing: '0.10em', color: '#475569',
        }}>
          {title}
        </span>
      </div>

      {/* Insight callout — the key intelligence sentence */}
      <div style={{
        padding: '10px 14px',
        borderLeft: '3px solid rgba(251,191,36,0.55)',
        borderRadius: '0 8px 8px 0',
        background: 'rgba(251,191,36,0.05)',
      }}>
        <span style={{
          display: 'block',
          fontSize: '0.62rem', fontWeight: 800, textTransform: 'uppercase',
          letterSpacing: '0.12em', color: 'rgba(251,191,36,0.7)',
          marginBottom: 5,
        }}>
          ◎ Signal
        </span>
        <p style={{
          fontSize: '0.85rem', lineHeight: 1.6,
          color: '#c8cde0', margin: 0, fontWeight: 500,
        }}>
          {summary}
        </p>
      </div>

      {/* Divider */}
      <div style={{ height: 1, background: 'rgba(255,255,255,0.07)' }} />

      {/* Body */}
      {children}
    </article>
  );
}


// ─── Main component ──────────────────────────────────────────────────────────
type Props = { data: IntelligenceSummaryResponse };

export default function IntelligenceSummary({ data }: Props) {
  const { risk_breakthrough, domain_momentum, lab_model_movement } = data;

  return (
    <section className="intel-shell" aria-label="AI Intelligence Summary">
      <div style={{ ...S.col, gap: 3, marginBottom: 4 }}>
        <span style={{
          fontSize: '0.63rem', fontWeight: 800, textTransform: 'uppercase',
          letterSpacing: '0.16em', color: '#06b6d4',
        }}>
          Backend Intelligence · 3 Live Signals
        </span>
        <h3 style={{
          fontSize: '1.35rem', fontWeight: 700, margin: 0,
          background: 'linear-gradient(135deg,#e2e8f0 0%,#94a3b8 100%)',
          WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
        }}>
          AI Intelligence Signals
        </h3>
        <p style={{ fontSize: '0.78rem', color: '#4a4d6a', margin: 0 }}>
          Backend-computed insights from the latest AI articles in the database.
        </p>
      </div>

      <div className="intel-grid">
        <IntelCard icon="⚡" title={risk_breakthrough.title} summary={risk_breakthrough.summary}>
          <DualLineChart points={risk_breakthrough.chart_points} />
        </IntelCard>

        <IntelCard icon="📡" title={domain_momentum.title} summary={domain_momentum.summary}>
          <DomainRisingCard
            topDomain={domain_momentum.top_domain}
            runnersUp={domain_momentum.runners_up}
          />
        </IntelCard>

        <IntelCard icon="🏆" title={lab_model_movement.title} summary={lab_model_movement.summary}>
          <LeadersCard items={lab_model_movement.items} />
        </IntelCard>
      </div>
    </section>
  );
}
