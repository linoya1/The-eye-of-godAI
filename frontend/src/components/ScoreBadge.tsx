interface Props {
  type: 'breakthrough' | 'risk' | 'evidence' | 'momentum';
  value: number | string;
}

function riskClass(v: number) { return v <= 3 ? 'risk-low' : v <= 6 ? 'risk-mid' : 'risk-high'; }

export default function ScoreBadge({ type, value }: Props) {
  const n = Number(value);
  if (type === 'breakthrough') return <span className="score-badge breakthrough">⚡ {n.toFixed(1)}/10</span>;
  if (type === 'risk')         return <span className={`score-badge ${riskClass(n)}`}>⚠️ Risk {n.toFixed(1)}</span>;
  if (type === 'evidence')     return <span className="score-badge evidence">📄 {String(value).replace(/-/g,' ')}</span>;
  if (type === 'momentum')     return <span className={`score-badge ${n >= 0 ? 'momentum-up' : 'momentum-dn'}`}>{n >= 0 ? '↑' : '↓'} {n >= 0 ? '+' : ''}{n.toFixed(2)}</span>;
  return null;
}
