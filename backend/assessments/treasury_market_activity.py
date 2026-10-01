from datetime import date


from backend.assessments.models import (
    Assessment,
)

from backend.signals.treasury_market_activity import (
    evaluate_treasury_market_activity_signal,
)


# =============================================================
# SIGNAL -> ASSESSMENT
# =============================================================


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


# =============================================================
# PUBLIC ASSESSMENT
# =============================================================


def assess_treasury_market_activity(
    as_of_date: date | None = None,
) -> Assessment:
    """
    Convert the Treasury Market Activity signal into
    a qualitative assessment.

    Factor #5 evaluates Treasury bill supply load and
    auction absorption as separate dimensions.

    Heavy supply alone can warrant monitoring, while
    weak auction absorption or convergence across both
    dimensions can produce a more severe assessment.
    """

    signal = (
        evaluate_treasury_market_activity_signal(
            as_of_date=as_of_date
        )
    )

    return Assessment(
        category=
            "Treasury Market Activity",

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
