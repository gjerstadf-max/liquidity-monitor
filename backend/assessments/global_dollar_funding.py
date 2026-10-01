
from __future__ import annotations

from datetime import date

from backend.assessments.models import Assessment
from backend.signals.global_dollar_funding import (
    evaluate_global_dollar_funding_signal,
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


def assess_global_dollar_funding(
    as_of_date: date | None = None,
) -> Assessment:

    signal = (
        evaluate_global_dollar_funding_signal(
            as_of_date=as_of_date
        )
    )

    return Assessment(
        category=
            "Global Dollar Funding",

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
