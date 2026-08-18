from backend.assessments.funding import (
    assess_funding,
)
from backend.assessments.models import (
    LiquidityAssessment,
)
from backend.assessments.system_liquidity import (
    assess_system_liquidity,
)


def _overall_condition(
    score: int,
) -> str:
    """
    Convert the composite score into a headline
    liquidity condition.
    """

    if score >= 90:
        return "Healthy"

    if score >= 80:
        return "Normal"

    if score >= 65:
        return "Watch"

    if score >= 40:
        return "Warning"

    return "Stressed"


def _overall_confidence(
    funding_confidence: str,
    liquidity_confidence: str,
) -> str:
    """
    Overall confidence cannot exceed the weakest
    major component.
    """

    confidence_rank = {
        "Low": 1,
        "Moderate": 2,
        "High": 3,
    }

    lowest = min(
        confidence_rank.get(
            funding_confidence,
            1,
        ),
        confidence_rank.get(
            liquidity_confidence,
            1,
        ),
    )

    reverse_rank = {
        1: "Low",
        2: "Moderate",
        3: "High",
    }

    return reverse_rank[lowest]


def build_liquidity_assessment(
) -> LiquidityAssessment:
    """
    Build the first multi-factor Liquidity Monitor
    assessment.

    Current weights:

        Funding Conditions    50%
        System Liquidity      50%

    These weights are intentionally simple and
    transparent while the framework is still growing.
    """

    funding = assess_funding()

    system_liquidity = (
        assess_system_liquidity()
    )


    # ---------------------------------------------------------
    # Composite score
    # ---------------------------------------------------------

    overall_score = round(
        (
            funding.score
            + system_liquidity.score
        )
        / 2
    )


    overall_condition = (
        _overall_condition(
            overall_score
        )
    )


    confidence = (
        _overall_confidence(
            funding.confidence,
            system_liquidity.confidence,
        )
    )


    # ---------------------------------------------------------
    # Summary
    # ---------------------------------------------------------

    summary = (
        f"Funding conditions are "
        f"{funding.condition.lower()} "
        f"with a score of "
        f"{funding.score}/100. "
        f"System liquidity is "
        f"{system_liquidity.condition.lower()} "
        f"with a score of "
        f"{system_liquidity.score}/100."
    )


    return LiquidityAssessment(
        overall_score=
            overall_score,

        overall_condition=
            overall_condition,

        confidence=
            confidence,

        funding=
            funding,

        system_liquidity=
            system_liquidity,

        summary=
            summary,
    )


def run_assessment() -> None:

    assessment = (
        build_liquidity_assessment()
    )


    print()
    print("Liquidity Monitor Assessment")
    print("================================")


    print()
    print("OVERALL")
    print("--------------------------------")

    print(
        f"Score:       "
        f"{assessment.overall_score}/100"
    )

    print(
        f"Condition:   "
        f"{assessment.overall_condition}"
    )

    print(
        f"Confidence:  "
        f"{assessment.confidence}"
    )


    print()
    print("FUNDING")
    print("--------------------------------")

    print(
        f"Score:       "
        f"{assessment.funding.score}/100"
    )

    print(
        f"Condition:   "
        f"{assessment.funding.condition}"
    )

    print(
        f"Confidence:  "
        f"{assessment.funding.confidence}"
    )


    print()
    print("SYSTEM LIQUIDITY")
    print("--------------------------------")

    print(
        f"Score:       "
        f"{assessment.system_liquidity.score}/100"
    )

    print(
        f"Condition:   "
        f"{assessment.system_liquidity.condition}"
    )

    print(
        f"Confidence:  "
        f"{assessment.system_liquidity.confidence}"
    )


    print()
    print("SUMMARY")
    print("--------------------------------")

    print(
        assessment.summary
    )


if __name__ == "__main__":
    run_assessment()