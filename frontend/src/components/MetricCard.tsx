import type { ReactNode } from "react";

interface MetricCardProps {
  label: string;
  value: string;
  detail?: string;
  tone?: "neutral" | "good" | "bad" | "warn";
  icon?: ReactNode;
}

export function MetricCard({ label, value, detail, tone = "neutral", icon }: MetricCardProps): JSX.Element {
  return (
    <section className={`metric-card tone-${tone}`} aria-label={label}>
      <div className="metric-label">
        {icon}
        <span>{label}</span>
      </div>
      <strong>{value}</strong>
      {detail ? <small>{detail}</small> : null}
    </section>
  );
}
