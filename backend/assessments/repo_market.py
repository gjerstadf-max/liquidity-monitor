from datetime import date


from backend.assessments.models import Assessment
from backend.signals.repo_market import (
    evaluate_repo_market_signal,
)


SEVERITY_VERDICT = {
    "Normal": "Normal",
    "Watch": "Watch",
    "Warning": "Elevated",
    "Critical": "Stressed",
}


SEVERITY_CONFIDENCE = {
    "Normal": "High",
    "Watch": "Moderate",
    "Warning": "High",
    "Critical": "High",
}


def assess_repo_market(
    as_of_date: date | None = None,
) -> Assessment:

    signal = (
        evaluate_repo_market_signal(
            as_of_date=as_of_date
        )
    )


    return Assessment(
        category=
            "Repo Market Pressure",

        verdict=
            SEVERITY_VERDICT[
                signal.severity
            ],

        confidence=
            SEVERITY_CONFIDENCE[
                signal.severity
            ],

        summary=
            signal.message,
    )
