
from __future__ import annotations

from datetime import date

from backend.assessments.models import Assessment
from backend.signals.commercial_paper import (
    evaluate_commercial_paper_signal,
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


def assess_commercial_paper(
    as_of_date: date | None = None,
) -> Assessment:

    signal = (
        evaluate_commercial_paper_signal(
            as_of_date=as_of_date
        )
    )

    return Assessment(
        category=
            "Commercial Paper",

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
