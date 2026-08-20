from __future__ import annotations

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
from backend.metrics.repo_market import (
    repo_market_statistics,
)
from backend.metrics.system_liquidity import (
    system_liquidity_history_metrics,
    system_liquidity_metrics,
)


# =============================================================
# MORNING BRIEF MODEL
# =============================================================


@dataclass(frozen=True)
class MorningBrief:
    headline: str
    summary: str
    what_matters: str
    what_to_watch: str


# =============================================================
# HEADLINE
# =============================================================


def _build_headline(
    overall_verdict: str,
) -> str:

    headline_map = {

        "Normal":
            "Liquidity conditions remain broadly normal.",

        "Watch":
            "Liquidity conditions warrant closer monitoring.",

        "Elevated":
            "Liquidity pressure is elevated.",

        "Stressed":
            "Liquidity conditions are materially stressed.",
    }


    return headline_map.get(
        overall_verdict,
        "Liquidity conditions warrant monitoring.",
    )


# =============================================================
# FUNDING WATCH COMMENTARY
# =============================================================


def _funding_watch_text(
    verdict: str,
) -> str:

    if verdict == "Normal":

        return (
            "Funding conditions remain orderly. "
            "Watch for a persistent widening of SOFR "
            "above EFFR or movement into the upper tail "
            "of its recent distribution."
        )


    if verdict == "Watch":

        return (
            "Funding conditions warrant monitoring. "
            "The key issue is whether the SOFR-EFFR "
            "spread remains unusually wide or begins "
            "to normalize."
        )


    if verdict == "Elevated":

        return (
            "Funding pressure is elevated. "
            "Watch for continued SOFR-EFFR widening, "
            "persistent positive spread pressure, and "
            "confirmation from repo-market internals."
        )


    return (
        "Funding conditions are stressed. "
        "Focus on persistence, the breadth of overnight "
        "funding pressure, and whether policy facilities "
        "or other market mechanisms begin absorbing "
        "the strain."
    )


# =============================================================
# SYSTEM LIQUIDITY WATCH COMMENTARY
# =============================================================


def _system_watch_text(
    verdict: str,
) -> str:

    if verdict == "Normal":

        return (
            "System liquidity remains broadly comfortable. "
            "Watch for a sustained negative turn in the "
            "four- and thirteen-week liquidity trends."
        )


    if verdict == "Watch":

        return (
            "System liquidity warrants monitoring. "
            "The key issue is whether the recent liquidity "
            "contraction persists. Continued reserve drainage "
            "or further TGA rebuilding would increase the "
            "significance of the current signal."
        )


    if verdict == "Elevated":

        return (
            "System-liquidity pressure is elevated. "
            "Watch closely for continued reserve drainage, "
            "further TGA accumulation, and confirmation from "
            "overnight funding markets."
        )


    return (
        "System liquidity is stressed. "
        "Focus on whether liquidity contraction continues "
        "and whether funding and repo-market pricing confirm "
        "broader market pressure."
    )


# =============================================================
# REPO MARKET WATCH COMMENTARY
# =============================================================


def _repo_watch_text(
    verdict: str,
) -> str:

    if verdict == "Normal":

        return (
            "Repo-market internals remain orderly. "
            "Watch for simultaneous widening in secured-versus-"
            "unsecured funding spreads, transaction dispersion, "
            "and the SOFR upper tail."
        )


    if verdict == "Watch":

        return (
            "Repo-market internals warrant monitoring. "
            "Watch whether currently unusual measures broaden "
            "across multiple repo diagnostics or move beyond "
            "normal statistical variation into economically "
            "meaningful pressure."
        )


    if verdict == "Elevated":

        return (
            "Repo-market pressure is elevated. "
            "Watch for persistence across SOFR-OBFR, "
            "SOFR-TGCR, SOFR-BGCR, transaction dispersion, "
            "and upper-tail pricing."
        )


    return (
        "Repo-market conditions are stressed. "
        "Focus on whether severe funding pressure persists, "
        "whether the stress broadens across repo venues, and "
        "whether official liquidity facilities or other "
        "market mechanisms begin absorbing the pressure."
    )


# =============================================================
# GENERATE MORNING BRIEF
# =============================================================


def generate_morning_brief(
    assessment: LiquidityAssessment | None = None,
) -> MorningBrief:
    """
    Generate deterministic commentary from the
    multi-factor Liquidity Monitor assessment.

    The Morning Brief does not calculate an overall
    numeric liquidity score.

    It summarizes three independent factors:

        Funding Conditions
        System Liquidity
        Repo Market Pressure

    The overall conclusion is qualitative.
    """

    if assessment is None:

        assessment = (
            build_liquidity_assessment()
        )


    funding = (
        assessment.funding
    )


    system = (
        assessment.system_liquidity
    )


    repo = (
        assessment.repo_market
    )


    # =========================================================
    # LOAD UNDERLYING METRICS
    # =========================================================


    funding_stats = (
        funding_spread_statistics()
    )


    system_history = (
        system_liquidity_history_metrics()
    )


    system_current = (
        system_liquidity_metrics()
    )


    repo_stats = (
        repo_market_statistics(
            lookback=60
        )
    )


    # =========================================================
    # HEADLINE
    # =========================================================


    headline = (
        _build_headline(
            assessment.overall_verdict
        )
    )


    # =========================================================
    # SUMMARY
    # =========================================================
    #
    # Use the assessment engine's qualitative synthesis.
    # This preserves disagreement between factors instead
    # of averaging them into a single numeric score.
    # =========================================================


    summary = (
        assessment.summary
    )


    # =========================================================
    # WHAT MATTERS
    # =========================================================


    what_matters = (

        # -----------------------------------------------------
        # FUNDING
        # -----------------------------------------------------

        f"Funding conditions are "
        f"{funding.verdict.lower()}. "

        f"The SOFR-EFFR spread is currently "
        f"{funding_stats.current_spread_bp:+.0f} bp, "
        f"placing it near the "
        f"{funding_stats.percentile_60d:.0f}th percentile "
        f"of its recent distribution with a z-score of "
        f"{funding_stats.zscore_60d:+.2f}. "


        # -----------------------------------------------------
        # SYSTEM LIQUIDITY
        # -----------------------------------------------------

        f"System liquidity is "
        f"{system.verdict.lower()}. "

        f"The system-liquidity proxy stands at "
        f"${system_history.current_proxy_billions:,.0f}B "
        f"and has changed "
        f"${system_history.four_week_change_billions:+,.0f}B "
        f"over four weeks and "
        f"${system_history.thirteen_week_change_billions:+,.0f}B "
        f"over thirteen weeks. "

        f"The current proxy is near the "
        f"{system_history.percentile_52_week:.0f}th percentile "
        f"of its 52-week distribution with a z-score of "
        f"{system_history.zscore_52_week:+.2f}. "


        # -----------------------------------------------------
        # REPO MARKET
        # -----------------------------------------------------

        f"Repo-market pressure is "
        f"{repo.verdict.lower()}. "

        f"SOFR is "
        f"{float(repo_stats.sofr_obfr.current):+.0f} bp "
        f"above OBFR and "
        f"{float(repo_stats.sofr_tgcr.current):+.0f} bp "
        f"above TGCR. "

        f"The SOFR interquartile range is "
        f"{float(repo_stats.sofr_iqr.current):.0f} bp, "
        f"while the 99th-percentile premium is "
        f"{float(repo_stats.sofr_upper_tail.current):.0f} bp."
    )


    # =========================================================
    # WHAT TO WATCH
    # =========================================================


    funding_watch = (
        _funding_watch_text(
            funding.verdict
        )
    )


    system_watch = (
        _system_watch_text(
            system.verdict
        )
    )


    repo_watch = (
        _repo_watch_text(
            repo.verdict
        )
    )


    system_driver_text = (

        f"Over the latest four-week period, "
        f"reserve balances contributed "
        f"${system_current.reserve_4_week_contribution_billions:+,.0f}B, "
        f"ON RRP contributed "
        f"${system_current.rrp_4_week_contribution_billions:+,.0f}B, "
        f"and the TGA effect contributed "
        f"${system_current.tga_4_week_contribution_billions:+,.0f}B "
        f"to the change in the system-liquidity proxy."
    )


    what_to_watch = (
        funding_watch
        + " "
        + system_watch
        + " "
        + repo_watch
        + " "
        + system_driver_text
    )


    # =========================================================
    # RETURN
    # =========================================================


    return MorningBrief(
        headline=
            headline,

        summary=
            summary,

        what_matters=
            what_matters,

        what_to_watch=
            what_to_watch,
    )


# =============================================================
# TERMINAL DISPLAY
# =============================================================


def print_morning_brief() -> None:

    brief = (
        generate_morning_brief()
    )


    print()
    print(
        "Morning Liquidity Brief"
    )

    print("=" * 72)


    print()
    print(
        brief.headline
    )


    print()
    print("SUMMARY")
    print("-" * 72)

    print(
        brief.summary
    )


    print()
    print("WHAT MATTERS")
    print("-" * 72)

    print(
        brief.what_matters
    )


    print()
    print("WHAT TO WATCH")
    print("-" * 72)

    print(
        brief.what_to_watch
    )


# =============================================================
# MAIN
# =============================================================


if __name__ == "__main__":
    print_morning_brief()