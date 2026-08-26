from __future__ import annotations

from dataclasses import dataclass

from datetime import date

from decimal import Decimal

from statistics import mean, pstdev

from sqlalchemy import select
from collections import defaultdict
from datetime import date, timedelta, datetime
from zoneinfo import ZoneInfo

from backend.database.connection import (
    get_session,
)
from backend.database.models import (
    Indicator,
    Observation,
    TreasuryAuctionRecord,
)


# =============================================================
# DATA OBJECTS
# =============================================================


@dataclass(frozen=True)
class TreasuryMarketSnapshot:
    """
    Current Treasury market relative-pricing snapshot.

    The Treasury 3-month yield and IORB are always
    aligned on the same observation date.
    """

    observation_date: date
    previous_observation_date: date

    treasury_3m: Decimal
    previous_treasury_3m: Decimal
    treasury_3m_change_bp: Decimal

    iorb: Decimal
    previous_iorb: Decimal
    iorb_change_bp: Decimal

    treasury_iorb_spread_bp: Decimal
    previous_treasury_iorb_spread_bp: Decimal
    spread_change_bp: Decimal


@dataclass(frozen=True)
class TreasuryMarketSpreadStatistics:
    """
    Historical context for the 3-month Treasury
    yield relative to IORB.
    """

    observation_date: date
    observations_used: int

    current_spread_bp: Decimal

    average_30d_bp: Decimal
    average_60d_bp: Decimal

    minimum_60d_bp: Decimal
    maximum_60d_bp: Decimal

    percentile_60d: float
    zscore_60d: float


# =============================================================
# COMMON-DATE HISTORY
# =============================================================


def _load_common_rate_history(
    as_of_date: date | None = None,
) -> list[
    tuple[
        date,
        Decimal,
        Decimal,
    ]
]:
    """
    Return common Treasury 3-month / IORB observations
    sorted newest first.

    Each tuple contains:

        observation_date
        Treasury 3-month yield
        IORB

    Rates are matched strictly on observation date.

    This prevents a future effective IORB observation
    from being paired with an older Treasury market
    observation.

    If as_of_date is supplied, only common observations
    on or before that date are returned.
    """

    with get_session() as session:

        treasury_rows = session.scalars(
            select(
                Observation
            )
            .join(
                Indicator
            )
            .where(
                Indicator.symbol
                == "treasury_3m"
            )
            .order_by(
                Observation.observation_date.desc()
            )
        ).all()

        iorb_rows = session.scalars(
            select(
                Observation
            )
            .join(
                Indicator
            )
            .where(
                Indicator.symbol
                == "iorb"
            )
            .order_by(
                Observation.observation_date.desc()
            )
        ).all()

    if not treasury_rows:
        raise RuntimeError(
            "3-month Treasury observations "
            "not found."
        )

    if not iorb_rows:
        raise RuntimeError(
            "IORB observations not found."
        )

    treasury_by_date = {
        row.observation_date:
            row.value

        for row
        in treasury_rows
    }

    iorb_by_date = {
        row.observation_date:
            row.value

        for row
        in iorb_rows
    }

    common_dates = (
        set(treasury_by_date)
        & set(iorb_by_date)
    )

    if as_of_date is not None:
        common_dates = {
            observation_date

            for observation_date
            in common_dates

            if observation_date
            <= as_of_date
        }

    common_dates = sorted(
        common_dates,
        reverse=True,
    )

    if not common_dates:
        raise RuntimeError(
            "No common 3-month Treasury / IORB "
            "observation dates found."
        )

    return [
        (
            observation_date,

            treasury_by_date[
                observation_date
            ],

            iorb_by_date[
                observation_date
            ],
        )

        for observation_date
        in common_dates
    ]

REGULAR_BILL_TERMS = (
    "4-Week",
    "6-Week",
    "8-Week",
    "13-Week",
    "17-Week",
    "26-Week",
    "52-Week",
)

TREASURY_HISTORY_START = date(
    2021,
    7,
    29,
)


def _market_today() -> date:
    return datetime.now(
        ZoneInfo(
            "America/New_York"
        )
    ).date()


def _percentile(
    current: float,
    values: list[float],
) -> float:
    return (
        sum(
            1
            for value in values
            if value <= current
        )
        / len(values)
        * 100.0
    )


def _zscore(
    current: float,
    values: list[float],
) -> float:
    std = pstdev(
        values
    )

    if std == 0:
        return 0.0

    return (
        current
        - mean(values)
    ) / std

# =============================================================
# CURRENT SNAPSHOT
# =============================================================


def latest_treasury_market_snapshot(
    as_of_date: date | None = None,
) -> TreasuryMarketSnapshot:
    """
    Return the latest Treasury market relative-pricing
    snapshot available on or before as_of_date.

    If as_of_date is None, the latest common observation
    date is used.
    """

    history = (
        _load_common_rate_history(
            as_of_date=
                as_of_date
        )
    )

    if len(history) < 2:
        raise RuntimeError(
            "At least two common Treasury 3-month / "
            "IORB observation dates are required."
        )

    (
        current_date,
        treasury_3m,
        iorb,
    ) = history[0]

    (
        previous_date,
        previous_treasury_3m,
        previous_iorb,
    ) = history[1]

    treasury_change_bp = (
        treasury_3m
        - previous_treasury_3m
    ) * Decimal(
        "100"
    )

    iorb_change_bp = (
        iorb
        - previous_iorb
    ) * Decimal(
        "100"
    )

    spread = (
        treasury_3m
        - iorb
    ) * Decimal(
        "100"
    )

    previous_spread = (
        previous_treasury_3m
        - previous_iorb
    ) * Decimal(
        "100"
    )

    return TreasuryMarketSnapshot(
        observation_date=
            current_date,

        previous_observation_date=
            previous_date,

        treasury_3m=
            treasury_3m,

        previous_treasury_3m=
            previous_treasury_3m,

        treasury_3m_change_bp=
            treasury_change_bp,

        iorb=
            iorb,

        previous_iorb=
            previous_iorb,

        iorb_change_bp=
            iorb_change_bp,

        treasury_iorb_spread_bp=
            spread,

        previous_treasury_iorb_spread_bp=
            previous_spread,

        spread_change_bp=
            spread
            - previous_spread,
    )


# =============================================================
# HISTORICAL STATISTICS
# =============================================================


def treasury_market_spread_statistics(
    lookback: int = 60,
    as_of_date: date | None = None,
) -> TreasuryMarketSpreadStatistics:
    """
    Calculate historical context for the spread between
    the 3-month Treasury yield and IORB.

    Spread values are expressed in basis points.

    Positive spread:
        Treasury 3-month yield is above IORB.

    Negative spread:
        Treasury 3-month yield is below IORB.

    If as_of_date is supplied, only observations on or
    before that date are used.
    """

    if lookback < 2:
        raise ValueError(
            "lookback must be at least 2"
        )

    history = (
        _load_common_rate_history(
            as_of_date=
                as_of_date
        )
    )

    selected = history[
        :lookback
    ]

    if len(selected) < 2:
        raise RuntimeError(
            "At least two common observations are "
            "required for Treasury market spread "
            "statistics."
        )

    spreads = [
        (
            treasury_3m
            - iorb
        ) * Decimal(
            "100"
        )

        for (
            _,
            treasury_3m,
            iorb,
        )
        in selected
    ]

    current_spread = (
        spreads[0]
    )

    last_30 = (
        spreads[:30]
    )

    average_30 = (
        sum(
            last_30,
            Decimal("0"),
        )
        / Decimal(
            len(last_30)
        )
    )

    average_60 = (
        sum(
            spreads,
            Decimal("0"),
        )
        / Decimal(
            len(spreads)
        )
    )

    minimum = min(
        spreads
    )

    maximum = max(
        spreads
    )

    observations_at_or_below_current = sum(
        1

        for value
        in spreads

        if value
        <= current_spread
    )

    percentile = (
        observations_at_or_below_current
        / len(spreads)
        * 100.0
    )

    spread_floats = [
        float(value)

        for value
        in spreads
    ]

    spread_mean = mean(
        spread_floats
    )

    spread_std = pstdev(
        spread_floats
    )

    if spread_std == 0:
        zscore = 0.0

    else:
        zscore = (
            float(
                current_spread
            )
            - spread_mean
        ) / spread_std

    return TreasuryMarketSpreadStatistics(
        observation_date=
            selected[0][0],

        observations_used=
            len(selected),

        current_spread_bp=
            current_spread,

        average_30d_bp=
            average_30,

        average_60d_bp=
            average_60,

        minimum_60d_bp=
            minimum,

        maximum_60d_bp=
            maximum,

        percentile_60d=
            percentile,

        zscore_60d=
            zscore,
    )
@dataclass(frozen=True)
class TreasuryBillSupplyStatistics:
    observation_date: date
    window_days: int

    gross_supply_billions: float
    regular_supply_billions: float
    cmb_supply_billions: float

    observations_used: int

    historical_average_billions: float
    historical_minimum_billions: float
    historical_maximum_billions: float
    historical_percentile: float
    historical_zscore: float

    trailing_52_week_average_billions: float
    trailing_52_week_minimum_billions: float
    trailing_52_week_maximum_billions: float
    trailing_52_week_percentile: float
    trailing_52_week_zscore: float


@dataclass(frozen=True)
class TreasuryAuctionAbsorptionStatistics:
    observation_date: date
    window_days: int

    auctions_used: int
    offering_amount_billions: float

    current_pressure: float

    observations_used: int
    historical_average: float
    historical_minimum: float
    historical_maximum: float
    historical_percentile: float
    historical_zscore: float
def treasury_bill_supply_statistics(
    window_days: int = 28,
    as_of_date: date | None = None,
) -> TreasuryBillSupplyStatistics:
    """
    Measure gross Treasury bill supply settling during
    the trailing window.

    Gross supply includes regular bills and CMBs.

    The metric intentionally does not subtract maturing
    bills. It measures the market's gross absorption
    burden rather than duplicating System Liquidity.
    """

    if window_days < 1:
        raise ValueError(
            "window_days must be at least 1"
        )

    if as_of_date is None:
        as_of_date = (
            _market_today()
        )

    with get_session() as session:

        rows = session.execute(
            select(
                TreasuryAuctionRecord.issue_date,
                TreasuryAuctionRecord.offering_amount_dollars,
                TreasuryAuctionRecord.cash_management_bill,
            )
            .where(
                TreasuryAuctionRecord.offering_amount_dollars
                .is_not(None)
            )
            .where(
                TreasuryAuctionRecord.issue_date
                >= TREASURY_HISTORY_START
            )
            .where(
                TreasuryAuctionRecord.issue_date
                <= as_of_date
            )
            .order_by(
                TreasuryAuctionRecord.issue_date
            )
        ).all()

    if not rows:
        raise RuntimeError(
            "Treasury bill auction history "
            "not found."
        )

    records = [
        (
            issue_date,
            float(amount)
            / 1_000_000_000,
            bool(is_cmb),
        )
        for (
            issue_date,
            amount,
            is_cmb,
        )
        in rows
    ]

    def rolling_supply(
        observation_date: date,
        cmb_filter: bool | None = None,
    ) -> float:

        start_date = (
            observation_date
            - timedelta(
                days=window_days - 1
            )
        )

        return sum(
            amount_billions

            for (
                issue_date,
                amount_billions,
                is_cmb,
            )
            in records

            if (
                start_date
                <= issue_date
                <= observation_date
            )
            and (
                cmb_filter is None
                or is_cmb == cmb_filter
            )
        )

    first_date = (
        TREASURY_HISTORY_START
        + timedelta(
            days=window_days - 1
        )
    )

    offset = (
        as_of_date.weekday()
        - first_date.weekday()
    ) % 7

    sample_date = (
        first_date
        + timedelta(
            days=offset
        )
    )

    history: list[
        tuple[date, float]
    ] = []

    while sample_date <= as_of_date:

        history.append(
            (
                sample_date,
                rolling_supply(
                    sample_date
                ),
            )
        )

        sample_date += timedelta(
            days=7
        )

    if (
        not history
        or history[-1][0]
        != as_of_date
    ):
        history.append(
            (
                as_of_date,
                rolling_supply(
                    as_of_date
                ),
            )
        )

    values = [
        value
        for _, value
        in history
    ]

    current = values[-1]

    trailing_52 = (
        values[-52:]
    )

    return TreasuryBillSupplyStatistics(
        observation_date=
            as_of_date,

        window_days=
            window_days,

        gross_supply_billions=
            current,

        regular_supply_billions=
            rolling_supply(
                as_of_date,
                cmb_filter=False,
            ),

        cmb_supply_billions=
            rolling_supply(
                as_of_date,
                cmb_filter=True,
            ),

        observations_used=
            len(values),

        historical_average_billions=
            mean(values),

        historical_minimum_billions=
            min(values),

        historical_maximum_billions=
            max(values),

        historical_percentile=
            _percentile(
                current,
                values,
            ),

        historical_zscore=
            _zscore(
                current,
                values,
            ),

        trailing_52_week_average_billions=
            mean(trailing_52),

        trailing_52_week_minimum_billions=
            min(trailing_52),

        trailing_52_week_maximum_billions=
            max(trailing_52),

        trailing_52_week_percentile=
            _percentile(
                current,
                trailing_52,
            ),

        trailing_52_week_zscore=
            _zscore(
                current,
                trailing_52,
            ),
    )
def treasury_auction_absorption_statistics(
    window_days: int = 28,
    lookback: int = 52,
    minimum_history: int = 20,
    as_of_date: date | None = None,
) -> TreasuryAuctionAbsorptionStatistics:
    """
    Measure Treasury bill auction absorption pressure.

    Each regular bill auction is compared only with
    prior auctions of the same tenor.

    Lower bid-to-cover increases pressure.
    Higher primary-dealer take-down increases pressure.

    Auction pressure is:

        (-BTC z-score + dealer-share z-score) / 2

    The current window is weighted by offering amount.

    Positive values indicate weaker absorption.
    Negative values indicate stronger absorption.
    """

    if as_of_date is None:
        as_of_date = (
            _market_today()
        )

    with get_session() as session:

        rows = session.scalars(
            select(
                TreasuryAuctionRecord
            )
            .where(
                TreasuryAuctionRecord.cash_management_bill
                == False
            )
            .where(
                TreasuryAuctionRecord.bid_to_cover_ratio
                .is_not(None)
            )
            .where(
                TreasuryAuctionRecord.competitive_accepted_dollars
                .is_not(None)
            )
            .where(
                TreasuryAuctionRecord.primary_dealer_accepted_dollars
                .is_not(None)
            )
            .where(
                TreasuryAuctionRecord.offering_amount_dollars
                .is_not(None)
            )
            .where(
                TreasuryAuctionRecord.auction_date
                <= as_of_date
            )
            .order_by(
                TreasuryAuctionRecord.auction_date
            )
        ).all()

    history_by_term: dict[
        str,
        list[tuple[float, float]],
    ] = defaultdict(
        list
    )

    scored = []

    for row in rows:

        if (
            row.security_term
            not in REGULAR_BILL_TERMS
        ):
            continue

        competitive = float(
            row.competitive_accepted_dollars
        )

        if competitive <= 0:
            continue

        btc = float(
            row.bid_to_cover_ratio
        )

        dealer_share = (
            float(
                row.primary_dealer_accepted_dollars
            )
            / competitive
            * 100.0
        )

        offering = (
            float(
                row.offering_amount_dollars
            )
            / 1_000_000_000
        )

        prior = (
            history_by_term[
                row.security_term
            ][-lookback:]
        )

        if len(prior) >= minimum_history:

            btc_values = [
                item[0]
                for item
                in prior
            ]

            dealer_values = [
                item[1]
                for item
                in prior
            ]

            btc_z = (
                _zscore(
                    btc,
                    btc_values,
                )
            )

            dealer_z = (
                _zscore(
                    dealer_share,
                    dealer_values,
                )
            )

            pressure = (
                -btc_z
                + dealer_z
            ) / 2.0

            scored.append(
                (
                    row.auction_date,
                    offering,
                    pressure,
                )
            )

        history_by_term[
            row.security_term
        ].append(
            (
                btc,
                dealer_share,
            )
        )

    if not scored:
        raise RuntimeError(
            "No Treasury auctions have "
            "sufficient history for scoring."
        )

    def pressure_as_of(
        observation_date: date,
    ) -> tuple[
        float | None,
        int,
        float,
    ]:

        start_date = (
            observation_date
            - timedelta(
                days=window_days - 1
            )
        )

        selected = [
            item

            for item
            in scored

            if (
                start_date
                <= item[0]
                <= observation_date
            )
        ]

        if not selected:
            return (
                None,
                0,
                0.0,
            )

        total_offering = sum(
            item[1]
            for item
            in selected
        )

        if total_offering == 0:
            return (
                None,
                0,
                0.0,
            )

        pressure = (
            sum(
                offering
                * auction_pressure

                for (
                    _,
                    offering,
                    auction_pressure,
                )
                in selected
            )
            / total_offering
        )

        return (
            pressure,
            len(selected),
            total_offering,
        )

    first_scored_date = (
        scored[0][0]
    )

    first_sample_date = (
        first_scored_date
        + timedelta(
            days=window_days - 1
        )
    )

    offset = (
        as_of_date.weekday()
        - first_sample_date.weekday()
    ) % 7

    sample_date = (
        first_sample_date
        + timedelta(
            days=offset
        )
    )

    history: list[
        tuple[date, float]
    ] = []

    while sample_date <= as_of_date:

        pressure, _, _ = (
            pressure_as_of(
                sample_date
            )
        )

        if pressure is not None:

            history.append(
                (
                    sample_date,
                    pressure,
                )
            )

        sample_date += timedelta(
            days=7
        )

    (
        current,
        auctions_used,
        offering_billions,
    ) = pressure_as_of(
        as_of_date
    )

    if current is None:
        raise RuntimeError(
            "No scored Treasury auctions "
            "available in current window."
        )

    if (
        not history
        or history[-1][0]
        != as_of_date
    ):
        history.append(
            (
                as_of_date,
                current,
            )
        )

    values = [
        value
        for _, value
        in history
    ]

    return TreasuryAuctionAbsorptionStatistics(
        observation_date=
            as_of_date,

        window_days=
            window_days,

        auctions_used=
            auctions_used,

        offering_amount_billions=
            offering_billions,

        current_pressure=
            current,

        observations_used=
            len(values),

        historical_average=
            mean(values),

        historical_minimum=
            min(values),

        historical_maximum=
            max(values),

        historical_percentile=
            _percentile(
                current,
                values,
            ),

        historical_zscore=
            _zscore(
                current,
                values,
            ),
    )

# =============================================================
# TERMINAL DISPLAY
# =============================================================


def print_treasury_market_activity(
    as_of_date: date | None = None,
) -> None:
    """
    Print the current Treasury market relative-pricing
    diagnostics.
    """

    snapshot = (
        latest_treasury_market_snapshot(
            as_of_date=
                as_of_date
        )
    )

    stats = (
        treasury_market_spread_statistics(
            lookback=60,
            as_of_date=
                as_of_date,
        )
    )

    print()

    print(
        "TREASURY MARKET ACTIVITY"
    )

    print(
        "=" * 72
    )

    print()

    print(
        "Observation date:"
    )

    print(
        f"  {snapshot.observation_date}"
    )

    print()

    print(
        "3-Month Treasury:"
    )

    print(
        f"  {snapshot.treasury_3m:.2f}%"
    )

    print()

    print(
        "IORB:"
    )

    print(
        f"  {snapshot.iorb:.2f}%"
    )

    print()

    print(
        "Treasury 3M - IORB spread:"
    )

    print(
        f"  "
        f"{snapshot.treasury_iorb_spread_bp:+.1f} bp"
    )

    print()

    print(
        "Previous spread:"
    )

    print(
        f"  "
        f"{snapshot.previous_treasury_iorb_spread_bp:+.1f} bp"
    )

    print()

    print(
        "Spread change:"
    )

    print(
        f"  "
        f"{snapshot.spread_change_bp:+.1f} bp"
    )

    print()

    print(
        "60-observation context:"
    )

    print(
        f"  Average: "
        f"{stats.average_60d_bp:+.1f} bp"
    )

    print(
        f"  Minimum: "
        f"{stats.minimum_60d_bp:+.1f} bp"
    )

    print(
        f"  Maximum: "
        f"{stats.maximum_60d_bp:+.1f} bp"
    )

    print(
        f"  Percentile: "
        f"{stats.percentile_60d:.1f}"
    )

    print(
        f"  Z-score: "
        f"{stats.zscore_60d:+.2f}"
    )

    print()


# =============================================================
# DIRECT EXECUTION
# =============================================================


if __name__ == "__main__":
    print_treasury_market_activity()