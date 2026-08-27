from datetime import date

from backend.metrics.treasury_market_activity import (
    latest_treasury_market_snapshot,
    treasury_auction_absorption_statistics,
    treasury_bill_supply_statistics,
)
from backend.signals.treasury_market_activity import (
    build_treasury_market_activity_diagnostics,
    evaluate_treasury_market_activity_signal,
)


REFERENCE_DATE = date(2026, 8, 26)


def test_treasury_supply_reference_date():
    result = treasury_bill_supply_statistics(
        as_of_date=REFERENCE_DATE
    )

    assert result.observation_date == REFERENCE_DATE
    assert result.gross_supply_billions == 2244.0
    assert result.regular_supply_billions == 2244.0
    assert result.cmb_supply_billions == 0.0

    assert (
        result.trailing_52_week_percentile
        == 100.0
    )

    assert round(
        result.trailing_52_week_zscore,
        2,
    ) == 1.83


def test_treasury_absorption_reference_date():
    result = (
        treasury_auction_absorption_statistics(
            as_of_date=REFERENCE_DATE
        )
    )

    assert result.auctions_used == 25

    assert round(
        result.offering_amount_billions,
        1,
    ) == 2244.0

    assert round(
        result.current_pressure,
        2,
    ) == -0.04

    assert round(
        result.historical_percentile,
        1,
    ) == 49.6

    assert round(
        result.historical_zscore,
        2,
    ) == -0.02


def test_treasury_iorb_reference_date():
    result = latest_treasury_market_snapshot(
        as_of_date=REFERENCE_DATE
    )

    assert result.observation_date == date(
        2026,
        8,
        24,
    )

    assert result.treasury_3m_percent == 3.87
    assert result.iorb_percent == 3.65

    assert round(
        result.spread_bp,
        1,
    ) == 22.0


def test_treasury_market_activity_signal():
    signal = (
        evaluate_treasury_market_activity_signal(
            as_of_date=REFERENCE_DATE
        )
    )

    assert signal.category == (
        "Treasury Market Activity"
    )

    assert signal.severity == "Watch"

    assert (
        "absorbed normally"
        in signal.title.lower()
    )


def test_treasury_market_activity_diagnostics():
    diagnostics = (
        build_treasury_market_activity_diagnostics(
            as_of_date=REFERENCE_DATE
        )
    )

    assert round(
        diagnostics.supply_z_52w,
        2,
    ) == 1.83

    assert round(
        diagnostics.absorption_z,
        2,
    ) == -0.02

    assert round(
        diagnostics.treasury_iorb_spread_bp,
        1,
    ) == 22.0
