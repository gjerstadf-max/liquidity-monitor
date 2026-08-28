from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy import select

from backend.database.connection import get_session
from backend.database.models import Indicator, Observation


# =============================================================
# DATA OBJECT
# =============================================================


@dataclass(frozen=True)
class GlobalDollarFundingStatistics:
    observation_date: date

    swap_date: date
    fima_date: date

    swap_usage_billions: Decimal
    fima_repo_billions: Decimal

    swap_previous_billions: Decimal | None
    fima_previous_billions: Decimal | None

    swap_4w_max_billions: Decimal
    fima_4w_max_billions: Decimal


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


# =============================================================
# PUBLIC METRIC
# =============================================================


def global_dollar_funding_statistics(
    as_of_date: date | None = None,
) -> GlobalDollarFundingStatistics:

    swaps = _load_series(
        "central_bank_liquidity_swaps"
    )

    fima = _load_series(
        "fima_repo"
    )

    if as_of_date is None:
        as_of_date = max(
            swaps[-1][0],
            fima[-1][0],
        )

    swap_index = _index_at_or_before(
        swaps,
        as_of_date,
    )

    fima_index = _index_at_or_before(
        fima,
        as_of_date,
    )

    if (
        swap_index is None
        or fima_index is None
    ):
        raise RuntimeError(
            "Insufficient global-dollar "
            "funding data."
        )

    swap_date, swap_value = (
        swaps[swap_index]
    )

    fima_date, fima_value = (
        fima[fima_index]
    )

    swap_previous = (
        swaps[swap_index - 1][1]
        if swap_index >= 1
        else None
    )

    fima_previous = (
        fima[fima_index - 1][1]
        if fima_index >= 1
        else None
    )

    swap_window = [
        value
        for _, value
        in swaps[
            max(0, swap_index - 3):
            swap_index + 1
        ]
    ]

    fima_window = [
        value
        for _, value
        in fima[
            max(0, fima_index - 3):
            fima_index + 1
        ]
    ]

    return GlobalDollarFundingStatistics(
        observation_date=
            max(
                swap_date,
                fima_date,
            ),

        swap_date=
            swap_date,

        fima_date=
            fima_date,

        swap_usage_billions=
            swap_value,

        fima_repo_billions=
            fima_value,

        swap_previous_billions=
            swap_previous,

        fima_previous_billions=
            fima_previous,

        swap_4w_max_billions=
            max(swap_window),

        fima_4w_max_billions=
            max(fima_window),
    )


# =============================================================
# TERMINAL DISPLAY
# =============================================================


def print_global_dollar_funding_diagnostics() -> None:

    stats = (
        global_dollar_funding_statistics()
    )

    print()

    print(
        "Liquidity Monitor — "
        "Global Dollar Funding Stress"
    )

    print("=" * 72)

    print()

    print(
        f"Swap observation date: "
        f"{stats.swap_date}"
    )

    print(
        f"FIMA observation date: "
        f"{stats.fima_date}"
    )

    print()

    print(
        f"Central-bank swaps:     "
        f"${stats.swap_usage_billions:,.3f}B"
    )

    print(
        f"Swap 4-week maximum:    "
        f"${stats.swap_4w_max_billions:,.3f}B"
    )

    print()

    print(
        f"FIMA repo:              "
        f"${stats.fima_repo_billions:,.3f}B"
    )

    print(
        f"FIMA 4-week maximum:    "
        f"${stats.fima_4w_max_billions:,.3f}B"
    )


if __name__ == "__main__":
    print_global_dollar_funding_diagnostics()