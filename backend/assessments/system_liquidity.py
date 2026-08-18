from backend.assessments.models import Assessment
from backend.signals.system_liquidity import (
    evaluate_system_liquidity_signal,
)


SEVERITY_SCORE = {
    "Normal": 95,
    "Watch": 75,
    "Warning": 45,
    "Critical": 20,
}


SEVERITY_CONDITION = {
    "Normal": "Healthy",
    "Watch": "Watch",
    "Warning": "Warning",
    "Critical": "Stressed",
}


# System Liquidity is a constructed proxy rather than
# a directly observed market price, so Normal conditions
# receive Moderate rather than High confidence for now.
SEVERITY_CONFIDENCE = {
    "Normal": "Moderate",
    "Watch": "Moderate",
    "Warning": "High",
    "Critical": "High",
}


def assess_system_liquidity() -> Assessment:
    """
    Convert the deterministic System Liquidity signal
    into a scored assessment.
    """

    signal = (
        evaluate_system_liquidity_signal()
    )

    return Assessment(
        category="System Liquidity",

        score=SEVERITY_SCORE[
            signal.severity
        ],

        condition=SEVERITY_CONDITION[
            signal.severity
        ],

        confidence=SEVERITY_CONFIDENCE[
            signal.severity
        ],

        summary=signal.message,
    )