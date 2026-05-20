import type { ReactNode } from 'react';

type KPICardProps = {
  title: string;
  value: string | number;
  delta?: number | null;
  children?: ReactNode;
};

export default function KPICard({ title, value, delta, children }: KPICardProps) {
  const deltaClass = delta == null ? '' : delta >= 0 ? 'kpi-up' : 'kpi-down';
  return (
    <div className="kpi-card card">
      <div className="kpi-top">
        <div className="kpi-title">{title}</div>
        <div className="kpi-icon">{children}</div>
      </div>
      <div className="kpi-value">{value}</div>
      {delta != null && (
        <div className={`kpi-delta ${deltaClass}`}>{delta >= 0 ? `+${(delta * 100).toFixed(0)}%` : `${(delta * 100).toFixed(0)}%`}</div>
      )}
    </div>
  );
}
