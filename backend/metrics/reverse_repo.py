from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy import select

from backend.database.connection import get_session
from backend.database.models import Indicator, Observation


@dataclass(frozen=True)
class ReverseRepoMetrics:
    observation_date: date
    previous_observation_date: date

    current_balance_billions: Decimal
    previous_balance_billions: Decimal
    daily_change_billions: Decimal

    observations_used: int

    average_20d_billions: Decimal
    average_60d_billions: Decimal

    minimum_60d_billions: Decimal
    maximum_60d_billions: Decimal

    percentile_60d: float


def reverse_repo_metrics(
    lookback: int = 60,
) -> ReverseRepoMetrics:
    """
    Calculate recent historical context for ON RRP usage.

    Values are stored and reported in USD billions.
    """

    if lookback < 2:
        raise ValueError(
            "lookback must be at least 2"
        )

    with get_session() as session:

        indicator = session.scalar(
            select(Indicator).where(
                Indicator.symbol == "on_rrp"
            )
        )

        if indicator is None:
            raise RuntimeError(
                "ON RRP indicator not found."
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


    if len(observations) < 2:
        raise RuntimeError(
            "At least two ON RRP observations "
            "are required."
        )


    values = [
        observation.value
        for observation in observations
    ]


    current = values[0]
    previous = values[1]


    last_20 = values[:20]


    average_20 = (
        sum(last_20, Decimal("0"))
        / Decimal(len(last_20))
    )


    average_60 = (
        sum(values, Decimal("0"))
        / Decimal(len(values))
    )


    minimum = min(values)
    maximum = max(values)


    observations_at_or_below_current = sum(
        1
        for value in values
        if value <= current
    )


    percentile = (
        observations_at_or_below_current
        / len(values)
        * 100
    )


    return ReverseRepoMetrics(
        observation_date=
            observations[0].observation_date,

        previous_observation_date=
            observations[1].observation_date,

        current_balance_billions=current,

        previous_balance_billions=previous,

        daily_change_billions=
            current - previous,

        observations_used=len(values),

        average_20d_billions=average_20,

        average_60d_billions=average_60,

        minimum_60d_billions=minimum,

        maximum_60d_billions=maximum,

        percentile_60d=percentile,
    )