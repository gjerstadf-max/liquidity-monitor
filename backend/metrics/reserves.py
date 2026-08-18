from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy import select

from backend.database.connection import get_session
from backend.database.models import Indicator, Observation


@dataclass(frozen=True)
class ReserveBalanceMetrics:
    observation_date: date
    previous_observation_date: date

    current_balance_billions: Decimal
    previous_balance_billions: Decimal

    weekly_change_billions: Decimal
    four_week_change_billions: Decimal

    average_13_week_billions: Decimal
    minimum_13_week_billions: Decimal
    maximum_13_week_billions: Decimal

    percentile_52_week: float

    observations_used: int


def reserve_balance_metrics(
    lookback: int = 52,
) -> ReserveBalanceMetrics:
    """
    Calculate historical context for Federal Reserve
    reserve balances.

    Values are stored in USD billions.
    """

    if lookback < 13:
        raise ValueError(
            "lookback must be at least 13 observations"
        )

    with get_session() as session:

        indicator = session.scalar(
            select(Indicator).where(
                Indicator.symbol
                == "reserve_balances"
            )
        )

        if indicator is None:
            raise RuntimeError(
                "Reserve balances indicator not found."
            )

        observations = session.scalars(
            select(Observation)
            .where(
                Observation.indicator_id
                == indicator.id
            )
            .order_by(
                Observation.observation_date.desc()
            )
            .limit(lookback)
        ).all()


    if len(observations) < 13:
        raise RuntimeError(
            "At least 13 reserve balance "
            "observations are required."
        )


    values = [
        observation.value
        for observation in observations
    ]


    current = values[0]
    previous = values[1]


    # Four-week change:
    # current versus four observations ago.
    #
    # Weekly H.4.1 series means this is approximately
    # one month of movement.
    if len(values) >= 5:
        four_week_change = (
            current - values[4]
        )
    else:
        four_week_change = Decimal("0")


    last_13 = values[:13]


    average_13 = (
        sum(
            last_13,
            Decimal("0")
        )
        / Decimal(
            len(last_13)
        )
    )


    minimum_13 = min(
        last_13
    )

    maximum_13 = max(
        last_13
    )


    observations_at_or_below_current = sum(
        1
        for value in values
        if value <= current
    )


    percentile_52 = (
        observations_at_or_below_current
        / len(values)
        * 100
    )


    return ReserveBalanceMetrics(
        observation_date=
            observations[0].observation_date,

        previous_observation_date=
            observations[1].observation_date,

        current_balance_billions=current,

        previous_balance_billions=previous,

        weekly_change_billions=
            current - previous,

        four_week_change_billions=
            four_week_change,

        average_13_week_billions=
            average_13,

        minimum_13_week_billions=
            minimum_13,

        maximum_13_week_billions=
            maximum_13,

        percentile_52_week=
            percentile_52,

        observations_used=
            len(values),
    )