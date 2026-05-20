export default function InsightCard({
  title,
  summary,
  confidence,
  category,
}: {
  title: string;
  summary: string;
  confidence: 'high' | 'medium' | 'low' | string;
  category: string;
}) {
  return (
    <article className={`card analytics-insight-card analytics-confidence-${confidence}`}>
      <div className="analytics-insight-card-top">
        <span className="analytics-insight-category">{category.replace(/-/g, ' ')}</span>
        <span className="analytics-insight-confidence">{confidence} confidence</span>
      </div>
      <h5 className="analytics-insight-title">{title}</h5>
      <p className="analytics-insight-summary">{summary}</p>
    </article>
  );
}
