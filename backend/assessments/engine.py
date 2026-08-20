from backend.assessments.funding import (
    assess_funding,
)
from backend.assessments.models import (
    Assessment,
    LiquidityAssessment,
)
from backend.assessments.repo_market import (
    assess_repo_market,
)
from backend.assessments.system_liquidity import (
    assess_system_liquidity,
)


VERDICT_RANK = {
    "Normal": 0,
    "Watch": 1,
    "Elevated": 2,
    "Stressed": 3,
}


CONFIDENCE_RANK = {
    "Low": 1,
    "Moderate": 2,
    "High": 3,
}


# =============================================================
# OVERALL VERDICT
# =============================================================


def _overall_verdict(
    assessments: list[
        Assessment
    ],
) -> str:
    """
    Produce a qualitative overall conclusion.

    No weighted average is used.

    Principles:

    - Any Watch deserves monitoring.
    - Any Elevated factor makes the overall picture Elevated.
    - One isolated Stressed factor produces Elevated unless
      another factor provides confirmation.
    - Stressed conditions with confirmation from another
      factor produce an overall Stressed verdict.
    """

    verdicts = [
        assessment.verdict
        for assessment
        in assessments
    ]


    stressed = verdicts.count(
        "Stressed"
    )

    elevated = verdicts.count(
        "Elevated"
    )

    watch = verdicts.count(
        "Watch"
    )


    if stressed >= 2:

        return "Stressed"


    if stressed == 1:

        if (
            elevated >= 1
            or
            watch >= 1
        ):

            return "Stressed"

        return "Elevated"


    if elevated >= 1:

        return "Elevated"


    if watch >= 1:

        return "Watch"


    return "Normal"


# =============================================================
# CONFIDENCE
# =============================================================


def _overall_confidence(
    assessments: list[
        Assessment
    ],
) -> str:

    lowest = min(
        CONFIDENCE_RANK.get(
            assessment.confidence,
            1,
        )
        for assessment
        in assessments
    )


    reverse_rank = {
        1: "Low",
        2: "Moderate",
        3: "High",
    }


    return reverse_rank[
        lowest
    ]


# =============================================================
# OVERALL NARRATIVE
# =============================================================


def _overall_summary(
    funding: Assessment,
    system: Assessment,
    repo: Assessment,
    overall_verdict: str,
) -> str:

    # ---------------------------------------------------------
    # ALL NORMAL
    # ---------------------------------------------------------

    if overall_verdict == "Normal":

        return (
            "The major liquidity indicators are broadly "
            "consistent with orderly market conditions."
        )


    # ---------------------------------------------------------
    # TIGHTENING, BUT REPO STILL ORDERLY
    # ---------------------------------------------------------

    if (
        repo.verdict == "Normal"
        and
        (
            funding.verdict != "Normal"
            or
            system.verdict != "Normal"
        )
    ):

        return (
            "Liquidity conditions are becoming less "
            "comfortable, but secured funding markets "
            "remain orderly. The current evidence points "
            "to tightening liquidity rather than broad "
            "market dysfunction."
        )


    # ---------------------------------------------------------
    # ISOLATED SEVERE FACTOR
    # ---------------------------------------------------------

    stressed_factors = [
        assessment.category
        for assessment
        in [
            funding,
            system,
            repo,
        ]
        if assessment.verdict
        == "Stressed"
    ]


    if (
        len(
            stressed_factors
        ) == 1
        and
        overall_verdict == "Elevated"
    ):

        return (
            f"Severe pressure is currently concentrated "
            f"in {stressed_factors[0]}, while the other "
            "major liquidity factors do not yet provide "
            "broad confirmation."
        )


    # ---------------------------------------------------------
    # CONFIRMED STRESS
    # ---------------------------------------------------------

    if overall_verdict == "Stressed":

        return (
            "Stress is being confirmed across more than "
            "one liquidity channel, indicating broader "
            "market pressure rather than an isolated "
            "signal."
        )


    # ---------------------------------------------------------
    # GENERAL ELEVATED
    # ---------------------------------------------------------

    if overall_verdict == "Elevated":

        return (
            "One or more liquidity channels are showing "
            "material pressure. Conditions remain functional, "
            "but the evidence is stronger than a routine "
            "monitoring signal."
        )


    # ---------------------------------------------------------
    # WATCH
    # ---------------------------------------------------------

    return (
        "One or more liquidity indicators warrant closer "
        "monitoring, but there is not currently evidence "
        "of broad market stress."
    )

# =============================================================
# ASSESSMENT
# =============================================================


def build_liquidity_assessment(
) -> LiquidityAssessment:

    funding = (
        assess_funding()
    )


    system_liquidity = (
        assess_system_liquidity()
    )


    repo_market = (
        assess_repo_market()
    )


    components = [
        funding,
        system_liquidity,
        repo_market,
    ]


    overall_verdict = (
        _overall_verdict(
            components
        )
    )


    confidence = (
        _overall_confidence(
            components
        )
    )


    summary = (
        _overall_summary(
            funding=
                funding,

            system=
                system_liquidity,

            repo=
                repo_market,

            overall_verdict=
                overall_verdict,
        )
    )


    return LiquidityAssessment(
        overall_verdict=
            overall_verdict,

        confidence=
            confidence,

        funding=
            funding,

        system_liquidity=
            system_liquidity,

        repo_market=
            repo_market,

        summary=
            summary,
    )


# =============================================================
# TERMINAL DISPLAY
# =============================================================


def run_assessment() -> None:

    assessment = (
        build_liquidity_assessment()
    )


    print()
    print(
        "Liquidity Monitor Assessment"
    )

    print("=" * 72)


    print()
    print("OVERALL CONCLUSION")
    print("-" * 72)

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


    for component in [
        assessment.funding,
        assessment.system_liquidity,
        assessment.repo_market,
    ]:

        print()
        print(
            component.category.upper()
        )

        print("-" * 72)

        print(
            f"Verdict:     "
            f"{component.verdict}"
        )

        print(
            f"Confidence:  "
            f"{component.confidence}"
        )

        print()

        print(
            component.summary
        )


if __name__ == "__main__":
    run_assessment()