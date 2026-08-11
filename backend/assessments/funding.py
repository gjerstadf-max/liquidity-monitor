from backend.assessments.models import Assessment
from backend.signals.funding import evaluate_funding_signal


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


SEVERITY_CONFIDENCE = {
    "Normal": "High",
    "Watch": "Moderate",
    "Warning": "High",
    "Critical": "High",
}


def assess_funding() -> Assessment:
    signal = evaluate_funding_signal()

    if signal.severity not in SEVERITY_SCORE:
        raise RuntimeError(
            f"Unsupported funding signal severity: {signal.severity}"
        )

    return Assessment(
        category="Funding",
        score=SEVERITY_SCORE[signal.severity],
        condition=SEVERITY_CONDITION[signal.severity],
        confidence=SEVERITY_CONFIDENCE[signal.severity],
        summary=signal.message,
    )