from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from statistics import mean, pstdev

from sqlalchemy import select

from backend.database.connection import get_session
from backend.database.models import Indicator, Observation


BP = Decimal("100")


# =============================================================
# DATA OBJECTS
# =============================================================


@dataclass(frozen=True)
class CommercialPaperSnapshot:
    observation_date: date

    aa_nonfinancial_30d: Decimal
    a2p2_nonfinancial_30d: Decimal

    credit_premium_bp: Decimal


@dataclass(frozen=True)
class CommercialPaperStatistics:
    observation_date: date
    observations_used: int

    current_spread_bp: Decimal
    previous_spread_bp: Decimal

    average_20d_bp: Decimal
    average_60d_bp: Decimal

    minimum_60d_bp: Decimal
    maximum_60d_bp: Decimal

    percentile_60d: float
    zscore_60d: float

    full_history_percentile: float
    full_history_zscore: float


# =============================================================
# DATABASE
# =============================================================


def _load_series(
    symbol: str,
) -> dict[date, Decimal]:

    with get_session() as session:

        rows = session.scalars(
            select(Observation)
            .join(Indicator)
            .where(
                Indicator.symbol == symbol
            )
            .order_by(
                Observation.observation_date.desc()
            )
        ).all()

    if not rows:

        raise RuntimeError(
            f"No observations found for {symbol}."
        )

    return {
        row.observation_date: row.value
        for row in rows
    }


# =============================================================
# HISTORY
# =============================================================


def _load_credit_spread_history(
    as_of_date: date | None = None,
) -> list[CommercialPaperSnapshot]:

    aa = _load_series(
        "cp_aa_nonfinancial_30d"
    )

    a2p2 = _load_series(
        "cp_a2p2_nonfinancial_30d"
    )

    common_dates = (
        set(aa)
        & set(a2p2)
    )

    if as_of_date is not None:

        common_dates = {
            observation_date
            for observation_date
            in common_dates
            if observation_date <= as_of_date
        }

    if not common_dates:

        raise RuntimeError(
            "No common commercial-paper "
            "observation dates found."
        )

    history: list[
        CommercialPaperSnapshot
    ] = []

    for observation_date in sorted(
        common_dates,
        reverse=True,
    ):

        aa_value = (
            aa[observation_date]
        )

        a2p2_value = (
            a2p2[observation_date]
        )

        history.append(
            CommercialPaperSnapshot(
                observation_date=
                    observation_date,

                aa_nonfinancial_30d=
                    aa_value,

                a2p2_nonfinancial_30d=
                    a2p2_value,

                credit_premium_bp=(
                    a2p2_value
                    - aa_value
                ) * BP,
            )
        )

    return history


# =============================================================
# STATISTICS
# =============================================================


def _percentile(
    current: float,
    values: list[float],
) -> float:

    if not values:
        return 0.0

    observations_at_or_below = sum(
        1
        for value in values
        if value <= current
    )

    return (
        observations_at_or_below
        / len(values)
        * 100
    )


def _zscore(
    current: float,
    values: list[float],
) -> float:

    if len(values) < 2:
        return 0.0

    historical_mean = mean(
        values
    )

    historical_std = pstdev(
        values
    )

    if historical_std == 0:
        return 0.0

    return (
        current
        - historical_mean
    ) / historical_std


# =============================================================
# PUBLIC FUNCTIONS
# =============================================================


def latest_commercial_paper_snapshot(
    as_of_date: date | None = None,
) -> CommercialPaperSnapshot:

    history = (
        _load_credit_spread_history(
            as_of_date=as_of_date
        )
    )

    return history[0]


def commercial_paper_statistics(
    lookback: int = 60,
    as_of_date: date | None = None,
) -> CommercialPaperStatistics:

    if lookback < 20:

        raise ValueError(
            "lookback must be at least 20"
        )

    history = (
        _load_credit_spread_history(
            as_of_date=as_of_date
        )
    )

    if len(history) < lookback:

        raise RuntimeError(
            "Insufficient commercial-paper history."
        )

    selected = history[:lookback]

    current = (
        selected[0].credit_premium_bp
    )

    previous = (
        selected[1].credit_premium_bp
    )

    last_20 = [
        item.credit_premium_bp
        for item in selected[:20]
    ]

    last_60 = [
        item.credit_premium_bp
        for item in selected[:60]
    ]

    full_history = [
        item.credit_premium_bp
        for item in history
    ]

    average_20 = (
        sum(
            last_20,
            Decimal("0"),
        )
        / Decimal(
            len(last_20)
        )
    )

    average_60 = (
        sum(
            last_60,
            Decimal("0"),
        )
        / Decimal(
            len(last_60)
        )
    )

    current_float = float(
        current
    )

    last_60_float = [
        float(value)
        for value in last_60
    ]

    full_history_float = [
        float(value)
        for value in full_history
    ]

    return CommercialPaperStatistics(
        observation_date=
            selected[0].observation_date,

        observations_used=
            len(selected),

        current_spread_bp=
            current,

        previous_spread_bp=
            previous,

        average_20d_bp=
            average_20,

        average_60d_bp=
            average_60,

        minimum_60d_bp=
            min(last_60),

        maximum_60d_bp=
            max(last_60),

        percentile_60d=
            _percentile(
                current_float,
                last_60_float,
            ),

        zscore_60d=
            _zscore(
                current_float,
                last_60_float,
            ),

        full_history_percentile=
            _percentile(
                current_float,
                full_history_float,
            ),

        full_history_zscore=
            _zscore(
                current_float,
                full_history_float,
            ),
    )


# =============================================================
# TERMINAL DISPLAY
# =============================================================


def print_commercial_paper_diagnostics() -> None:

    snapshot = (
        latest_commercial_paper_snapshot()
    )

    stats = (
        commercial_paper_statistics()
    )

    print()

    print(
        "Liquidity Monitor — "
        "Commercial Paper Funding"
    )

    print("=" * 72)

    print()

    print(
        f"Observation date: "
        f"{snapshot.observation_date}"
    )

    print()

    print(
        f"AA nonfinancial 30-day:   "
        f"{snapshot.aa_nonfinancial_30d:.2f}%"
    )

    print(
        f"A2/P2 nonfinancial 30-day:"
        f" {snapshot.a2p2_nonfinancial_30d:.2f}%"
    )

    print()

    print(
        f"A2/P2 - AA spread:        "
        f"{stats.current_spread_bp:+.1f} bp"
    )

    print(
        f"Previous:                 "
        f"{stats.previous_spread_bp:+.1f} bp"
    )

    print(
        f"20-day average:           "
        f"{stats.average_20d_bp:.1f} bp"
    )

    print(
        f"60-day average:           "
        f"{stats.average_60d_bp:.1f} bp"
    )

    print(
        f"60-day range:             "
        f"{stats.minimum_60d_bp:.1f} "
        f"to "
        f"{stats.maximum_60d_bp:.1f} bp"
    )

    print(
        f"60-day percentile:        "
        f"{stats.percentile_60d:.1f}"
    )

    print(
        f"60-day z-score:           "
        f"{stats.zscore_60d:+.2f}"
    )

    print(
        f"Full-history percentile:  "
        f"{stats.full_history_percentile:.1f}"
    )

    print(
        f"Full-history z-score:     "
        f"{stats.full_history_zscore:+.2f}"
    )


if __name__ == "__main__":
    print_commercial_paper_diagnostics()