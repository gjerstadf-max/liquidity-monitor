from __future__ import annotations


from backend.assessments.models import (
    Assessment,
    FactorAssessment,
    LiquidityAssessment,
)

from backend.assessments.registry import (
    FACTOR_REGISTRY,
)


# =============================================================
# OVERALL VERDICT
# =============================================================


def _overall_verdict(
    assessments: list[Assessment],
) -> str:
    """
    Deterministic qualitative synthesis.

    No numeric composite score is used.

    Rules:

    - Two or more Stressed factors:
        Stressed

    - One Stressed factor plus any other
      Elevated or Watch factor:
        Stressed

    - One isolated Stressed factor:
        Elevated

    - Any Elevated factor:
        Elevated

    - Any Watch factor:
        Watch

    - Otherwise:
        Normal
    """

    verdicts = [
        assessment.verdict
        for assessment
        in assessments
    ]

    stressed_count = (
        verdicts.count(
            "Stressed"
        )
    )

    elevated_count = (
        verdicts.count(
            "Elevated"
        )
    )

    watch_count = (
        verdicts.count(
            "Watch"
        )
    )

    # ---------------------------------------------------------
    # STRESSED
    # ---------------------------------------------------------

    if stressed_count >= 2:
        return "Stressed"

    if (
        stressed_count == 1
        and
        (
            elevated_count
            +
            watch_count
        )
        >= 1
    ):
        return "Stressed"

    # ---------------------------------------------------------
    # ELEVATED
    # ---------------------------------------------------------

    if stressed_count == 1:
        return "Elevated"

    if elevated_count >= 1:
        return "Elevated"

    # ---------------------------------------------------------
    # WATCH
    # ---------------------------------------------------------

    if watch_count >= 1:
        return "Watch"

    # ---------------------------------------------------------
    # NORMAL
    # ---------------------------------------------------------

    return "Normal"


# =============================================================
# CONFIDENCE
# =============================================================


def _overall_confidence(
    assessments: list[Assessment],
) -> str:
    """
    Overall confidence cannot exceed the weakest
    component confidence.
    """

    confidence_rank = {
        "Low": 1,
        "Moderate": 2,
        "High": 3,
    }

    reverse_rank = {
        1: "Low",
        2: "Moderate",
        3: "High",
    }

    weakest = min(
        confidence_rank.get(
            assessment.confidence,
            1,
        )
        for assessment
        in assessments
    )

    return (
        reverse_rank[
            weakest
        ]
    )


# =============================================================
# OVERALL SUMMARY
# =============================================================


def _overall_summary(
    overall_verdict: str,
    funding: Assessment,
    system_liquidity: Assessment,
    repo_market: Assessment,
    treasury_intermediation: Assessment,
) -> str:
    """
    Produce a concise qualitative headline.

    The summary intentionally does not repeat every
    factor verdict. Individual factor cards provide
    that detail.
    """

    # ---------------------------------------------------------
    # NORMAL
    # ---------------------------------------------------------

    if overall_verdict == "Normal":
        return (
            "Liquidity conditions remain broadly normal. "
            "Funding markets, system liquidity, repo-market "
            "conditions, and Treasury intermediation are not "
            "showing material signs of stress."
        )

    # ---------------------------------------------------------
    # WATCH
    # ---------------------------------------------------------
    #
    # This is an important and common configuration:
    #
    # Funding/System Liquidity may become less comfortable
    # while both market-plumbing factors remain orderly.
    # ---------------------------------------------------------

    if overall_verdict == "Watch":

        if (
            repo_market.verdict == "Normal"
            and
            treasury_intermediation.verdict == "Normal"
            and
            (
                funding.verdict != "Normal"
                or
                system_liquidity.verdict != "Normal"
            )
        ):
            return (
                "Liquidity conditions are becoming less "
                "comfortable, but secured funding markets "
                "and Treasury intermediation remain orderly. "
                "The current evidence points to tightening "
                "liquidity rather than broad market "
                "dysfunction."
            )

        if (
            funding.verdict == "Normal"
            and
            system_liquidity.verdict == "Normal"
            and
            (
                repo_market.verdict != "Normal"
                or
                treasury_intermediation.verdict != "Normal"
            )
        ):
            return (
                "Market plumbing warrants closer monitoring, "
                "but the evidence remains isolated. Broader "
                "funding and system-liquidity conditions do "
                "not currently confirm material liquidity "
                "stress."
            )

        return (
            "Liquidity conditions warrant closer monitoring. "
            "Pressure is present in at least one component, "
            "but the evidence is not broad enough to indicate "
            "material market dysfunction."
        )

    # ---------------------------------------------------------
    # ELEVATED
    # ---------------------------------------------------------

    if overall_verdict == "Elevated":

        stressed_count = sum(
            1
            for assessment
            in [
                funding,
                system_liquidity,
                repo_market,
                treasury_intermediation,
            ]
            if assessment.verdict
            == "Stressed"
        )

        if stressed_count == 1:
            return (
                "One liquidity component is showing material "
                "stress, but the broader framework does not "
                "yet show confirmation across other liquidity "
                "channels. Overall conditions are elevated "
                "and warrant close attention."
            )

        return (
            "Liquidity pressure is elevated across one or "
            "more dimensions. Multiple indicators warrant "
            "attention, although the evidence does not yet "
            "meet the framework's threshold for broad "
            "liquidity stress."
        )

    # ---------------------------------------------------------
    # STRESSED
    # ---------------------------------------------------------

    return (
        "Liquidity conditions are materially stressed. "
        "Severe pressure is either present across multiple "
        "dimensions or a stressed component is being "
        "confirmed by deterioration elsewhere in the "
        "liquidity framework."
    )


# =============================================================
# BUILD COMPLETE ASSESSMENT
# =============================================================


def build_liquidity_assessment(
) -> LiquidityAssessment:
    """
    Build the Liquidity Monitor qualitative assessment
    from all registered factors.

    Factor registration is generic.

    Individual factor economics and overall narrative
    interpretation remain explicit.
    """

    factor_results = tuple(
        FactorAssessment(
            key=
                definition.key,

            assessment=
                definition.assessor(),
        )

        for definition
        in FACTOR_REGISTRY
    )

    assessments = [
        item.assessment
        for item
        in factor_results
    ]

    factors_by_key = {
        item.key:
            item.assessment

        for item
        in factor_results
    }

    overall_verdict = (
        _overall_verdict(
            assessments
        )
    )

    confidence = (
        _overall_confidence(
            assessments
        )
    )

    # ---------------------------------------------------------
    # EXPLICIT ECONOMIC SUMMARY
    # ---------------------------------------------------------
    #
    # The overall narrative still intentionally understands
    # the economic roles of the existing factors.
    #
    # We are not turning this into a generic scoring engine.
    # ---------------------------------------------------------

    summary = (
        _overall_summary(
            overall_verdict=
                overall_verdict,

            funding=
                factors_by_key[
                    "funding"
                ],

            system_liquidity=
                factors_by_key[
                    "system_liquidity"
                ],

            repo_market=
                factors_by_key[
                    "repo_market"
                ],

            treasury_intermediation=
                factors_by_key[
                    "treasury_intermediation"
                ],
        )
    )

    return LiquidityAssessment(
        overall_verdict=
            overall_verdict,

        confidence=
            confidence,

        factors=
            factor_results,

        summary=
            summary,
    )

# =============================================================
# TERMINAL DISPLAY
# =============================================================


def _print_assessment(
    assessment: Assessment,
) -> None:

    print()
    print(
        assessment.category.upper()
    )

    print(
        "-" * 72
    )

    print(
        f"Verdict:     "
        f"{assessment.verdict}"
    )

    print(
        f"Confidence:  "
        f"{assessment.confidence}"
    )

    print()

    print(
        assessment.summary
    )


def run_assessment() -> None:

    assessment = (
        build_liquidity_assessment()
    )

    print()
    print(
        "Liquidity Monitor Assessment"
    )

    print(
        "=" * 72
    )

    print()
    print(
        "OVERALL"
    )

    print(
        "-" * 72
    )

    print(
        f"Verdict:     "
        f"{assessment.overall_verdict}"
    )

    print(
        f"Confidence:  "
        f"{assessment.confidence}"
    )

    print()

    print(
        assessment.summary
    )

    _print_assessment(
        assessment.funding
    )

    _print_assessment(
        assessment.system_liquidity
    )

    _print_assessment(
        assessment.repo_market
    )

    _print_assessment(
        assessment.treasury_intermediation
    )


if __name__ == "__main__":
    run_assessment()