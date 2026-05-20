type Item = { key: string; count?: number; score?: number };

export default function LeaderboardCard({ title, items }:{ title: string; items: Item[] }) {
  return (
    <div className="card leaderboard-card">
      <h4>{title}</h4>
      <ol className="leaderboard-list">
        {items.map((it, idx) => (
          <li key={it.key} className="leaderboard-item">
            <span className="rank">{idx+1}</span>
            <span className="name">{it.key}</span>
            <span className="meta">{it.count ?? (it.score != null ? it.score.toFixed(2) : '')}</span>
          </li>
        ))}
      </ol>
    </div>
  );
}
