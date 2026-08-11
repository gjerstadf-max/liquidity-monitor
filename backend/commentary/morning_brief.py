from __future__ import annotations

from dataclasses import dataclass

from backend.assessments.funding import assess_funding
from backend.assessments.models import LiquidityAssessment


@dataclass(frozen=True)
class MorningBrief:
    headline: str
    summary: str
    what_matters: str
    what_to_watch: str


def build_liquidity_assessment() -> LiquidityAssessment:
    funding = assess_funding()

    return LiquidityAssessment(
        overall_score=funding.score,
        overall_condition=funding.condition,
        confidence=funding.confidence,
        funding=funding,
        summary=funding.summary,
    )


def generate_morning_brief() -> MorningBrief:
    assessment = build_liquidity_assessment()
    funding = assessment.funding

    headline = (
        f"Liquidity conditions are {assessment.overall_condition.lower()} "
        f"with a score of {assessment.overall_score}/100."
    )

    if funding.score >= 90:
        summary = (
            "Overnight funding conditions remain orderly. "
            f"{funding.summary} "
            "Current funding-market evidence does not indicate "
            "meaningful stress."
        )

        what_matters = (
            "SOFR and EFFR remain closely aligned, suggesting no "
            "material divergence between secured and unsecured "
            "overnight funding conditions."
        )

        what_to_watch = (
            "Continue monitoring the SOFR-EFFR spread for persistent "
            "widening or a change in direction."
        )

    elif funding.score >= 70:
        summary = (
            "Overnight funding conditions remain broadly functional, "
            "but the current spread warrants monitoring. "
            f"{funding.summary}"
        )

        what_matters = (
            "The relationship between secured and unsecured overnight "
            "funding rates has moved away from its healthiest range."
        )

        what_to_watch = (
            "Watch whether the spread persists, widens further, or "
            "begins to normalize."
        )

    else:
        summary = (
            "Overnight funding conditions show signs of pressure. "
            f"{funding.summary}"
        )

        what_matters = (
            "The current secured-unsecured funding relationship is "
            "outside the range used by the initial Liquidity Monitor "
            "funding framework."
        )

        what_to_watch = (
            "Monitor persistence, direction, and confirmation from "
            "additional liquidity indicators as they are added."
        )

    return MorningBrief(
        headline=headline,
        summary=summary,
        what_matters=what_matters,
        what_to_watch=what_to_watch,
    )


def print_morning_brief() -> None:
    assessment = build_liquidity_assessment()
    brief = generate_morning_brief()

    print()
    print("Liquidity Monitor — Morning Brief")
    print("=================================")
    print(
        f"Score:      {assessment.overall_score}/100"
    )
    print(
        f"Condition:  {assessment.overall_condition}"
    )
    print(
        f"Confidence: {assessment.confidence}"
    )

    print()
    print("Headline")
    print("---------------------------------")
    print(brief.headline)

    print()
    print("Summary")
    print("---------------------------------")
    print(brief.summary)

    print()
    print("What Matters")
    print("---------------------------------")
    print(brief.what_matters)

    print()
    print("What To Watch")
    print("---------------------------------")
    print(brief.what_to_watch)


if __name__ == "__main__":
    print_morning_brief()