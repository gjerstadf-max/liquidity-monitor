from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Assessment:
    category: str
    verdict: str
    confidence: str
    summary: str


@dataclass(frozen=True)
class LiquidityAssessment:
    overall_verdict: str
    confidence: str

    funding: Assessment
    system_liquidity: Assessment
    repo_market: Assessment

    summary: str