import type { MarketPoint, ResearchItem } from "../lib/types";

interface PriceChartProps {
  symbol: string;
  series: MarketPoint[];
}

export function PriceChart({ symbol, series }: PriceChartProps): JSX.Element {
  const points = series.slice(-96);
  if (points.length < 2) {
    return <div className="chart-empty">No chart data</div>;
  }
  const closes = points.map((point) => point.close);
  const volumes = points.map((point) => point.volume);
  const min = Math.min(...closes);
  const max = Math.max(...closes);
  const maxVolume = Math.max(...volumes, 1);
  const line = pointsToPath(closes, min, max, 760, 230);
  const area = `${line} L 760 230 L 0 230 Z`;
  const latest = closes[closes.length - 1];
  const first = closes[0];
  const isUp = latest >= first;
  const gradientId = `price-${symbol.replace(/\W/g, "")}`;

  return (
    <div className="chart-shell">
      <div className="chart-header">
        <div>
          <span className="terminal-label">Primary Tape</span>
          <strong>{symbol}</strong>
        </div>
        <div className={isUp ? "positive" : "negative"}>
          {isUp ? "+" : ""}
          {(((latest - first) / first) * 100).toFixed(2)}%
        </div>
      </div>
      <svg className="price-chart" viewBox="0 0 760 300" role="img" aria-label={`${symbol} price chart`}>
        <defs>
          <linearGradient id={gradientId} x1="0" x2="0" y1="0" y2="1">
            <stop offset="0%" stopColor={isUp ? "#34d399" : "#ff6b6b"} stopOpacity="0.45" />
            <stop offset="100%" stopColor={isUp ? "#34d399" : "#ff6b6b"} stopOpacity="0.02" />
          </linearGradient>
        </defs>
        {[0, 1, 2, 3].map((lineIndex) => (
          <line key={lineIndex} x1="0" x2="760" y1={lineIndex * 58 + 18} y2={lineIndex * 58 + 18} className="grid-line" />
        ))}
        {points.map((point, index) => {
          const x = (index / Math.max(points.length - 1, 1)) * 760;
          const height = Math.max((point.volume / maxVolume) * 48, 2);
          return <rect key={`${point.date}-${point.volume}`} x={x - 2} y={286 - height} width="3" height={height} className="volume-bar" />;
        })}
        <path d={area} fill={`url(#${gradientId})`} />
        <path d={line} className={isUp ? "chart-line positive-stroke" : "chart-line negative-stroke"} />
        <circle cx="760" cy={scaleY(latest, min, max, 230)} r="4" className={isUp ? "last-dot positive-fill" : "last-dot negative-fill"} />
      </svg>
    </div>
  );
}

interface ImpactGraphProps {
  item: ResearchItem;
}

export function ImpactGraph({ item }: ImpactGraphProps): JSX.Element {
  const history = item.impact.history.slice(-58);
  const projection = item.impact.projection;
  if (!history.length || !projection.length) {
    return <div className="chart-empty">No impact model</div>;
  }
  const historical = history.map((point) => point.close);
  const projectedValues = projection.flatMap((point) => [point.bull, point.baseline, point.bear]);
  const min = Math.min(...historical, ...projectedValues);
  const max = Math.max(...historical, ...projectedValues);
  const historyPath = pointsToPath(historical, min, max, 520, 190);
  const projectionBase = projectionToPath(projection.map((point) => point.baseline), min, max, 220, 190, 520);
  const projectionBull = projectionToPath(projection.map((point) => point.bull), min, max, 220, 190, 520);
  const projectionBear = projectionToPath(projection.map((point) => point.bear), min, max, 220, 190, 520);
  const band = projectionBandPath(
    projection.map((point) => point.bull),
    projection.map((point) => point.bear),
    min,
    max,
    220,
    190,
    520
  );

  return (
    <div className="impact-shell">
      <div className="impact-header">
        <div>
          <span className="terminal-label">{item.symbols[0]} Catalyst Model</span>
          <strong>{item.catalyst}</strong>
        </div>
        <div className="impact-stats">
          <span>{item.impact.trendScore.toFixed(1)} trend</span>
          <span>{item.impact.shockPct > 0 ? "+" : ""}{item.impact.shockPct}% shock</span>
        </div>
      </div>
      <svg className="impact-chart" viewBox="0 0 760 250" role="img" aria-label={`${item.title} impact graph`}>
        {[0, 1, 2].map((index) => (
          <line key={index} x1="0" x2="760" y1={index * 70 + 26} y2={index * 70 + 26} className="grid-line" />
        ))}
        <line x1="520" x2="520" y1="10" y2="212" className="event-line" />
        <text x="532" y="28" className="event-label">news</text>
        <path d={historyPath} className="chart-line cyan-stroke" />
        <path d={band} className="scenario-band" />
        <path d={projectionBull} className="chart-line positive-stroke ghost" />
        <path d={projectionBase} className="chart-line amber-stroke" />
        <path d={projectionBear} className="chart-line negative-stroke ghost" />
      </svg>
    </div>
  );
}

function pointsToPath(values: number[], min: number, max: number, width: number, height: number): string {
  return values
    .map((value, index) => {
      const x = (index / Math.max(values.length - 1, 1)) * width;
      const y = scaleY(value, min, max, height);
      return `${index === 0 ? "M" : "L"} ${x.toFixed(2)} ${y.toFixed(2)}`;
    })
    .join(" ");
}

function projectionToPath(values: number[], min: number, max: number, width: number, height: number, offsetX: number): string {
  return values
    .map((value, index) => {
      const x = offsetX + (index / Math.max(values.length - 1, 1)) * width;
      const y = scaleY(value, min, max, height);
      return `${index === 0 ? "M" : "L"} ${x.toFixed(2)} ${y.toFixed(2)}`;
    })
    .join(" ");
}

function projectionBandPath(
  upper: number[],
  lower: number[],
  min: number,
  max: number,
  width: number,
  height: number,
  offsetX: number
): string {
  const upperPoints = upper.map((value, index) => {
    const x = offsetX + (index / Math.max(upper.length - 1, 1)) * width;
    const y = scaleY(value, min, max, height);
    return `${x.toFixed(2)} ${y.toFixed(2)}`;
  });
  const lowerPoints = lower
    .map((value, index) => {
      const x = offsetX + (index / Math.max(lower.length - 1, 1)) * width;
      const y = scaleY(value, min, max, height);
      return `${x.toFixed(2)} ${y.toFixed(2)}`;
    })
    .reverse();
  return `M ${upperPoints.join(" L ")} L ${lowerPoints.join(" L ")} Z`;
}

function scaleY(value: number, min: number, max: number, height: number): number {
  const spread = Math.max(max - min, 0.01);
  return 10 + (1 - (value - min) / spread) * height;
}
