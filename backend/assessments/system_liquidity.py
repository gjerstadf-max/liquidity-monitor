from datetime import date


from backend.assessments.models import Assessment
from backend.signals.system_liquidity import (
    evaluate_system_liquidity_signal,
)


SEVERITY_VERDICT = {
    "Normal": "Normal",
    "Watch": "Watch",
    "Warning": "Elevated",
    "Critical": "Stressed",
}


SEVERITY_CONFIDENCE = {
    "Normal": "Moderate",
    "Watch": "Moderate",
    "Warning": "High",
    "Critical": "High",
}


def assess_system_liquidity(
    as_of_date: date | None = None,
) -> Assessment:

    signal = (
        evaluate_system_liquidity_signal(
            as_of_date=as_of_date
        )
    )


    return Assessment(
        category=
            "System Liquidity",

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
