interface StatusPillProps {
  children: string;
  tone?: "neutral" | "good" | "bad" | "warn";
}

export function StatusPill({ children, tone = "neutral" }: StatusPillProps): JSX.Element {
  return <span className={`status-pill tone-${tone}`}>{children}</span>;
}
