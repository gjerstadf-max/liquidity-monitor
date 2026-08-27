from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from statistics import mean, pstdev
from zoneinfo import ZoneInfo

from sqlalchemy import select

from backend.database.connection import get_session
from backend.database.models import (
    Indicator,
    Observation,
    TreasuryAuctionRecord,
)


# =============================================================
# CONSTANTS
# =============================================================


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


TREASURY_3M_SYMBOL = (
    "treasury_3m"
)


IORB_SYMBOL = (
    "iorb"
)


# =============================================================
# DATA OBJECTS
# =============================================================


@dataclass(frozen=True)
class TreasuryMarketSnapshot:
    """
    Latest common-date Treasury 3M / IORB observation.
    """

    observation_date: date

    treasury_3m_percent: float

    iorb_percent: float

    spread_bp: float

    previous_spread_bp: float | None

    change_bp: float | None


@dataclass(frozen=True)
class TreasuryMarketSpreadStatistics:
    """
    Statistical context for the Treasury 3M - IORB spread.
    """

    observation_date: date

    lookback: int

    observations_used: int

    current_spread_bp: float

    previous_spread_bp: float | None

    change_bp: float | None

    average_spread_bp: float

    minimum_spread_bp: float

    maximum_spread_bp: float

    percentile: float

    zscore: float

    # ---------------------------------------------------------
    # COMPATIBILITY PROPERTIES
    # ---------------------------------------------------------
    #
    # These preserve the original interface used by the
    # Factor #5 signal code while allowing lookback to vary.
    #
    # ---------------------------------------------------------

    @property
    def average_60d_bp(
        self,
    ) -> float:
        return self.average_spread_bp

    @property
    def minimum_60d_bp(
        self,
    ) -> float:
        return self.minimum_spread_bp

    @property
    def maximum_60d_bp(
        self,
    ) -> float:
        return self.maximum_spread_bp

    @property
    def percentile_60d(
        self,
    ) -> float:
        return self.percentile

    @property
    def zscore_60d(
        self,
    ) -> float:
        return self.zscore


@dataclass(frozen=True)
class TreasuryBillSupplyStatistics:
    """
    Trailing gross Treasury bill supply.

    Supply is measured using issue_date because settlement
    is when investors fund Treasury purchases.

    Gross supply includes both regular bills and CMBs.
    """

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
    """
    Treasury bill auction absorption pressure.

    Positive pressure means weaker absorption.

    Negative pressure means stronger absorption.
    """

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


# =============================================================
# GENERAL HELPERS
# =============================================================


def _market_today() -> date:
    """
    Return the current Treasury-market calendar date.

    Cloud Run operates in UTC, so explicitly use
    America/New_York rather than date.today().
    """

    return datetime.now(
        ZoneInfo(
            "America/New_York"
        )
    ).date()


def _percentile(
    current: float,
    values: list[float],
) -> float:
    """
    Empirical percentile of current within values.
    """

    if not values:
        raise ValueError(
            "Cannot calculate percentile "
            "from an empty list."
        )

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
    """
    Population z-score of current within values.
    """

    if not values:
        raise ValueError(
            "Cannot calculate z-score "
            "from an empty list."
        )

    average = mean(
        values
    )

    standard_deviation = pstdev(
        values
    )

    if standard_deviation == 0:
        return 0.0

    return (
        current
        - average
    ) / standard_deviation


# =============================================================
# FRED SERIES HELPERS
# =============================================================


def _load_indicator_history(
    symbol: str,
    as_of_date: date | None = None,
) -> list[
    tuple[
        date,
        float,
    ]
]:
    """
    Load observation history for a scalar indicator.
    """

    with get_session() as session:

        indicator = session.scalar(
            select(
                Indicator
            )
            .where(
                Indicator.symbol
                == symbol
            )
        )

        if indicator is None:
            raise RuntimeError(
                f"Indicator not found: {symbol}"
            )

        statement = (
            select(
                Observation.observation_date,
                Observation.value,
            )
            .where(
                Observation.indicator_id
                == indicator.id
            )
        )

        if as_of_date is not None:

            statement = (
                statement.where(
                    Observation.observation_date
                    <= as_of_date
                )
            )

        statement = statement.order_by(
            Observation.observation_date
        )

        rows = session.execute(
            statement
        ).all()

    return [
        (
            observation_date,
            float(value),
        )
        for (
            observation_date,
            value,
        )
        in rows
        if value is not None
    ]


def _load_common_rate_history(
    as_of_date: date | None = None,
) -> list[
    tuple[
        date,
        float,
        float,
        float,
    ]
]:
    """
    Load Treasury 3M and IORB strictly on common
    observation dates.

    Returns:

        (
            observation_date,
            treasury_3m_percent,
            iorb_percent,
            spread_bp,
        )

    This strict common-date alignment prevents a future
    effective administered IORB observation from being
    combined with an older Treasury market observation.
    """

    treasury_history = (
        _load_indicator_history(
            TREASURY_3M_SYMBOL,
            as_of_date=
                as_of_date,
        )
    )

    iorb_history = (
        _load_indicator_history(
            IORB_SYMBOL,
            as_of_date=
                as_of_date,
        )
    )

    treasury_by_date = {
        observation_date:
            value

        for (
            observation_date,
            value,
        )
        in treasury_history
    }

    iorb_by_date = {
        observation_date:
            value

        for (
            observation_date,
            value,
        )
        in iorb_history
    }

    common_dates = sorted(
        set(
            treasury_by_date
        )
        & set(
            iorb_by_date
        )
    )

    if not common_dates:
        raise RuntimeError(
            "No common observation dates found "
            "for Treasury 3M and IORB."
        )

    history = []

    for observation_date in common_dates:

        treasury_rate = (
            treasury_by_date[
                observation_date
            ]
        )

        iorb_rate = (
            iorb_by_date[
                observation_date
            ]
        )

        spread_bp = (
            treasury_rate
            - iorb_rate
        ) * 100.0

        history.append(
            (
                observation_date,
                treasury_rate,
                iorb_rate,
                spread_bp,
            )
        )

    return history


# =============================================================
# TREASURY 3M - IORB
# =============================================================


def latest_treasury_market_snapshot(
    as_of_date: date | None = None,
) -> TreasuryMarketSnapshot:
    """
    Return the latest common-date Treasury 3M / IORB
    observation and change from the prior common date.
    """

    history = (
        _load_common_rate_history(
            as_of_date=
                as_of_date
        )
    )

    (
        observation_date,
        treasury_rate,
        iorb_rate,
        spread_bp,
    ) = history[-1]

    previous_spread_bp = None
    change_bp = None

    if len(history) >= 2:

        previous_spread_bp = (
            history[-2][3]
        )

        change_bp = (
            spread_bp
            - previous_spread_bp
        )

    return TreasuryMarketSnapshot(
        observation_date=
            observation_date,

        treasury_3m_percent=
            treasury_rate,

        iorb_percent=
            iorb_rate,

        spread_bp=
            spread_bp,

        previous_spread_bp=
            previous_spread_bp,

        change_bp=
            change_bp,
    )


def treasury_market_spread_statistics(
    lookback: int = 60,
    as_of_date: date | None = None,
) -> TreasuryMarketSpreadStatistics:
    """
    Statistical context for Treasury 3M - IORB.

    This is a supporting Factor #5 indicator rather than
    a core supply signal because the spread is also
    influenced by monetary-policy expectations.
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

    if len(history) < 2:
        raise RuntimeError(
            "At least two common Treasury 3M / IORB "
            "observations are required."
        )

    trailing = (
        history[
            -lookback:
        ]
    )

    values = [
        row[3]
        for row in trailing
    ]

    current = (
        values[-1]
    )

    previous = (
        history[-2][3]
    )

    return TreasuryMarketSpreadStatistics(
        observation_date=
            history[-1][0],

        lookback=
            lookback,

        observations_used=
            len(values),

        current_spread_bp=
            current,

        previous_spread_bp=
            previous,

        change_bp=
            current
            - previous,

        average_spread_bp=
            mean(values),

        minimum_spread_bp=
            min(values),

        maximum_spread_bp=
            max(values),

        percentile=
            _percentile(
                current,
                values,
            ),

        zscore=
            _zscore(
                current,
                values,
            ),
    )


# =============================================================
# TREASURY BILL SUPPLY
# =============================================================


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
            float(
                amount
            )
            / 1_000_000_000,
            bool(
                is_cmb
            ),
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
                days=
                    window_days
                    - 1
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
                or is_cmb
                == cmb_filter
            )
        )

    first_date = (
        TREASURY_HISTORY_START
        + timedelta(
            days=
                window_days
                - 1
        )
    )

    if as_of_date < first_date:
        raise RuntimeError(
            "Insufficient Treasury bill history "
            "for the requested date."
        )

    # ---------------------------------------------------------
    # WEEKLY HISTORY
    #
    # Align historical observations to the same weekday as
    # as_of_date so weekday settlement patterns do not distort
    # the comparison.
    # ---------------------------------------------------------

    offset = (
        as_of_date.weekday()
        - first_date.weekday()
    ) % 7

    sample_date = (
        first_date
        + timedelta(
            days=
                offset
        )
    )

    history: list[
        tuple[
            date,
            float,
        ]
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

    if not values:
        raise RuntimeError(
            "No Treasury bill supply observations "
            "could be calculated."
        )

    current = (
        values[-1]
    )

    trailing_52 = (
        values[
            -52:
        ]
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
            mean(
                values
            ),

        historical_minimum_billions=
            min(
                values
            ),

        historical_maximum_billions=
            max(
                values
            ),

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
            mean(
                trailing_52
            ),

        trailing_52_week_minimum_billions=
            min(
                trailing_52
            ),

        trailing_52_week_maximum_billions=
            max(
                trailing_52
            ),

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


# =============================================================
# TREASURY AUCTION ABSORPTION
# =============================================================


def treasury_auction_absorption_statistics(
    window_days: int = 28,
    lookback: int = 52,
    minimum_history: int = 20,
    as_of_date: date | None = None,
) -> TreasuryAuctionAbsorptionStatistics:
    """
    Measure Treasury bill auction absorption pressure.

    Each regular bill auction is compared only with
    PRIOR auctions of the same tenor.

    Lower bid-to-cover increases pressure.

    Higher primary-dealer take-down increases pressure.

    Auction pressure:

        (
            - bid_to_cover_z
            + dealer_share_z
        ) / 2

    The current trailing window is weighted by each
    auction's offering amount.

    Positive values indicate weaker absorption.

    Negative values indicate stronger absorption.
    """

    if window_days < 1:
        raise ValueError(
            "window_days must be at least 1"
        )

    if lookback < 2:
        raise ValueError(
            "lookback must be at least 2"
        )

    if minimum_history < 2:
        raise ValueError(
            "minimum_history must be at least 2"
        )

    if minimum_history > lookback:
        raise ValueError(
            "minimum_history cannot exceed lookback"
        )

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
        list[
            tuple[
                float,
                float,
            ]
        ],
    ] = defaultdict(
        list
    )

    scored: list[
        tuple[
            date,
            float,
            float,
        ]
    ] = []

    # ---------------------------------------------------------
    # SCORE EACH AUCTION AGAINST PRIOR SAME-TENOR AUCTIONS
    # ---------------------------------------------------------

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
            ][
                -lookback:
            ]
        )

        if (
            len(
                prior
            )
            >= minimum_history
        ):

            prior_btc = [
                item[0]
                for item
                in prior
            ]

            prior_dealer = [
                item[1]
                for item
                in prior
            ]

            btc_z = (
                _zscore(
                    btc,
                    prior_btc,
                )
            )

            dealer_z = (
                _zscore(
                    dealer_share,
                    prior_dealer,
                )
            )

            # Lower BTC = more pressure.
            btc_pressure = (
                -btc_z
            )

            # Higher dealer take-down = more pressure.
            dealer_pressure = (
                dealer_z
            )

            pressure = (
                btc_pressure
                + dealer_pressure
            ) / 2.0

            scored.append(
                (
                    row.auction_date,
                    offering,
                    pressure,
                )
            )

        # -----------------------------------------------------
        # IMPORTANT
        #
        # Add the current auction to history only AFTER
        # scoring it. This avoids look-ahead contamination.
        # -----------------------------------------------------

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
            "No Treasury auctions have sufficient "
            "history for scoring."
        )

    # ---------------------------------------------------------
    # TRAILING WINDOW AGGREGATION
    # ---------------------------------------------------------

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
                days=
                    window_days
                    - 1
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

        if total_offering <= 0:

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
            len(
                selected
            ),
            total_offering,
        )

    # ---------------------------------------------------------
    # WEEKLY HISTORY
    # ---------------------------------------------------------

    first_scored_date = (
        scored[0][0]
    )

    first_sample_date = (
        first_scored_date
        + timedelta(
            days=
                window_days
                - 1
        )
    )

    if as_of_date < first_sample_date:
        raise RuntimeError(
            "Insufficient scored Treasury auction "
            "history for the requested date."
        )

    offset = (
        as_of_date.weekday()
        - first_sample_date.weekday()
    ) % 7

    sample_date = (
        first_sample_date
        + timedelta(
            days=
                offset
        )
    )

    history: list[
        tuple[
            date,
            float,
        ]
    ] = []

    while sample_date <= as_of_date:

        (
            pressure,
            _,
            _,
        ) = pressure_as_of(
            sample_date
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
            "No scored Treasury auctions are available "
            "in the current trailing window."
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
            len(
                values
            ),

        historical_average=
            mean(
                values
            ),

        historical_minimum=
            min(
                values
            ),

        historical_maximum=
            max(
                values
            ),

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
    Print all current Factor #5 metric diagnostics.
    """

    snapshot = (
        latest_treasury_market_snapshot(
            as_of_date=
                as_of_date
        )
    )

    pricing = (
        treasury_market_spread_statistics(
            lookback=60,
            as_of_date=
                as_of_date
        )
    )

    supply = (
        treasury_bill_supply_statistics(
            window_days=28,
            as_of_date=
                as_of_date
        )
    )

    absorption = (
        treasury_auction_absorption_statistics(
            window_days=28,
            lookback=52,
            minimum_history=20,
            as_of_date=
                as_of_date
        )
    )

    print()

    print(
        "TREASURY MARKET ACTIVITY"
    )

    print(
        "=" * 78
    )

    print()

    print(
        "SUPPLY LOAD"
    )

    print(
        "-" * 78
    )

    print(
        f"Observation date:      "
        f"{supply.observation_date}"
    )

    print(
        f"Gross 28-day supply:   "
        f"${supply.gross_supply_billions:,.1f}B"
    )

    print(
        f"Regular bills:         "
        f"${supply.regular_supply_billions:,.1f}B"
    )

    print(
        f"CMBs:                  "
        f"${supply.cmb_supply_billions:,.1f}B"
    )

    print(
        f"52-week percentile:    "
        f"{supply.trailing_52_week_percentile:.1f}"
    )

    print(
        f"52-week z-score:        "
        f"{supply.trailing_52_week_zscore:+.2f}"
    )

    print()

    print(
        "AUCTION ABSORPTION"
    )

    print(
        "-" * 78
    )

    print(
        f"Pressure:               "
        f"{absorption.current_pressure:+.2f}"
    )

    print(
        f"Historical percentile:  "
        f"{absorption.historical_percentile:.1f}"
    )

    print(
        f"Historical z-score:      "
        f"{absorption.historical_zscore:+.2f}"
    )

    print(
        f"Auctions used:          "
        f"{absorption.auctions_used}"
    )

    print(
        f"Offering amount:        "
        f"${absorption.offering_amount_billions:,.1f}B"
    )

    print()

    print(
        "RELATIVE PRICING — SUPPORTING"
    )

    print(
        "-" * 78
    )

    print(
        f"Observation date:       "
        f"{snapshot.observation_date}"
    )

    print(
        f"3-Month Treasury:       "
        f"{snapshot.treasury_3m_percent:.2f}%"
    )

    print(
        f"IORB:                   "
        f"{snapshot.iorb_percent:.2f}%"
    )

    print(
        f"Treasury 3M - IORB:     "
        f"{snapshot.spread_bp:+.1f} bp"
    )

    if snapshot.previous_spread_bp is not None:

        print(
            f"Previous spread:        "
            f"{snapshot.previous_spread_bp:+.1f} bp"
        )

    if snapshot.change_bp is not None:

        print(
            f"Change:                 "
            f"{snapshot.change_bp:+.1f} bp"
        )

    print(
        f"60-observation average: "
        f"{pricing.average_spread_bp:+.1f} bp"
    )

    print(
        f"60-observation range:   "
        f"{pricing.minimum_spread_bp:+.1f} to "
        f"{pricing.maximum_spread_bp:+.1f} bp"
    )

    print(
        f"60-observation pct:     "
        f"{pricing.percentile:.1f}"
    )

    print(
        f"60-observation z-score: "
        f"{pricing.zscore:+.2f}"
    )

    print()


# =============================================================
# DIRECT EXECUTION
# =============================================================


if __name__ == "__main__":
    print_treasury_market_activity()