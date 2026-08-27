from backend.assessments.engine import (
    _overall_verdict,
)
from backend.assessments.models import (
    Assessment,
)


def assessment(
    verdict: str,
) -> Assessment:

    return Assessment(
        category="Test",
        verdict=verdict,
        confidence="High",
        summary="Test assessment.",
    )


def verdicts(
    *values: str,
) -> str:

    return _overall_verdict(
        [
            assessment(value)
            for value
            in values
        ]
    )


def test_all_normal_is_normal():
    assert verdicts(
        "Normal",
        "Normal",
        "Normal",
        "Normal",
        "Normal",
    ) == "Normal"


def test_one_watch_is_watch():
    assert verdicts(
        "Watch",
        "Normal",
        "Normal",
        "Normal",
        "Normal",
    ) == "Watch"


def test_multiple_watch_remain_watch():
    assert verdicts(
        "Watch",
        "Watch",
        "Normal",
        "Normal",
        "Normal",
    ) == "Watch"


def test_one_elevated_is_elevated():
    assert verdicts(
        "Elevated",
        "Normal",
        "Normal",
        "Normal",
        "Normal",
    ) == "Elevated"


def test_isolated_stressed_is_elevated():
    assert verdicts(
        "Stressed",
        "Normal",
        "Normal",
        "Normal",
        "Normal",
    ) == "Elevated"


def test_stressed_plus_one_watch_is_elevated():
    assert verdicts(
        "Stressed",
        "Watch",
        "Normal",
        "Normal",
        "Normal",
    ) == "Elevated"


def test_stressed_plus_two_watch_is_stressed():
    assert verdicts(
        "Stressed",
        "Watch",
        "Watch",
        "Normal",
        "Normal",
    ) == "Stressed"


def test_stressed_plus_elevated_is_stressed():
    assert verdicts(
        "Stressed",
        "Elevated",
        "Normal",
        "Normal",
        "Normal",
    ) == "Stressed"


def test_two_stressed_is_stressed():
    assert verdicts(
        "Stressed",
        "Stressed",
        "Normal",
        "Normal",
        "Normal",
    ) == "Stressed"
