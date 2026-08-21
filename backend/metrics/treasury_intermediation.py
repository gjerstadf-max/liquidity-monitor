from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from statistics import mean, pstdev

from sqlalchemy import select

from backend.database.connection import get_session
from backend.database.models import (
    Indicator,
    Observation,
)


# =============================================================
# DATA OBJECTS
# =============================================================


@dataclass(frozen=True)
class IntermediationSnapshot:
    observation_date: date

    dealer_positions_billions: Decimal
    treasury_transactions_billions: Decimal
    securities_borrowed_billions: Decimal

    fails_receive_billions: Decimal
    fails_deliver_billions: Decimal
    total_fails_billions: Decimal

    repo_billions: Decimal | None
    reverse_repo_billions: Decimal | None


@dataclass(frozen=True)
class MetricContext:
    current: Decimal

    change_1_week: Decimal
    change_4_week: Decimal
    change_13_week: Decimal

    average_13_week: Decimal
    average_26_week: Decimal
    average_52_week: Decimal

    minimum_52_week: Decimal
    maximum_52_week: Decimal

    percentile_52_week: float
    zscore_52_week: float


@dataclass(frozen=True)
class TreasuryIntermediationStatistics:
    observation_date: date
    observations_used: int

    dealer_positions: MetricContext
    treasury_transactions: MetricContext
    securities_borrowed: MetricContext

    fails_receive: MetricContext
    fails_deliver: MetricContext
    total_fails: MetricContext


# =============================================================
# DATABASE
# =============================================================


def _load_series(
    symbol: str,
) -> dict[date, Decimal]:
    """
    Load all observations for one indicator.

    Returns:
        {
            observation_date: value
        }
    """

    with get_session() as session:
        rows = session.scalars(
            select(Observation)
            .join(Indicator)
            .where(
                Indicator.symbol == symbol
            )
            .order_by(
                Observation.observation_date.asc()
            )
        ).all()

    if not rows:
        raise RuntimeError(
            f"No observations found for "
            f"{symbol.upper()}."
        )

    return {
        row.observation_date: row.value
        for row in rows
    }


# =============================================================
# HISTORY
# =============================================================


def _load_intermediation_history(
    as_of_date: date | None = None,
) -> list[IntermediationSnapshot]:
    """
    Build canonical Treasury Intermediation history.

    Core series:

    - Dealer Treasury positions
    - Treasury transactions
    - Treasury securities borrowed
    - Treasury fails to receive
    - Treasury fails to deliver

    Supporting series:

    - Treasury repo financing
    - Treasury reverse repo financing

    Supporting financing observations may be suppressed
    by the NY Fed. Missing values remain missing and are
    never converted to zero.

    When as_of_date is supplied, only observations on or
    before that date are used. This prevents look-ahead
    bias in historical replay.
    """

    positions = _load_series(
        "pd_treasury_positions"
    )

    transactions = _load_series(
        "pd_treasury_transactions"
    )

    borrowed = _load_series(
        "pd_treasury_borrowed"
    )

    fails_receive = _load_series(
        "pd_treasury_fails_receive"
    )

    fails_deliver = _load_series(
        "pd_treasury_fails_deliver"
    )

    repo = _load_series(
        "pd_treasury_repo"
    )

    reverse_repo = _load_series(
        "pd_treasury_reverse_repo"
    )

    # ---------------------------------------------------------
    # COMMON CORE DATES
    # ---------------------------------------------------------

    common_dates = (
        set(positions)
        & set(transactions)
        & set(borrowed)
        & set(fails_receive)
        & set(fails_deliver)
    )

    if as_of_date is not None:
        common_dates = {
            observation_date
            for observation_date in common_dates
            if observation_date <= as_of_date
        }

    if not common_dates:
        raise RuntimeError(
            "No common Treasury intermediation "
            "dates found."
        )

    history: list[
        IntermediationSnapshot
    ] = []

    for observation_date in sorted(
        common_dates
    ):
        transaction_value = (
            transactions[
                observation_date
            ]
        )

        fails_receive_value = (
            fails_receive[
                observation_date
            ]
        )

        fails_deliver_value = (
            fails_deliver[
                observation_date
            ]
        )

        total_fails = (
            fails_receive_value
            + fails_deliver_value
        )

        history.append(
            IntermediationSnapshot(
                observation_date=
                    observation_date,

                dealer_positions_billions=
                    positions[
                        observation_date
                    ],

                treasury_transactions_billions=
                    transaction_value,

                securities_borrowed_billions=
                    borrowed[
                        observation_date
                    ],

                fails_receive_billions=
                    fails_receive_value,

                fails_deliver_billions=
                    fails_deliver_value,

                total_fails_billions=
                    total_fails,

                repo_billions=
                    repo.get(
                        observation_date
                    ),

                reverse_repo_billions=
                    reverse_repo.get(
                        observation_date
                    ),
            )
        )

    return history


# =============================================================
# STATISTICS
# =============================================================


def _metric_context(
    values_ascending: list[
        Decimal
    ],
) -> MetricContext:
    """
    Calculate trailing statistical context.

    Input must be ordered oldest -> newest.

    Uses:
    - 1-week change
    - 4-week change
    - 13-week change
    - 13-week average
    - 26-week average
    - 52-week average
    - 52-week range
    - 52-week percentile
    - 52-week z-score
    """

    if len(
        values_ascending
    ) < 52:
        raise RuntimeError(
            "At least 52 weekly observations "
            "are required."
        )

    current = (
        values_ascending[
            -1
        ]
    )

    # ---------------------------------------------------------
    # HISTORICAL VALUE
    # ---------------------------------------------------------

    def historical_value(
        weeks_back: int,
    ) -> Decimal:
        if len(
            values_ascending
        ) <= weeks_back:
            return (
                values_ascending[
                    0
                ]
            )

        return (
            values_ascending[
                -(weeks_back + 1)
            ]
        )

    # ---------------------------------------------------------
    # CHANGES
    # ---------------------------------------------------------

    change_1_week = (
        current
        - historical_value(
            1
        )
    )

    change_4_week = (
        current
        - historical_value(
            4
        )
    )

    change_13_week = (
        current
        - historical_value(
            13
        )
    )

    # ---------------------------------------------------------
    # TRAILING WINDOWS
    # ---------------------------------------------------------

    last_13 = (
        values_ascending[
            -13:
        ]
    )

    last_26 = (
        values_ascending[
            -26:
        ]
    )

    last_52 = (
        values_ascending[
            -52:
        ]
    )

    # ---------------------------------------------------------
    # AVERAGES
    # ---------------------------------------------------------

    average_13 = (
        sum(
            last_13,
            Decimal("0"),
        )
        / Decimal(
            len(
                last_13
            )
        )
    )

    average_26 = (
        sum(
            last_26,
            Decimal("0"),
        )
        / Decimal(
            len(
                last_26
            )
        )
    )

    average_52 = (
        sum(
            last_52,
            Decimal("0"),
        )
        / Decimal(
            len(
                last_52
            )
        )
    )

    # ---------------------------------------------------------
    # RANGE
    # ---------------------------------------------------------

    minimum_52 = min(
        last_52
    )

    maximum_52 = max(
        last_52
    )

    # ---------------------------------------------------------
    # PERCENTILE
    # ---------------------------------------------------------

    observations_at_or_below = sum(
        1
        for value in last_52
        if value <= current
    )

    percentile_52 = (
        observations_at_or_below
        / len(
            last_52
        )
        * 100
    )

    # ---------------------------------------------------------
    # Z-SCORE
    # ---------------------------------------------------------

    float_values = [
        float(
            value
        )
        for value in last_52
    ]

    historical_mean = mean(
        float_values
    )

    historical_std = pstdev(
        float_values
    )

    if historical_std == 0:
        zscore = 0.0

    else:
        zscore = (
            float(
                current
            )
            - historical_mean
        ) / historical_std

    return MetricContext(
        current=
            current,

        change_1_week=
            change_1_week,

        change_4_week=
            change_4_week,

        change_13_week=
            change_13_week,

        average_13_week=
            average_13,

        average_26_week=
            average_26,

        average_52_week=
            average_52,

        minimum_52_week=
            minimum_52,

        maximum_52_week=
            maximum_52,

        percentile_52_week=
            percentile_52,

        zscore_52_week=
            zscore,
    )


# =============================================================
# PUBLIC FUNCTIONS
# =============================================================


def latest_treasury_intermediation_snapshot(
    as_of_date: date | None = None,
) -> IntermediationSnapshot:
    """
    Return the latest Treasury Intermediation snapshot
    available on or before as_of_date.
    """

    history = (
        _load_intermediation_history(
            as_of_date=
                as_of_date
        )
    )

    return (
        history[
            -1
        ]
    )


def treasury_intermediation_statistics(
    as_of_date: date | None = None,
) -> TreasuryIntermediationStatistics:
    """
    Calculate Treasury Intermediation diagnostics
    using only information available on or before
    as_of_date.

    No signal or verdict is produced here.
    """

    history = (
        _load_intermediation_history(
            as_of_date=
                as_of_date
        )
    )

    if len(
        history
    ) < 52:
        raise RuntimeError(
            "At least 52 common Treasury "
            "intermediation observations "
            "are required."
        )

    return TreasuryIntermediationStatistics(
        observation_date=
            history[
                -1
            ].observation_date,

        observations_used=
            len(
                history
            ),

        dealer_positions=
            _metric_context(
                [
                    item.dealer_positions_billions
                    for item in history
                ]
            ),

        treasury_transactions=
            _metric_context(
                [
                    item.treasury_transactions_billions
                    for item in history
                ]
            ),

        securities_borrowed=
            _metric_context(
                [
                    item.securities_borrowed_billions
                    for item in history
                ]
            ),

        fails_receive=
            _metric_context(
                [
                    item.fails_receive_billions
                    for item in history
                ]
            ),

        fails_deliver=
            _metric_context(
                [
                    item.fails_deliver_billions
                    for item in history
                ]
            ),

        total_fails=
            _metric_context(
                [
                    item.total_fails_billions
                    for item in history
                ]
            ),
    )


# =============================================================
# DISPLAY HELPERS
# =============================================================


def _print_metric(
    title: str,
    metric: MetricContext,
    units: str,
) -> None:
    """
    Print one metric in a terminal-friendly format.
    """

    print()
    print(
        title
    )

    print(
        "-" * 72
    )

    print(
        f"Current:       "
        f"{float(metric.current):,.2f} "
        f"{units}"
    )

    print(
        f"1-week change: "
        f"{float(metric.change_1_week):+,.2f} "
        f"{units}"
    )

    print(
        f"4-week change: "
        f"{float(metric.change_4_week):+,.2f} "
        f"{units}"
    )

    print(
        f"13-week change: "
        f"{float(metric.change_13_week):+,.2f} "
        f"{units}"
    )

    print(
        f"13-week avg:   "
        f"{float(metric.average_13_week):,.2f} "
        f"{units}"
    )

    print(
        f"26-week avg:   "
        f"{float(metric.average_26_week):,.2f} "
        f"{units}"
    )

    print(
        f"52-week avg:   "
        f"{float(metric.average_52_week):,.2f} "
        f"{units}"
    )

    print(
        f"52-week range: "
        f"{float(metric.minimum_52_week):,.2f} "
        f"to "
        f"{float(metric.maximum_52_week):,.2f} "
        f"{units}"
    )

    print(
        f"Percentile:    "
        f"{metric.percentile_52_week:.0f}"
    )

    print(
        f"Z-score:       "
        f"{metric.zscore_52_week:+.2f}"
    )


# =============================================================
# TERMINAL DIAGNOSTICS
# =============================================================


def print_treasury_intermediation_diagnostics(
) -> None:
    """
    Print latest Factor #4 diagnostics.

    This is intentionally diagnostic only.
    No signal thresholds or verdicts are applied.
    """

    snapshot = (
        latest_treasury_intermediation_snapshot()
    )

    statistics = (
        treasury_intermediation_statistics()
    )

    print()
    print(
        "Liquidity Monitor — "
        "Treasury Intermediation Diagnostics"
    )

    print(
        "=" * 72
    )

    print()

    print(
        f"Observation Date: "
        f"{snapshot.observation_date}"
    )

    print(
        f"Common Core Observations: "
        f"{statistics.observations_used}"
    )

    # ---------------------------------------------------------
    # SUPPORTING FINANCING
    # ---------------------------------------------------------

    print()
    print(
        "CURRENT SUPPORTING FINANCING"
    )

    print(
        "-" * 72
    )

    if snapshot.repo_billions is None:
        print(
            "Treasury repo:         "
            "suppressed / unavailable"
        )

    else:
        print(
            f"Treasury repo:         "
            f"${float(snapshot.repo_billions):,.0f}B"
        )

    if snapshot.reverse_repo_billions is None:
        print(
            "Treasury reverse repo: "
            "suppressed / unavailable"
        )

    else:
        print(
            f"Treasury reverse repo: "
            f"${float(snapshot.reverse_repo_billions):,.0f}B"
        )

    # ---------------------------------------------------------
    # CORE METRICS
    # ---------------------------------------------------------

    _print_metric(
        "Dealer Treasury Positions",
        statistics.dealer_positions,
        "$B",
    )

    _print_metric(
        "Treasury Transactions",
        statistics.treasury_transactions,
        "$B",
    )

    _print_metric(
        "Treasury Securities Borrowed",
        statistics.securities_borrowed,
        "$B",
    )

    _print_metric(
        "Fails to Receive",
        statistics.fails_receive,
        "$B",
    )

    _print_metric(
        "Fails to Deliver",
        statistics.fails_deliver,
        "$B",
    )

    _print_metric(
        "Total Treasury Fails",
        statistics.total_fails,
        "$B",
    )


# =============================================================
# DIRECT EXECUTION
# =============================================================


if __name__ == "__main__":
    print_treasury_intermediation_diagnostics()