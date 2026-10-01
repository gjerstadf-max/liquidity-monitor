from datetime import date

from backend.assessments.engine import (
    build_liquidity_assessment,
)
from backend.metrics.funding import (
    funding_spread_statistics,
)
from backend.metrics.system_liquidity import (
    system_liquidity_history_metrics,
    system_liquidity_metrics,
)


REPLAY_DATE = date(2026, 9, 15)


def test_funding_respects_historical_date():
    stats = funding_spread_statistics(
        as_of_date=REPLAY_DATE
    )

    assert stats.observation_date <= REPLAY_DATE

    assert stats.observation_date == date(
        2026,
        9,
        15,
    )


def test_system_liquidity_respects_historical_date():
    current = system_liquidity_metrics(
        as_of_date=REPLAY_DATE
    )

    history = system_liquidity_history_metrics(
        as_of_date=REPLAY_DATE
    )

    assert current.observation_date <= REPLAY_DATE

    assert current.observation_date == date(
        2026,
        9,
        9,
    )

    assert round(
        float(
            current.net_liquidity_proxy_billions
        ),
        1,
    ) == 2148.0

    assert round(
        float(
            history.four_week_change_billions
        ),
        1,
    ) == 162.7

    assert round(
        history.zscore_52_week,
        2,
    ) == 0.19


def test_full_assessment_replays_historical_state():
    assessment = build_liquidity_assessment(
        as_of_date=REPLAY_DATE
    )

    assert len(
        assessment.factors
    ) == 8

    factors = {
        factor.key: factor.assessment
        for factor in assessment.factors
    }

    assert (
        factors["funding"].verdict
        == "Normal"
    )

    assert (
        factors["system_liquidity"].verdict
        == "Normal"
    )

    assert (
        factors[
            "treasury_market_activity"
        ].verdict
        == "Normal"
    )

    assert (
        "+46 bp relative to IORB"
        in factors[
            "treasury_market_activity"
        ].summary
    )