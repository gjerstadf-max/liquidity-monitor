from backend.api.routes import (
    _assessment_factors,
)
from backend.assessments.engine import (
    build_liquidity_assessment,
)
from backend.services.daily_snapshot import (
    build_daily_snapshot,
)


EXPECTED_FACTOR_KEYS = {
    "funding",
    "system_liquidity",
    "repo_market",
    "treasury_intermediation",
    "treasury_market_activity",
    "commercial_paper",
}


def test_assessment_engine_builds_all_registered_factors():
    assessment = (
        build_liquidity_assessment()
    )

    keys = {
        factor.key
        for factor
        in assessment.factors
    }

    assert keys == EXPECTED_FACTOR_KEYS
    assert len(assessment.factors) == 6

    assert assessment.overall_verdict in {
        "Normal",
        "Watch",
        "Elevated",
        "Stressed",
    }

    assert assessment.confidence in {
        "Low",
        "Moderate",
        "High",
    }

    assert assessment.summary
    assert assessment.summary.strip()


def test_daily_snapshot_preserves_all_factors():
    """
    The daily snapshot must reuse the complete
    registered-factor assessment.
    """

    snapshot = build_daily_snapshot(
        include_news=False
    )

    keys = {
        factor.key
        for factor
        in snapshot.assessment.factors
    }

    assert keys == EXPECTED_FACTOR_KEYS
    assert len(
        snapshot.assessment.factors
    ) == 6

    assert snapshot.morning_brief is not None


def test_api_factor_serialization_includes_all_factors():
    """
    Verify the generic API serializer exposes every
    registered factor without factor-specific wiring.
    """

    assessment = (
        build_liquidity_assessment()
    )

    serialized = (
        _assessment_factors(
            assessment
        )
    )

    assert set(
        serialized.keys()
    ) == EXPECTED_FACTOR_KEYS

    treasury = serialized[
        "treasury_market_activity"
    ]

    assert treasury["verdict"] in {
        "Normal",
        "Watch",
        "Elevated",
        "Stressed",
    }

    assert treasury["confidence"] in {
        "Low",
        "Moderate",
        "High",
    }

    assert treasury["summary"]
