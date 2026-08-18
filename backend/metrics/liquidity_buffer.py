from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy import select

from backend.database.connection import get_session
from backend.database.models import Indicator, Observation


@dataclass(frozen=True)
class LiquidityBufferMetrics:
    observation_date: date

    reserve_balances_billions: Decimal
    on_rrp_billions: Decimal
    combined_buffer_billions: Decimal

    previous_week_date: date
    previous_week_buffer_billions: Decimal
    weekly_change_billions: Decimal

    four_week_date: date
    four_week_buffer_billions: Decimal
    four_week_change_billions: Decimal

    reserve_change_4_week_billions: Decimal
    rrp_change_4_week_billions: Decimal

    reserve_share_percent: float
    rrp_share_percent: float


def liquidity_buffer_metrics() -> LiquidityBufferMetrics:
    """
    Build a preliminary liquidity-buffer proxy from:

        Reserve balances
        +
        ON RRP balances

    This is NOT a measure of total system liquidity.

    ON RRP observations are matched to each weekly
    reserve-balance observation using the latest ON RRP
    observation available on or before that reserve date.
    """

    with get_session() as session:

        reserve_indicator = session.scalar(
            select(Indicator).where(
                Indicator.symbol
                == "reserve_balances"
            )
        )

        rrp_indicator = session.scalar(
            select(Indicator).where(
                Indicator.symbol
                == "on_rrp"
            )
        )


        if reserve_indicator is None:
            raise RuntimeError(
                "Reserve balances indicator not found."
            )

        if rrp_indicator is None:
            raise RuntimeError(
                "ON RRP indicator not found."
            )


        reserve_observations = session.scalars(
            select(Observation)
            .where(
                Observation.indicator_id
                == reserve_indicator.id
            )
            .order_by(
                Observation.observation_date.desc()
            )
            .limit(5)
        ).all()


        rrp_observations = session.scalars(
            select(Observation)
            .where(
                Observation.indicator_id
                == rrp_indicator.id
            )
            .order_by(
                Observation.observation_date.desc()
            )
        ).all()


    if len(reserve_observations) < 5:
        raise RuntimeError(
            "At least five reserve balance "
            "observations are required."
        )

    if not rrp_observations:
        raise RuntimeError(
            "No ON RRP observations found."
        )


    def rrp_as_of(
        target_date: date,
    ) -> Observation:

        for observation in rrp_observations:

            if (
                observation.observation_date
                <= target_date
            ):
                return observation

        raise RuntimeError(
            f"No ON RRP observation available "
            f"on or before {target_date}."
        )


    # ---------------------------------------------------------
    # Current
    # ---------------------------------------------------------

    current_reserve = (
        reserve_observations[0]
    )

    current_rrp = rrp_as_of(
        current_reserve.observation_date
    )

    current_buffer = (
        current_reserve.value
        + current_rrp.value
    )


    # ---------------------------------------------------------
    # Previous week
    # ---------------------------------------------------------

    previous_reserve = (
        reserve_observations[1]
    )

    previous_rrp = rrp_as_of(
        previous_reserve.observation_date
    )

    previous_buffer = (
        previous_reserve.value
        + previous_rrp.value
    )


    # ---------------------------------------------------------
    # Four weeks earlier
    # ---------------------------------------------------------

    four_week_reserve = (
        reserve_observations[4]
    )

    four_week_rrp = rrp_as_of(
        four_week_reserve.observation_date
    )

    four_week_buffer = (
        four_week_reserve.value
        + four_week_rrp.value
    )


    # ---------------------------------------------------------
    # Component changes
    # ---------------------------------------------------------

    reserve_change_4_week = (
        current_reserve.value
        - four_week_reserve.value
    )

    rrp_change_4_week = (
        current_rrp.value
        - four_week_rrp.value
    )


    # ---------------------------------------------------------
    # Composition
    # ---------------------------------------------------------

    if current_buffer == 0:

        reserve_share = 0.0
        rrp_share = 0.0

    else:

        reserve_share = (
            float(
                current_reserve.value
                / current_buffer
            )
            * 100
        )

        rrp_share = (
            float(
                current_rrp.value
                / current_buffer
            )
            * 100
        )


    return LiquidityBufferMetrics(
        observation_date=
            current_reserve.observation_date,

        reserve_balances_billions=
            current_reserve.value,

        on_rrp_billions=
            current_rrp.value,

        combined_buffer_billions=
            current_buffer,

        previous_week_date=
            previous_reserve.observation_date,

        previous_week_buffer_billions=
            previous_buffer,

        weekly_change_billions=
            current_buffer
            - previous_buffer,

        four_week_date=
            four_week_reserve.observation_date,

        four_week_buffer_billions=
            four_week_buffer,

        four_week_change_billions=
            current_buffer
            - four_week_buffer,

        reserve_change_4_week_billions=
            reserve_change_4_week,

        rrp_change_4_week_billions=
            rrp_change_4_week,

        reserve_share_percent=
            reserve_share,

        rrp_share_percent=
            rrp_share,
    )