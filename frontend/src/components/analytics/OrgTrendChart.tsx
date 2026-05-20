export default function OrgTrendChart({ points, width=220, height=48 }:{ points:{ date:string; count:number }[]; width?:number; height?:number }){
  if (!points || points.length===0) return <div className="sparkline empty" />;
  const max = Math.max(...points.map(p=>p.count));
  const min = Math.min(...points.map(p=>p.count));
  const w = width; const h = height;
  const path = points.map((p,i)=>{
    const x = (i / Math.max(1, points.length-1)) * w;
    const y = h - ((p.count - min) / Math.max(1, max - min || 1)) * h;
    return `${i===0?'M':'L'} ${x.toFixed(1)} ${y.toFixed(1)}`;
  }).join(' ');
  return (
    <svg className="org-trend" width={w} height={h} viewBox={`0 0 ${w} ${h}`}>
      <path d={path} fill="none" stroke="var(--muted)" strokeWidth={2} />
    </svg>
  );
}
