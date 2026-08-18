from dataclasses import dataclass

from backend.assessments.engine import (
    build_liquidity_assessment,
)
from backend.assessments.models import (
    LiquidityAssessment,
)
from backend.metrics.funding import (
    funding_spread_statistics,
)
from backend.metrics.system_liquidity import (
    system_liquidity_history_metrics,
    system_liquidity_metrics,
)


@dataclass(frozen=True)
class MorningBrief:
    headline: str
    summary: str
    what_matters: str
    what_to_watch: str


def generate_morning_brief(
    assessment: LiquidityAssessment | None = None,
) -> MorningBrief:
    """
    Generate deterministic commentary from the
    multi-factor Liquidity Monitor assessment.
    """

    if assessment is None:
        assessment = build_liquidity_assessment()

    funding = assessment.funding

    system = assessment.system_liquidity

    if system is None:
        raise RuntimeError(
            "System Liquidity assessment is missing."
        )


    funding_stats = (
        funding_spread_statistics()
    )

    system_history = (
        system_liquidity_history_metrics()
    )

    system_current = (
        system_liquidity_metrics()
    )


    # =========================================================
    # HEADLINE
    # =========================================================

    if assessment.overall_condition == "Healthy":

        headline = (
            "Liquidity conditions remain healthy."
        )

    elif assessment.overall_condition == "Normal":

        headline = (
            "Liquidity conditions remain broadly normal."
        )

    elif assessment.overall_condition == "Watch":

        headline = (
            "Liquidity conditions warrant closer monitoring."
        )

    elif assessment.overall_condition == "Warning":

        headline = (
            "Liquidity pressure is elevated."
        )

    else:

        headline = (
            "Liquidity conditions are materially stressed."
        )


    # =========================================================
    # SUMMARY
    # =========================================================

    summary = (
        f"The overall Liquidity Monitor score is "
        f"{assessment.overall_score}/100, classified as "
        f"{assessment.overall_condition}. "
        f"Funding conditions are "
        f"{funding.condition.lower()} at "
        f"{funding.score}/100, while system liquidity is "
        f"{system.condition.lower()} at "
        f"{system.score}/100."
    )


    # =========================================================
    # WHAT MATTERS
    # =========================================================

    what_matters = (
        f"The SOFR-EFFR spread is currently "
        f"{funding_stats.current_spread_bp:+.0f} bp, "
        f"placing it near the "
        f"{funding_stats.percentile_60d:.0f}th percentile "
        f"of its recent distribution with a z-score of "
        f"{funding_stats.zscore_60d:+.2f}. "
        f"The system-liquidity proxy stands at "
        f"${system_history.current_proxy_billions:,.0f}B "
        f"and has changed "
        f"${system_history.four_week_change_billions:+,.0f}B "
        f"over four weeks and "
        f"${system_history.thirteen_week_change_billions:+,.0f}B "
        f"over thirteen weeks. "
        f"The current proxy is near the "
        f"{system_history.percentile_52_week:.0f}th percentile "
        f"of its 52-week range with a z-score of "
        f"{system_history.zscore_52_week:+.2f}."
    )


    # =========================================================
    # WHAT TO WATCH
    # =========================================================

    funding_watch = (
        "Watch for a persistent widening of SOFR above EFFR "
        "and movement into the upper tail of its recent "
        "distribution."
    )


    if system.condition == "Healthy":

        system_watch = (
            "System liquidity remains comfortable; watch for "
            "a sustained negative turn in the four- and "
            "thirteen-week trends."
        )

    elif system.condition == "Watch":

        system_watch = (
            "The key issue is whether the recent system-"
            "liquidity contraction persists. Continued reserve "
            "drainage or further TGA rebuilding would increase "
            "the significance of the current signal."
        )

    elif system.condition == "Warning":

        system_watch = (
            "Watch closely for continued reserve drainage, "
            "further TGA accumulation, and confirmation from "
            "overnight funding markets."
        )

    else:

        system_watch = (
            "Focus on whether liquidity contraction continues "
            "and whether funding-market pricing begins to "
            "confirm broader stress."
        )


    what_to_watch = (
        funding_watch
        + " "
        + system_watch
        + " "
        + (
            f"Over the latest four-week period, reserve "
            f"balances contributed "
            f"${system_current.reserve_4_week_contribution_billions:+,.0f}B, "
            f"ON RRP contributed "
            f"${system_current.rrp_4_week_contribution_billions:+,.0f}B, "
            f"and the TGA effect contributed "
            f"${system_current.tga_4_week_contribution_billions:+,.0f}B."
        )
    )


    return MorningBrief(
        headline=headline,
        summary=summary,
        what_matters=what_matters,
        what_to_watch=what_to_watch,
    )


def print_morning_brief() -> None:

    brief = generate_morning_brief()

    print()
    print("Morning Liquidity Brief")
    print("================================")

    print()
    print(brief.headline)

    print()
    print(brief.summary)

    print()
    print("WHAT MATTERS")
    print("--------------------------------")
    print(brief.what_matters)

    print()
    print("WHAT TO WATCH")
    print("--------------------------------")
    print(brief.what_to_watch)


if __name__ == "__main__":
    print_morning_brief()