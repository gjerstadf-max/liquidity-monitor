from __future__ import annotations

from dataclasses import dataclass

from backend.assessments.engine import (
    build_liquidity_assessment,
)
from backend.assessments.models import (
    LiquidityAssessment,
)
from backend.factors.registry import (
    factor_definition,
)


# =============================================================
# DATA OBJECT
# =============================================================


@dataclass(frozen=True)
class MorningBrief:
    headline: str
    summary: str
    what_matters: list[str]
    what_to_watch: list[str]


# =============================================================
# HEADLINE
# =============================================================


def _headline(
    verdict: str,
) -> str:
    headlines = {
        "Normal":
            "Liquidity conditions remain broadly normal.",

        "Watch":
            "Liquidity conditions warrant closer monitoring.",

        "Elevated":
            "Liquidity pressure is elevated.",

        "Stressed":
            "Liquidity conditions are materially stressed.",
    }

    return headlines.get(
        verdict,
        "Liquidity conditions warrant review.",
    )


# =============================================================
# BUILD MORNING BRIEF
# =============================================================


def build_morning_brief(
    assessment: LiquidityAssessment | None = None,
) -> MorningBrief:
    """
    Build deterministic daily liquidity commentary.

    If an assessment is supplied, reuse it.
    Otherwise build the current assessment.

    Factor ordering comes from the central factor registry
    through assessment.factors.

    Factor-specific economic commentary remains explicit
    in backend.commentary.factor_commentary.
    """

    if assessment is None:
        assessment = (
            build_liquidity_assessment()
        )

    what_matters: list[str] = []
    what_to_watch: list[str] = []

    # ---------------------------------------------------------
    # REGISTERED FACTORS
    # ---------------------------------------------------------

    for factor in assessment.factors:

        definition = (
            factor_definition(
                factor.key
            )
        )

        what_matters.append(
            definition.what_matters_builder()
        )

        what_to_watch.append(
            definition.watch_builder(
                factor.assessment.verdict
            )
        )

    # ---------------------------------------------------------
    # RESULT
    # ---------------------------------------------------------

    return MorningBrief(
        headline=
            _headline(
                assessment.overall_verdict
            ),

        summary=
            assessment.summary,

        what_matters=
            what_matters,

        what_to_watch=
            what_to_watch,
    )


# =============================================================
# TERMINAL DISPLAY
# =============================================================


def print_morning_brief(
    brief: MorningBrief,
) -> None:
    """
    Print one Morning Brief to the terminal.
    """

    print()

    print(
        "LIQUIDITY MONITOR — MORNING BRIEF"
    )

    print(
        "=" * 80
    )

    print()

    print(
        brief.headline
    )

    print()

    print(
        brief.summary
    )

    print()

    # ---------------------------------------------------------
    # WHAT MATTERS
    # ---------------------------------------------------------

    print(
        "WHAT MATTERS"
    )

    print(
        "-" * 80
    )

    print()

    for item in brief.what_matters:

        print(
            f"• {item}"
        )

        print()

    # ---------------------------------------------------------
    # WHAT TO WATCH
    # ---------------------------------------------------------

    print(
        "WHAT TO WATCH"
    )

    print(
        "-" * 80
    )

    print()

    for item in brief.what_to_watch:

        print(
            f"• {item}"
        )

        print()


# =============================================================
# RUN
# =============================================================


def run_morning_brief(
    assessment: LiquidityAssessment | None = None,
) -> None:
    """
    Build and print the current Morning Brief.
    """

    brief = (
        build_morning_brief(
            assessment=
                assessment
        )
    )

    print_morning_brief(
        brief
    )


# =============================================================
# DIRECT EXECUTION
# =============================================================


if __name__ == "__main__":
    run_morning_brief()