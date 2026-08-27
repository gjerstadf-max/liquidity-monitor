from backend.assessments.models import Assessment
from backend.factors.registry import (
    FACTOR_REGISTRY,
    FACTOR_BY_KEY,
)


VALID_VERDICTS = {
    "Normal",
    "Watch",
    "Elevated",
    "Stressed",
}

VALID_CONFIDENCE = {
    "Low",
    "Moderate",
    "High",
}


def test_factor_registry_not_empty():
    assert FACTOR_REGISTRY


def test_factor_keys_are_unique():
    keys = [
        factor.key
        for factor in FACTOR_REGISTRY
    ]

    assert len(keys) == len(set(keys))


def test_factor_display_names_are_unique():
    names = [
        factor.display_name
        for factor in FACTOR_REGISTRY
    ]

    assert len(names) == len(set(names))


def test_factor_lookup_matches_registry():
    assert len(FACTOR_BY_KEY) == len(
        FACTOR_REGISTRY
    )

    for factor in FACTOR_REGISTRY:
        assert FACTOR_BY_KEY[factor.key] is factor


def test_all_registered_factors_build_assessments():
    for factor in FACTOR_REGISTRY:

        assessment = factor.assessor()

        assert isinstance(
            assessment,
            Assessment,
        )

        assert (
            assessment.category
            == factor.display_name
        )

        assert (
            assessment.verdict
            in VALID_VERDICTS
        )

        assert (
            assessment.confidence
            in VALID_CONFIDENCE
        )

        assert assessment.summary
        assert assessment.summary.strip()


def test_expected_five_factors_registered():
    expected = {
        "funding",
        "system_liquidity",
        "repo_market",
        "treasury_intermediation",
        "treasury_market_activity",
    }

    actual = {
        factor.key
        for factor in FACTOR_REGISTRY
    }

    assert actual == expected
