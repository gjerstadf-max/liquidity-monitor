from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from backend.assessments.funding import assess_funding
from backend.assessments.models import LiquidityAssessment
from backend.commentary.morning_brief import generate_morning_brief


@dataclass(frozen=True)
class DailySnapshot:
    """
    Complete representation of the application's current state.

    Every UI, API endpoint, and report should consume this object
    instead of assembling data independently.
    """

    generated_at: datetime

    assessment: LiquidityAssessment

    morning_brief: object


def build_daily_snapshot() -> DailySnapshot:

    funding = assess_funding()

    assessment = LiquidityAssessment(
        overall_score=funding.score,
        overall_condition=funding.condition,
        confidence=funding.confidence,
        funding=funding,
        summary=funding.summary,
    )

    brief = generate_morning_brief()

    return DailySnapshot(
        generated_at=datetime.now(timezone.utc),
        assessment=assessment,
        morning_brief=brief,
    )