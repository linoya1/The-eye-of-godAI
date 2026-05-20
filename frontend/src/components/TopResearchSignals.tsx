import React from 'react';
import { RESEARCH_SIGNALS, type ResearchSignal } from '../data/researchSignals';


// ─── Chip colour logic ───────────────────────────────────────────────────────
function chipStyle(label: string): React.CSSProperties {
  const l = label.toLowerCase();
  if (l.startsWith('evidence:')) {
    return { background: 'rgba(6,182,212,0.10)', color: '#06b6d4', border: '1px solid rgba(6,182,212,0.22)' };
  }
  if (l.startsWith('breakthrough:')) {
    return { background: 'rgba(139,92,246,0.12)', color: '#a78bfa', border: '1px solid rgba(139,92,246,0.25)' };
  }
  if (l.startsWith('risk:')) {
    const sub = l.replace('risk:', '').trim();
    if (sub.includes('high')) {
      return { background: 'rgba(244,63,94,0.10)', color: '#fb7185', border: '1px solid rgba(244,63,94,0.22)' };
    }
    return { background: 'rgba(245,158,11,0.10)', color: '#fbbf24', border: '1px solid rgba(245,158,11,0.22)' };
  }
  // plain tag
  return { background: 'rgba(255,255,255,0.05)', color: '#8b8fad', border: '1px solid rgba(255,255,255,0.10)' };
}

const baseChip: React.CSSProperties = {
  display: 'inline-flex',
  alignItems: 'center',
  padding: '3px 9px',
  borderRadius: 999,
  fontSize: '0.68rem',
  fontWeight: 600,
  whiteSpace: 'nowrap',
  lineHeight: 1.4,
};

// ─── Scroll + highlight helper ───────────────────────────────────────────────
function scrollToEvent(eventId: string) {
  const el = document.getElementById(`event-${eventId}`);
  if (!el) return;
  el.scrollIntoView({ behavior: 'smooth', block: 'center' });
  // pulse highlight for 1.6 s
  el.classList.add('event-card--highlight');
  setTimeout(() => el.classList.remove('event-card--highlight'), 1600);
}

// ─── Single signal card ──────────────────────────────────────────────────────
function SignalCard({ signal, available }: { signal: ResearchSignal; available: boolean }) {
  return (
    <article style={{
      display: 'flex',
      flexDirection: 'column',
      gap: 14,
      padding: '20px 22px',
      borderRadius: 14,
      background: 'linear-gradient(160deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.02) 100%)',
      border: '1px solid rgba(255,255,255,0.07)',
      transition: 'border-color 0.2s, box-shadow 0.2s',
    }}>
      {/* Category label */}
      <span style={{
        fontSize: '0.63rem',
        fontWeight: 800,
        textTransform: 'uppercase',
        letterSpacing: '0.12em',
        color: '#475569',
      }}>
        {signal.category}
      </span>

      {/* Title */}
      <h4 style={{
        margin: 0,
        fontSize: '0.97rem',
        fontWeight: 700,
        color: '#e2e8f0',
        lineHeight: 1.35,
      }}>
        {signal.displayTitle}
      </h4>

      {/* Curated takeaway — amber callout matching analytics cards */}
      <div style={{
        padding: '10px 14px',
        borderLeft: '3px solid rgba(251,191,36,0.50)',
        borderRadius: '0 8px 8px 0',
        background: 'rgba(251,191,36,0.04)',
      }}>
        <span style={{
          display: 'block',
          fontSize: '0.60rem',
          fontWeight: 800,
          textTransform: 'uppercase',
          letterSpacing: '0.12em',
          color: 'rgba(251,191,36,0.65)',
          marginBottom: 6,
        }}>
          ◎ Research Signal
        </span>
        <p style={{
          margin: 0,
          fontSize: '0.82rem',
          lineHeight: 1.65,
          color: '#b0b8d0',
          fontWeight: 400,
        }}>
          {signal.takeaway}
        </p>
      </div>

      {/* Chip row */}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
        {signal.chips.map(chip => (
          <span key={chip} style={{ ...baseChip, ...chipStyle(chip) }}>
            {chip}
          </span>
        ))}
      </div>

      {/* View Event button */}
      <div style={{ marginTop: 'auto', paddingTop: 2 }}>
        {available ? (
          <button
            onClick={() => scrollToEvent(signal.eventId)}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 6,
              padding: '7px 16px',
              borderRadius: 8,
              fontSize: '0.78rem',
              fontWeight: 600,
              cursor: 'pointer',
              border: '1px solid rgba(6,182,212,0.35)',
              background: 'rgba(6,182,212,0.08)',
              color: '#06b6d4',
              transition: 'background 0.15s, border-color 0.15s',
              fontFamily: 'inherit',
            }}
            onMouseEnter={e => {
              (e.currentTarget as HTMLButtonElement).style.background = 'rgba(6,182,212,0.16)';
              (e.currentTarget as HTMLButtonElement).style.borderColor = 'rgba(6,182,212,0.55)';
            }}
            onMouseLeave={e => {
              (e.currentTarget as HTMLButtonElement).style.background = 'rgba(6,182,212,0.08)';
              (e.currentTarget as HTMLButtonElement).style.borderColor = 'rgba(6,182,212,0.35)';
            }}
          >
            View Event ↓
          </button>
        ) : (
          <span style={{
            fontSize: '0.73rem',
            color: '#475569',
            fontStyle: 'italic',
          }}>
            Event not currently visible
          </span>
        )}
      </div>
    </article>
  );
}

// ─── Section ─────────────────────────────────────────────────────────────────
interface Props {
  /** IDs of events currently rendered in the All Events feed */
  visibleEventIds: string[];
}

export default function TopResearchSignals({ visibleEventIds }: Props) {
  const visibleSet = new Set(visibleEventIds);

  return (
    <section style={{ marginBottom: 32 }} aria-label="Top Research Signals">
      {/* Section header */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 3, marginBottom: 16 }}>
        <span style={{
          fontSize: '0.63rem',
          fontWeight: 800,
          textTransform: 'uppercase',
          letterSpacing: '0.16em',
          color: '#8b5cf6',
        }}>
          Curated Intelligence · 3 Research Signals
        </span>
        <h3 style={{
          margin: 0,
          fontSize: '1.25rem',
          fontWeight: 700,
          background: 'linear-gradient(135deg, #e2e8f0 0%, #94a3b8 100%)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
        }}>
          Top Research Signals
        </h3>
        <p style={{ margin: 0, fontSize: '0.78rem', color: '#4a4d6a' }}>
          Hand-curated takeaways from key events in the database. Click "View Event" to jump to the full article below.
        </p>
      </div>

      {/* 3-column grid (collapses to 1 on mobile via CSS) */}
      <div className="research-signals-grid">
        {RESEARCH_SIGNALS.map(signal => (
          <SignalCard
            key={signal.eventId}
            signal={signal}
            available={visibleSet.has(signal.eventId)}
          />
        ))}
      </div>
    </section>
  );
}
