from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from backend.assessments.funding import assess_funding
from backend.assessments.models import LiquidityAssessment
from backend.commentary.morning_brief import (
    MorningBrief,
    generate_morning_brief,
)
from backend.metrics.funding import (
    FundingSnapshot,
    latest_funding_snapshot,
)


@dataclass(frozen=True)
class DailySnapshot:
    generated_at: datetime
    assessment: LiquidityAssessment
    funding: FundingSnapshot
    morning_brief: MorningBrief


def build_daily_snapshot() -> DailySnapshot:
    funding_metrics = latest_funding_snapshot()
    funding_assessment = assess_funding()

    assessment = LiquidityAssessment(
        overall_score=funding_assessment.score,
        overall_condition=funding_assessment.condition,
        confidence=funding_assessment.confidence,
        funding=funding_assessment,
        summary=funding_assessment.summary,
    )

    morning_brief = generate_morning_brief()

    return DailySnapshot(
        generated_at=datetime.now(timezone.utc),
        assessment=assessment,
        funding=funding_metrics,
        morning_brief=morning_brief,
    )