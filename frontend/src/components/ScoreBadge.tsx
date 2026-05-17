interface Props {
  type: 'breakthrough' | 'risk' | 'evidence' | 'momentum';
  value: number | string;
}

function riskClass(v: number) { return v <= 3 ? 'risk-low' : v <= 6 ? 'risk-mid' : 'risk-high'; }

export default function ScoreBadge({ type, value }: Props) {
  const n = Number(value);
  if (type === 'breakthrough') return <span className="score-badge breakthrough" title="How much this event advances general AI capabilities or solves a previously unsolvable problem.">⚡ {n.toFixed(1)}/10</span>;
  if (type === 'risk')         return <span className={`score-badge ${riskClass(n)}`} title="How much this event poses a danger to users, corporations, or society.">⚠️ Risk {n.toFixed(1)}</span>;
  if (type === 'evidence')     return <span className="score-badge evidence" title="How reliable the information is (e.g., rumor vs. peer-reviewed).">📄 {String(value).replace(/-/g,' ')}</span>;
  if (type === 'momentum')     return <span className={`score-badge ${n >= 0 ? 'momentum-up' : 'momentum-dn'}`} title="Whether this topic is gaining traction or cooling down.">{n >= 0 ? '↑' : '↓'} {n >= 0 ? '+' : ''}{n.toFixed(2)}</span>;
  return null;
}
