export interface PortfolioSnapshot {
  total_value: number;
  buying_power: number;
  cash: number;
  equity_value: number;
  day_pl: number;
  unrealized_pl: number;
  updated_at: string;
  source: string;
}

export interface MarketPoint {
  date: string;
  close: number;
  high: number;
  low: number;
  volume: number;
}

export interface Position {
  symbol: string;
  name: string;
  quantity: number;
  average_cost: number;
  last_price: number;
  day_change_pct: number;
  thesis: string;
  risk: string;
  marketValue: number;
  dayPl: number;
  unrealizedPl: number;
  previous_close: number;
  volume: number;
  fiftyTwoWeekHigh: number;
  fiftyTwoWeekLow: number;
  series: MarketPoint[];
}

export interface Portfolio {
  snapshot: PortfolioSnapshot;
  positions: Position[];
  allocation: {
    cashPct: number;
    equityPct: number;
    costBasis: number;
    marketValue: number;
  };
}

export interface Ticker {
  symbol: string;
  name: string;
  last_price: number;
  previous_close: number;
  change_pct: number;
  day_high: number;
  day_low: number;
  volume: number;
  fifty_two_week_high: number;
  fifty_two_week_low: number;
  market_time: string;
  signal: string;
  series: MarketPoint[];
}

export interface Market {
  status: string;
  sessionDate: string;
  source: string;
  fetchedAt: string;
  tickers: Ticker[];
  breadth: Array<{ label: string; value: number }>;
  sparkline: number[];
}

export interface RiskControls {
  aggressiveness: number;
  maxPositionPct: number;
  maxDailyLossPct: number;
  cashTargetPct: number;
  allowOptions: boolean;
  requireHumanReview: boolean;
  liveTradingEnabled: boolean;
}

export interface AdvancedStrategy {
  momentumWeight: number;
  qualityWeight: number;
  valuationWeight: number;
  catalystWeight: number;
  minimumScore: number;
  researchCadenceMinutes: number;
  rebalanceCadence: string;
  primaryDecisionModel: string;
  researchModel: string;
  heartbeatModel: string;
}

export interface Strategy {
  id: number;
  name: string;
  policyText: string;
  risk: RiskControls;
  advanced: AdvancedStrategy;
  createdAt: string;
  liveTradingAvailable: boolean;
}

export interface ResearchItem {
  id: string;
  title: string;
  source: string;
  url: string;
  catalyst: string;
  symbols: string[];
  sentiment: string;
  summary: string;
  publishedAt: string;
  impact: {
    symbol: string;
    latest: number;
    return20d: number;
    return60d: number;
    realizedVolatility: number;
    trendScore: number;
    shockPct: number;
    history: MarketPoint[];
    projection: Array<{
      step: number;
      baseline: number;
      bull: number;
      bear: number;
    }>;
  };
}

export interface Research {
  items: ResearchItem[];
  watchlist: string[];
}

export interface Economics {
  totalCost: number;
  costPctOfPortfolio: number;
  costPctOfDayPl: number;
  isJustified: boolean;
  verdict: string;
  byAgent: Record<string, number>;
  records: Array<{
    id: number;
    agent: string;
    model: string;
    run_type: string;
    cost_usd: number;
    created_at: string;
  }>;
}

export interface AgentRun {
  id: string;
  lane: string;
  model: string;
  status: string;
  last_run: string;
  next_run: string;
  cost_usd: number;
  decision: string;
  policy_gate: string;
}

export interface Runs {
  runs: AgentRun[];
  safety: {
    liveTrading: string;
    orderEndpoints: string;
    killSwitch: string;
    broker: string;
  };
}

export interface DashboardData {
  portfolio: Portfolio;
  market: Market;
  strategy: Strategy;
  research: Research;
  economics: Economics;
  runs: Runs;
}

export interface SaveStrategyResponse {
  ok: boolean;
  errors: string[];
  diff: string[];
  strategy: Strategy;
}
