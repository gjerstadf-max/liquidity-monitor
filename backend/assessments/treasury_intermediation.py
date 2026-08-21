from backend.assessments.models import Assessment

from backend.signals.treasury_intermediation import (
    evaluate_treasury_intermediation_signal,
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


def assess_treasury_intermediation() -> Assessment:
    """
    Convert the validated Treasury Intermediation
    signal into a qualitative assessment.

    Factor #4 signal thresholds remain unchanged here.
    """

    signal = (
        evaluate_treasury_intermediation_signal()
    )

    return Assessment(
        category=
            "Treasury Intermediation",

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