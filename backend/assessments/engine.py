from backend.assessments.funding import assess_funding
from backend.assessments.models import LiquidityAssessment


def run_assessment() -> None:

    funding = assess_funding()

    assessment = LiquidityAssessment(
        overall_score=funding.score,
        overall_condition=funding.condition,
        confidence=funding.confidence,
        funding=funding,
        summary=funding.summary,
    )

    print()
    print("Liquidity Monitor")
    print("==============================")
    print(f"Overall Score : {assessment.overall_score}/100")
    print(f"Condition     : {assessment.overall_condition}")
    print(f"Confidence    : {assessment.confidence}")

    print()

    print("Category Scores")
    print("------------------------------")

    print(
        f"Funding        "
        f"{assessment.funding.score}/100   "
        f"{assessment.funding.condition}"
    )

    print()

    print("Summary")
    print("------------------------------")

    print(assessment.summary)


if __name__ == "__main__":
    run_assessment()