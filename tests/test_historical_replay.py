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

from backend.commentary.anomaly_context import (
    build_anomaly_diagnostics,
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
def test_historical_replay_detects_treasury_iorb_anomaly():
    diagnostics = build_anomaly_diagnostics(
        as_of_date=date(2026, 9, 15)
    )

    assert len(diagnostics) == 1

    diagnostic = diagnostics[0]

    assert (
        diagnostic["type"]
        == "treasury_iorb_relative_pricing"
    )
    assert diagnostic["spread_bp"] == 46.0
    assert diagnostic["zscore"] == 3.65
    assert diagnostic["percentile"] == 100.0
    assert diagnostic["treasury_change_5d_bp"] == 17.0
    assert diagnostic["iorb_change_5d_bp"] == 0.0
    assert diagnostic["consecutive_above_95th"] == 4
    assert diagnostic["consecutive_above_99th"] == 3
    assert diagnostic["primary_mover"] == "treasury_3m"


def test_historical_replay_skips_normal_treasury_iorb_reading():
    diagnostics = build_anomaly_diagnostics(
        as_of_date=date(2026, 9, 21)
    )

    assert diagnostics == []
