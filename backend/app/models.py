from __future__ import annotations

from pydantic import BaseModel, Field


class RiskControls(BaseModel):
    aggressiveness: int = Field(ge=0, le=100)
    maxPositionPct: float = Field(gt=0, le=100)
    maxDailyLossPct: float = Field(gt=0, le=20)
    cashTargetPct: float = Field(ge=0, le=100)
    allowOptions: bool
    requireHumanReview: bool
    liveTradingEnabled: bool


class AdvancedStrategy(BaseModel):
    momentumWeight: int = Field(ge=0, le=100)
    qualityWeight: int = Field(ge=0, le=100)
    valuationWeight: int = Field(ge=0, le=100)
    catalystWeight: int = Field(ge=0, le=100)
    minimumScore: int = Field(ge=0, le=100)
    researchCadenceMinutes: int = Field(ge=5, le=240)
    rebalanceCadence: str
    primaryDecisionModel: str
    researchModel: str
    heartbeatModel: str


class StrategyUpdate(BaseModel):
    name: str = Field(min_length=3, max_length=80)
    policyText: str = Field(min_length=100, max_length=6000)
    risk: RiskControls
    advanced: AdvancedStrategy


class SimulationRequest(BaseModel):
    symbol: str = Field(min_length=1, max_length=8)
    action: str = Field(pattern="^(buy|sell|hold)$")
    notionalUsd: float = Field(ge=0, le=10_000)
