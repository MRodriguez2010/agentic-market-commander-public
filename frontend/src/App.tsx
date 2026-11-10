import { useEffect, useState } from "react";
import {
  Activity,
  BadgeDollarSign,
  Bot,
  BrainCircuit,
  Cpu,
  Database,
  FileText,
  Gauge,
  LockKeyhole,
  Network,
  RefreshCw,
  Satellite,
  ShieldAlert,
  SlidersHorizontal,
  TrendingUp,
  Zap
} from "lucide-react";
import { fetchDashboard, saveStrategy } from "./lib/api";
import type { DashboardData, Position, ResearchItem, Strategy } from "./lib/types";
import { ImpactGraph, PriceChart } from "./components/MarketCharts";
import { MetricCard } from "./components/MetricCard";
import { StatusPill } from "./components/StatusPill";
import { Tabs, type TabItem, type ViewId } from "./components/Tabs";

const tabs: TabItem[] = [
  { id: "cockpit", label: "Cockpit", icon: Gauge },
  { id: "strategy", label: "Strategy", icon: SlidersHorizontal },
  { id: "research", label: "Research", icon: FileText },
  { id: "economics", label: "Economics", icon: BadgeDollarSign },
  { id: "audit", label: "Runs", icon: Bot },
  { id: "settings", label: "Settings", icon: Database }
];

const currency = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" });
const compactCurrency = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 2 });

export function App(): JSX.Element {
  const [active, setActive] = useState<ViewId>("cockpit");
  const [data, setData] = useState<DashboardData | null>(null);
  const [strategyDraft, setStrategyDraft] = useState<Strategy | null>(null);
  const [selectedSymbol, setSelectedSymbol] = useState("NVDA");
  const [selectedResearchId, setSelectedResearchId] = useState<string | null>(null);
  const [status, setStatus] = useState("Connecting market feed");
  const [saveResult, setSaveResult] = useState<string[]>([]);

  useEffect(() => {
    let mounted = true;
    fetchDashboard()
      .then((dashboard) => {
        if (!mounted) return;
        setData(dashboard);
        setStrategyDraft(dashboard.strategy);
        setSelectedSymbol(dashboard.portfolio.positions[0]?.symbol ?? "SPY");
        setSelectedResearchId(dashboard.research.items[0]?.id ?? null);
        setStatus("Feed online");
      })
      .catch((error: Error) => {
        if (!mounted) return;
        setStatus(error.message);
      });
    return () => {
      mounted = false;
    };
  }, []);

  async function handleSaveStrategy(): Promise<void> {
    if (!strategyDraft) return;
    const result = await saveStrategy(strategyDraft);
    setSaveResult(result.ok ? ["Policy saved in simulation mode.", ...result.diff.slice(0, 8)] : result.errors);
    if (result.ok && data) {
      setData({ ...data, strategy: strategyDraft });
    }
  }

  if (!data || !strategyDraft) {
    return (
      <main className="loading-shell">
        <Activity aria-hidden="true" />
        <span>{status}</span>
      </main>
    );
  }

  const selectedPosition = data.portfolio.positions.find((position) => position.symbol === selectedSymbol) ?? data.portfolio.positions[0];
  const selectedResearch =
    data.research.items.find((item) => item.id === selectedResearchId) ?? data.research.items[0];

  return (
    <div className="app-shell">
      <header className="command-header">
        <div>
          <span className="eyebrow">Autonomous Market Command / Simulation Safe</span>
          <h1>Agentic Market Commander</h1>
          <div className="feed-row">
            <span><Satellite size={14} aria-hidden="true" /> {status}</span>
            <span><Network size={14} aria-hidden="true" /> {data.market.source}</span>
            <span>{data.market.fetchedAt}</span>
          </div>
        </div>
        <div className="topbar-actions">
          <StatusPill tone="warn">Live trading disabled</StatusPill>
          <button type="button" className="icon-button" onClick={() => window.location.reload()} aria-label="Refresh market feed">
            <RefreshCw size={18} aria-hidden="true" />
          </button>
        </div>
      </header>

      <Tabs tabs={tabs} active={active} onChange={setActive} />

      <main>
        {active === "cockpit" ? (
          <Cockpit
            data={data}
            selectedPosition={selectedPosition}
            selectedResearch={selectedResearch}
            onSelectSymbol={setSelectedSymbol}
            onSelectResearch={setSelectedResearchId}
          />
        ) : null}
        {active === "strategy" ? (
          <StrategyStudio
            strategy={strategyDraft}
            onChange={setStrategyDraft}
            onSave={handleSaveStrategy}
            saveResult={saveResult}
          />
        ) : null}
        {active === "research" ? (
          <ResearchDesk data={data} selectedResearch={selectedResearch} onSelectResearch={setSelectedResearchId} />
        ) : null}
        {active === "economics" ? <EconomicsView data={data} /> : null}
        {active === "audit" ? <AuditView data={data} /> : null}
        {active === "settings" ? <SettingsView data={data} status={status} /> : null}
      </main>
    </div>
  );
}

function Cockpit({
  data,
  selectedPosition,
  selectedResearch,
  onSelectSymbol,
  onSelectResearch
}: {
  data: DashboardData;
  selectedPosition: Position;
  selectedResearch: ResearchItem;
  onSelectSymbol: (symbol: string) => void;
  onSelectResearch: (id: string) => void;
}): JSX.Element {
  const snapshot = data.portfolio.snapshot;
  return (
    <div className="cockpit-grid">
      <section className="market-tape" aria-label="Live market tape">
        {data.market.tickers.map((ticker) => (
          <button key={ticker.symbol} type="button" onClick={() => onSelectSymbol(ticker.symbol)}>
            <span>{ticker.symbol}</span>
            <strong>{compactCurrency.format(ticker.last_price)}</strong>
            <small className={ticker.change_pct >= 0 ? "positive" : "negative"}>
              {ticker.change_pct >= 0 ? "+" : ""}
              {ticker.change_pct}% / {ticker.signal}
            </small>
          </button>
        ))}
      </section>

      <div className="metrics-grid command-metrics">
        <MetricCard label="Net Liquidation" value={currency.format(snapshot.total_value)} detail={snapshot.source} icon={<Gauge size={18} />} />
        <MetricCard label="Equity Exposure" value={currency.format(snapshot.equity_value)} detail={`${data.portfolio.allocation.equityPct}% deployed`} icon={<TrendingUp size={18} />} />
        <MetricCard label="Session P/L" value={currency.format(snapshot.day_pl)} detail="Repriced from latest quote feed" tone={snapshot.day_pl >= 0 ? "good" : "bad"} icon={<Activity size={18} />} />
        <MetricCard label="Policy Gate" value="No-fire" detail="Simulation only" tone="warn" icon={<LockKeyhole size={18} />} />
      </div>

      <section className="terminal-panel primary-chart">
        <div className="panel-heading">
          <div>
            <span className="terminal-label">Selected Instrument</span>
            <h2>{selectedPosition.symbol} / {selectedPosition.name}</h2>
          </div>
          <div className="quote-stack">
            <strong>{currency.format(selectedPosition.last_price)}</strong>
            <span className={selectedPosition.day_change_pct >= 0 ? "positive" : "negative"}>
              {selectedPosition.day_change_pct >= 0 ? "+" : ""}
              {selectedPosition.day_change_pct}% today
            </span>
          </div>
        </div>
        <PriceChart symbol={selectedPosition.symbol} series={selectedPosition.series} />
      </section>

      <section className="terminal-panel positions-panel">
        <div className="panel-heading">
          <div>
            <span className="terminal-label">Position Matrix</span>
            <h2>Holdings</h2>
          </div>
          <StatusPill tone="neutral">{`${data.portfolio.positions.length} live marks`}</StatusPill>
        </div>
        <div className="position-list">
          {data.portfolio.positions.map((position) => (
            <button
              key={position.symbol}
              type="button"
              className={selectedPosition.symbol === position.symbol ? "active" : ""}
              onClick={() => onSelectSymbol(position.symbol)}
            >
              <span>
                <strong>{position.symbol}</strong>
                <small>{position.name}</small>
              </span>
              <span>{currency.format(position.marketValue)}</span>
              <span className={position.dayPl >= 0 ? "positive" : "negative"}>{currency.format(position.dayPl)}</span>
              <span className={position.day_change_pct >= 0 ? "positive" : "negative"}>
                {position.day_change_pct >= 0 ? "+" : ""}
                {position.day_change_pct}%
              </span>
            </button>
          ))}
        </div>
      </section>

      <section className="terminal-panel impact-panel">
        <div className="panel-heading">
          <div>
            <span className="terminal-label">Research Impact Engine</span>
            <h2>{selectedResearch.title}</h2>
          </div>
          <StatusPill tone={selectedResearch.sentiment === "constructive" ? "good" : selectedResearch.sentiment === "negative" ? "bad" : "warn"}>
            {selectedResearch.sentiment}
          </StatusPill>
        </div>
        <ImpactGraph item={selectedResearch} />
        <p className="research-summary">{selectedResearch.summary}</p>
      </section>

      <section className="terminal-panel signal-panel">
        <div className="panel-heading">
          <div>
            <span className="terminal-label">Catalyst Queue</span>
            <h2>News Routed To Trend</h2>
          </div>
          <Cpu size={18} aria-hidden="true" />
        </div>
        <div className="research-tape">
          {data.research.items.slice(0, 5).map((item) => (
            <button key={item.id} type="button" onClick={() => onSelectResearch(item.id)} className={selectedResearch.id === item.id ? "active" : ""}>
              <span>{item.symbols.join(", ")} / {item.catalyst}</span>
              <strong>{item.title}</strong>
              <small>{item.impact.return20d}% 20D / {item.impact.realizedVolatility}% vol</small>
            </button>
          ))}
        </div>
      </section>
    </div>
  );
}

function StrategyStudio({
  strategy,
  onChange,
  onSave,
  saveResult
}: {
  strategy: Strategy;
  onChange: (strategy: Strategy) => void;
  onSave: () => Promise<void>;
  saveResult: string[];
}): JSX.Element {
  function updateRisk(key: keyof Strategy["risk"], value: number | boolean): void {
    onChange({ ...strategy, risk: { ...strategy.risk, [key]: value } });
  }

  function updateAdvanced(key: keyof Strategy["advanced"], value: number | string): void {
    onChange({ ...strategy, advanced: { ...strategy.advanced, [key]: value } });
  }

  return (
    <div className="strategy-layout">
      <section className="terminal-panel">
        <div className="panel-heading">
          <h2>Risk Kernel</h2>
          <ShieldAlert size={19} aria-hidden="true" />
        </div>
        <Control label="Aggressiveness" value={strategy.risk.aggressiveness} onChange={(value) => updateRisk("aggressiveness", value)} />
        <Control label="Max Position %" value={strategy.risk.maxPositionPct} onChange={(value) => updateRisk("maxPositionPct", value)} />
        <Control label="Max Daily Loss %" value={strategy.risk.maxDailyLossPct} max={10} step={0.5} onChange={(value) => updateRisk("maxDailyLossPct", value)} />
        <Control label="Cash Target %" value={strategy.risk.cashTargetPct} onChange={(value) => updateRisk("cashTargetPct", value)} />
        <label className="toggle-row">
          <input type="checkbox" checked={strategy.risk.requireHumanReview} onChange={(event) => updateRisk("requireHumanReview", event.target.checked)} />
          <span>Human review required</span>
        </label>
        <label className="toggle-row disabled">
          <input type="checkbox" checked={strategy.risk.liveTradingEnabled} disabled readOnly />
          <span>Live trading locked</span>
        </label>
      </section>

      <section className="terminal-panel">
        <div className="panel-heading">
          <h2>Alpha Weights</h2>
          <BrainCircuit size={19} aria-hidden="true" />
        </div>
        <Control label="Momentum" value={strategy.advanced.momentumWeight} onChange={(value) => updateAdvanced("momentumWeight", value)} />
        <Control label="Quality" value={strategy.advanced.qualityWeight} onChange={(value) => updateAdvanced("qualityWeight", value)} />
        <Control label="Valuation" value={strategy.advanced.valuationWeight} onChange={(value) => updateAdvanced("valuationWeight", value)} />
        <Control label="Catalyst" value={strategy.advanced.catalystWeight} onChange={(value) => updateAdvanced("catalystWeight", value)} />
        <Control label="Minimum Score" value={strategy.advanced.minimumScore} onChange={(value) => updateAdvanced("minimumScore", value)} />
      </section>

      <section className="terminal-panel raw-policy">
        <div className="panel-heading">
          <h2>Raw Policy</h2>
          <button type="button" className="action-button" onClick={onSave}>
            <Zap size={17} aria-hidden="true" />
            Save
          </button>
        </div>
        <input
          className="policy-name"
          value={strategy.name}
          onChange={(event) => onChange({ ...strategy, name: event.target.value })}
          aria-label="Policy name"
        />
        <textarea
          value={strategy.policyText}
          onChange={(event) => onChange({ ...strategy, policyText: event.target.value })}
          aria-label="Policy text"
        />
        {saveResult.length ? (
          <div className="result-box" aria-live="polite">
            {saveResult.map((line) => (
              <code key={line}>{line}</code>
            ))}
          </div>
        ) : null}
      </section>
    </div>
  );
}

function Control({
  label,
  value,
  max = 100,
  step = 1,
  onChange
}: {
  label: string;
  value: number;
  max?: number;
  step?: number;
  onChange: (value: number) => void;
}): JSX.Element {
  return (
    <label className="control-row">
      <span>{label}</span>
      <input type="range" min={0} max={max} step={step} value={value} onChange={(event) => onChange(Number(event.target.value))} />
      <output>{value}</output>
    </label>
  );
}

function ResearchDesk({
  data,
  selectedResearch,
  onSelectResearch
}: {
  data: DashboardData;
  selectedResearch: ResearchItem;
  onSelectResearch: (id: string) => void;
}): JSX.Element {
  return (
    <div className="research-grid">
      <section className="terminal-panel">
        <div className="panel-heading">
          <h2>Research Impact</h2>
          <StatusPill tone="neutral">{selectedResearch.source}</StatusPill>
        </div>
        <ImpactGraph item={selectedResearch} />
        <p className="research-summary">{selectedResearch.summary}</p>
      </section>
      <section className="terminal-panel">
        <h2>Live Catalyst Feed</h2>
        <div className="research-list">
          {data.research.items.map((item) => (
            <button key={item.id} type="button" onClick={() => onSelectResearch(item.id)} className={selectedResearch.id === item.id ? "active" : ""}>
              <span>{item.symbols.join(", ")} / {item.catalyst}</span>
              <strong>{item.title}</strong>
              <small>{item.publishedAt}</small>
            </button>
          ))}
        </div>
      </section>
    </div>
  );
}

function EconomicsView({ data }: { data: DashboardData }): JSX.Element {
  return (
    <div className="view-grid">
      <div className="metrics-grid">
        <MetricCard label="API Spend" value={currency.format(data.economics.totalCost)} detail="Current sample window" icon={<BadgeDollarSign size={18} />} />
        <MetricCard label="Portfolio Drag" value={`${data.economics.costPctOfPortfolio}%`} detail="Cost / account value" tone="warn" icon={<Activity size={18} />} />
        <MetricCard label="P/L Cost Ratio" value={`${data.economics.costPctOfDayPl}%`} detail={data.economics.verdict} tone={data.economics.isJustified ? "good" : "bad"} icon={<ShieldAlert size={18} />} />
      </div>
      <section className="terminal-panel">
        <h2>Spend By Agent</h2>
        <div className="bar-list">
          {Object.entries(data.economics.byAgent).map(([agent, cost]) => (
            <div key={agent}>
              <span>{agent}</span>
              <div>
                <i style={{ width: `${Math.min((cost / data.economics.totalCost) * 100, 100)}%` }} />
              </div>
              <strong>{currency.format(cost)}</strong>
            </div>
          ))}
        </div>
      </section>
      <section className="terminal-panel">
        <h2>Cost Records</h2>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Agent</th>
                <th>Model</th>
                <th>Run</th>
                <th>Cost</th>
              </tr>
            </thead>
            <tbody>
              {data.economics.records.map((record) => (
                <tr key={record.id}>
                  <td>{record.agent}</td>
                  <td>{record.model}</td>
                  <td>{record.run_type}</td>
                  <td>{currency.format(record.cost_usd)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}

function AuditView({ data }: { data: DashboardData }): JSX.Element {
  return (
    <div className="two-column">
      <section className="terminal-panel">
        <h2>Agent Run Bus</h2>
        <div className="run-log">
          {data.runs.runs.map((run) => (
            <article key={run.id}>
              <div>
                <strong>{run.lane}</strong>
                <small>{run.model} / {run.last_run} → {run.next_run}</small>
              </div>
              <StatusPill tone={run.policy_gate === "pass" ? "good" : run.policy_gate === "hard-block" ? "bad" : "warn"}>{run.status}</StatusPill>
              <p>{run.decision}</p>
            </article>
          ))}
        </div>
      </section>
      <section className="terminal-panel safety-panel">
        <h2>Safety Interlocks</h2>
        {Object.entries(data.runs.safety).map(([key, value]) => (
          <div key={key}>
            <span>{key}</span>
            <strong>{value}</strong>
          </div>
        ))}
      </section>
    </div>
  );
}

function SettingsView({ data, status }: { data: DashboardData; status: string }): JSX.Element {
  return (
    <div className="two-column">
      <section className="terminal-panel settings-panel">
        <h2>Runtime</h2>
        <div>
          <span>Feed</span>
          <strong>{status}</strong>
        </div>
        <div>
          <span>Broker</span>
          <strong>{data.runs.safety.broker}</strong>
        </div>
        <div>
          <span>Market data</span>
          <strong>{data.market.source}</strong>
        </div>
      </section>
      <section className="terminal-panel settings-panel">
        <h2>Model Routing</h2>
        <div>
          <span>Decision</span>
          <strong>{data.strategy.advanced.primaryDecisionModel}</strong>
        </div>
        <div>
          <span>Research</span>
          <strong>{data.strategy.advanced.researchModel}</strong>
        </div>
        <div>
          <span>Heartbeat</span>
          <strong>{data.strategy.advanced.heartbeatModel}</strong>
        </div>
      </section>
    </div>
  );
}
