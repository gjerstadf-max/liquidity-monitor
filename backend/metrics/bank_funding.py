from __future__ import annotations

from dataclasses import dataclass

from datetime import (
    date,
    datetime,
    time,
    timedelta,
)

from decimal import Decimal
from zoneinfo import ZoneInfo

from sqlalchemy import select

from backend.database.connection import (
    get_session,
)

from backend.database.models import (
    Indicator,
    Observation,
    ObservationVintage,
)

from backend.services.freshness import (
    expected_system_liquidity_observation_date,
)

# =============================================================
# DATA OBJECT
# =============================================================


@dataclass(frozen=True)
class BankFundingStatistics:
    observation_date: date

    primary_credit_date: date
    deposit_date: date

    primary_credit_billions: Decimal
    primary_credit_pct_deposits: float

    small_bank_deposits_billions: Decimal
    large_bank_deposits_billions: Decimal

    small_bank_deposits_4w_pct: float
    small_bank_deposits_13w_pct: float

    large_bank_deposits_4w_pct: float
    large_bank_deposits_13w_pct: float

    small_minus_large_4w_pp: float

    small_bank_time_deposits_4w_pct: float | None


# =============================================================
# DATABASE
# =============================================================


def _load_series(
    symbol: str,
) -> list[tuple[date, Decimal]]:

    with get_session() as session:

        rows = session.execute(
            select(
                Observation.observation_date,
                Observation.value,
            )
            .join(Indicator)
            .where(
                Indicator.symbol == symbol
            )
            .order_by(
                Observation.observation_date
            )
        ).all()

    if not rows:

        raise RuntimeError(
            f"No observations found for {symbol}."
        )

    return [
        (
            row[0],
            row[1],
        )
        for row in rows
    ]

def _load_vintage_series(
    symbol: str,
    vintage_date: date,
) -> list[tuple[date, Decimal]]:
    """
    Load one exact point-in-time vintage of a series.

    The vintage must already have been captured in the
    observation_vintages table.
    """

    with get_session() as session:
        rows = session.execute(
            select(
                ObservationVintage.observation_date,
                ObservationVintage.value,
            )
            .join(Indicator)
            .where(
                Indicator.symbol == symbol,
                ObservationVintage.vintage_date
                == vintage_date,
            )
            .order_by(
                ObservationVintage.observation_date
            )
        ).all()

    if not rows:
        raise RuntimeError(
            "No vintage observations found for "
            f"{symbol} on {vintage_date}."
        )

    return [
        (
            row[0],
            row[1],
        )
        for row in rows
    ]


def _index_at_or_before(
    observations: list[
        tuple[date, Decimal]
    ],
    target_date: date,
) -> int | None:

    valid = [
        index
        for index, (
            observation_date,
            _,
        )
        in enumerate(observations)
        if observation_date <= target_date
    ]

    if not valid:
        return None

    return valid[-1]


def _value_at_or_before(
    observations: list[
        tuple[date, Decimal]
    ],
    target_date: date,
) -> tuple[date, Decimal] | None:

    index = _index_at_or_before(
        observations,
        target_date,
    )

    if index is None:
        return None

    return observations[index]


def _pct_change(
    observations: list[
        tuple[date, Decimal]
    ],
    target_date: date,
    lag: int,
) -> float | None:

    index = _index_at_or_before(
        observations,
        target_date,
    )

    if (
        index is None
        or index < lag
    ):
        return None

    current = (
        observations[index][1]
    )

    previous = (
        observations[index - lag][1]
    )

    if previous == 0:
        return None

    return float(
        (
            current / previous
            - Decimal("1")
        )
        * Decimal("100")
    )


# =============================================================
# PUBLIC METRIC
# =============================================================


def bank_funding_statistics(
    as_of_date: date | None = None,
) -> BankFundingStatistics:

    is_historical_replay = (
        as_of_date is not None
    )

    primary = _load_series(
        "fed_primary_credit"
    )

    if not is_historical_replay:
        small = _load_series(
            "bank_deposits_small"
        )
        large = _load_series(
            "bank_deposits_large"
        )
        time_deposits = _load_series(
            "bank_large_time_deposits_small"
        )

        as_of_date = max(
            primary[-1][0],
            small[-1][0],
            large[-1][0],
        )

        primary_available_date = (
            as_of_date
        )

    else:
        h8_vintage_date = (
            as_of_date
            - timedelta(days=1)
        )

        small = _load_vintage_series(
            "bank_deposits_small",
            h8_vintage_date,
        )
        large = _load_vintage_series(
            "bank_deposits_large",
            h8_vintage_date,
        )
        time_deposits = (
            _load_vintage_series(
                "bank_large_time_deposits_small",
                h8_vintage_date,
            )
        )

        replay_morning = datetime.combine(
            as_of_date,
            time(hour=9),
            tzinfo=ZoneInfo(
                "America/New_York"
            ),
        )

        primary_available_date = (
            expected_system_liquidity_observation_date(
                now=replay_morning
            )
        )

    primary_obs = _value_at_or_before(
        primary,
        primary_available_date,
    )

    small_obs = _value_at_or_before(
        small,
        as_of_date,
    )

    large_obs = _value_at_or_before(
        large,
        as_of_date,
    )

    if (
        primary_obs is None
        or small_obs is None
        or large_obs is None
    ):

        raise RuntimeError(
            "Insufficient bank-funding data."
        )

    primary_date, primary_value = (
        primary_obs
    )

    small_date, small_value = (
        small_obs
    )

    large_date, large_value = (
        large_obs
    )

    total_deposits = (
        small_value
        + large_value
    )

    primary_pct_deposits = float(
        primary_value
        / total_deposits
        * Decimal("100")
    )

    small_4w = _pct_change(
        small,
        as_of_date,
        4,
    )

    small_13w = _pct_change(
        small,
        as_of_date,
        13,
    )

    large_4w = _pct_change(
        large,
        as_of_date,
        4,
    )

    large_13w = _pct_change(
        large,
        as_of_date,
        13,
    )

    if None in (
        small_4w,
        small_13w,
        large_4w,
        large_13w,
    ):

        raise RuntimeError(
            "Insufficient deposit history."
        )

    time_deposit_4w = _pct_change(
        time_deposits,
        as_of_date,
        4,
    )

    deposit_date = min(
        small_date,
        large_date,
    )

    return BankFundingStatistics(
        observation_date=
            max(
                primary_date,
                deposit_date,
            ),

        primary_credit_date=
            primary_date,

        deposit_date=
            deposit_date,

        primary_credit_billions=
            primary_value,

        primary_credit_pct_deposits=
            primary_pct_deposits,

        small_bank_deposits_billions=
            small_value,

        large_bank_deposits_billions=
            large_value,

        small_bank_deposits_4w_pct=
            small_4w,

        small_bank_deposits_13w_pct=
            small_13w,

        large_bank_deposits_4w_pct=
            large_4w,

        large_bank_deposits_13w_pct=
            large_13w,

        small_minus_large_4w_pp=
            small_4w - large_4w,

        small_bank_time_deposits_4w_pct=
            time_deposit_4w,
    )


# =============================================================
# TERMINAL DISPLAY
# =============================================================


def print_bank_funding_diagnostics() -> None:

    stats = (
        bank_funding_statistics()
    )

    print()

    print(
        "Liquidity Monitor — "
        "Bank Funding Stress"
    )

    print("=" * 72)

    print()

    print(
        f"Primary credit date:      "
        f"{stats.primary_credit_date}"
    )

    print(
        f"Deposit data date:        "
        f"{stats.deposit_date}"
    )

    print()

    print(
        f"Primary credit:           "
        f"${stats.primary_credit_billions:,.3f}B"
    )

    print(
        f"Primary credit / deposits:"
        f" {stats.primary_credit_pct_deposits:.4f}%"
    )

    print()

    print(
        f"Small-bank deposits 4w:   "
        f"{stats.small_bank_deposits_4w_pct:+.2f}%"
    )

    print(
        f"Small-bank deposits 13w:  "
        f"{stats.small_bank_deposits_13w_pct:+.2f}%"
    )

    print(
        f"Large-bank deposits 4w:   "
        f"{stats.large_bank_deposits_4w_pct:+.2f}%"
    )

    print(
        f"Large-bank deposits 13w:  "
        f"{stats.large_bank_deposits_13w_pct:+.2f}%"
    )

    print(
        f"Small minus large 4w:     "
        f"{stats.small_minus_large_4w_pp:+.2f} pp"
    )

    if (
        stats.small_bank_time_deposits_4w_pct
        is not None
    ):

        print(
            f"Small-bank time dep 4w:   "
            f"{stats.small_bank_time_deposits_4w_pct:+.2f}%"
        )


if __name__ == "__main__":
    print_bank_funding_diagnostics()