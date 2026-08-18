from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from statistics import mean, pstdev

from sqlalchemy import select

from backend.database.connection import get_session
from backend.database.models import Indicator, Observation


# =============================================================
# DATA OBJECTS
# =============================================================


@dataclass(frozen=True)
class SystemLiquidityPoint:
    observation_date: date

    reserve_balances_billions: Decimal
    on_rrp_billions: Decimal
    tga_billions: Decimal

    net_liquidity_proxy_billions: Decimal


@dataclass(frozen=True)
class SystemLiquidityMetrics:
    observation_date: date

    reserve_balances_billions: Decimal
    on_rrp_billions: Decimal
    tga_billions: Decimal

    net_liquidity_proxy_billions: Decimal

    weekly_change_billions: Decimal
    four_week_change_billions: Decimal

    reserve_weekly_contribution_billions: Decimal
    rrp_weekly_contribution_billions: Decimal
    tga_weekly_contribution_billions: Decimal

    reserve_4_week_contribution_billions: Decimal
    rrp_4_week_contribution_billions: Decimal
    tga_4_week_contribution_billions: Decimal


@dataclass(frozen=True)
class SystemLiquidityHistoryMetrics:
    observation_date: date

    observations_used: int

    current_proxy_billions: Decimal

    four_week_change_billions: Decimal
    thirteen_week_change_billions: Decimal

    average_13_week_billions: Decimal
    average_52_week_billions: Decimal

    minimum_52_week_billions: Decimal
    maximum_52_week_billions: Decimal

    percentile_52_week: float
    zscore_52_week: float


# =============================================================
# DATA LOADING
# =============================================================


def _load_system_series():
    """
    Load reserve balances, ON RRP and TGA observations.

    All returned series are sorted newest first.
    """

    with get_session() as session:

        reserve_indicator = session.scalar(
            select(Indicator).where(
                Indicator.symbol == "reserve_balances"
            )
        )

        rrp_indicator = session.scalar(
            select(Indicator).where(
                Indicator.symbol == "on_rrp"
            )
        )

        tga_indicator = session.scalar(
            select(Indicator).where(
                Indicator.symbol == "tga"
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

        if tga_indicator is None:
            raise RuntimeError(
                "TGA indicator not found."
            )


        reserve_rows = session.scalars(
            select(Observation)
            .where(
                Observation.indicator_id
                == reserve_indicator.id
            )
            .order_by(
                Observation.observation_date.desc()
            )
        ).all()


        rrp_rows = session.scalars(
            select(Observation)
            .where(
                Observation.indicator_id
                == rrp_indicator.id
            )
            .order_by(
                Observation.observation_date.desc()
            )
        ).all()


        tga_rows = session.scalars(
            select(Observation)
            .where(
                Observation.indicator_id
                == tga_indicator.id
            )
            .order_by(
                Observation.observation_date.desc()
            )
        ).all()


        reserves = [
            (
                row.observation_date,
                row.value,
            )
            for row in reserve_rows
        ]

        rrp = [
            (
                row.observation_date,
                row.value,
            )
            for row in rrp_rows
        ]

        tga = [
            (
                row.observation_date,
                row.value,
            )
            for row in tga_rows
        ]


    return reserves, rrp, tga


def _value_as_of(
    observations: list[
        tuple[date, Decimal]
    ],
    target_date: date,
) -> Decimal:
    """
    Return the most recent observation available
    on or before target_date.
    """

    for (
        observation_date,
        value,
    ) in observations:

        if observation_date <= target_date:
            return value

    raise RuntimeError(
        f"No observation available on or before "
        f"{target_date}."
    )


# =============================================================
# HISTORICAL WEEKLY SERIES
# =============================================================


def build_system_liquidity_history(
    lookback: int = 52,
) -> list[SystemLiquidityPoint]:
    """
    Build weekly system-liquidity proxy history.

    Formula:

        Reserve Balances
        + ON RRP
        - TGA

    Reserve-balance observation dates provide the weekly
    anchor.

    TGA and reserve balances are Wednesday series.

    ON RRP is matched using the latest observation available
    on or before each reserve-balance date.

    Results are returned newest first.
    """

    if lookback < 1:
        raise ValueError(
            "lookback must be at least 1"
        )

    (
        reserves,
        rrp,
        tga,
    ) = _load_system_series()


    if not reserves:
        raise RuntimeError(
            "No reserve balance observations found."
        )

    if not rrp:
        raise RuntimeError(
            "No ON RRP observations found."
        )

    if not tga:
        raise RuntimeError(
            "No TGA observations found."
        )


    selected_reserves = (
        reserves[:lookback]
    )

    history: list[
        SystemLiquidityPoint
    ] = []


    for (
        observation_date,
        reserve_value,
    ) in selected_reserves:

        rrp_value = _value_as_of(
            rrp,
            observation_date,
        )

        tga_value = _value_as_of(
            tga,
            observation_date,
        )

        net_liquidity = (
            reserve_value
            + rrp_value
            - tga_value
        )

        history.append(
            SystemLiquidityPoint(
                observation_date=
                    observation_date,

                reserve_balances_billions=
                    reserve_value,

                on_rrp_billions=
                    rrp_value,

                tga_billions=
                    tga_value,

                net_liquidity_proxy_billions=
                    net_liquidity,
            )
        )


    return history


# =============================================================
# CURRENT DECOMPOSITION
# =============================================================


def system_liquidity_metrics() -> SystemLiquidityMetrics:
    """
    Current system-liquidity decomposition.

    Preliminary proxy:

        Reserve Balances
        + ON RRP
        - TGA

    This is a monitoring proxy, not a measure of total
    financial-system liquidity.
    """

    history = build_system_liquidity_history(
        lookback=5
    )


    if len(history) < 5:
        raise RuntimeError(
            "At least five weekly observations "
            "are required."
        )


    current = history[0]
    previous = history[1]
    four_week = history[4]


    # ---------------------------------------------------------
    # Weekly component contributions
    # ---------------------------------------------------------

    reserve_weekly = (
        current.reserve_balances_billions
        - previous.reserve_balances_billions
    )

    rrp_weekly = (
        current.on_rrp_billions
        - previous.on_rrp_billions
    )

    # A TGA increase removes liquidity from the proxy,
    # therefore its contribution has the opposite sign.
    tga_weekly = -(
        current.tga_billions
        - previous.tga_billions
    )


    # ---------------------------------------------------------
    # Four-week component contributions
    # ---------------------------------------------------------

    reserve_4_week = (
        current.reserve_balances_billions
        - four_week.reserve_balances_billions
    )

    rrp_4_week = (
        current.on_rrp_billions
        - four_week.on_rrp_billions
    )

    tga_4_week = -(
        current.tga_billions
        - four_week.tga_billions
    )


    return SystemLiquidityMetrics(
        observation_date=
            current.observation_date,

        reserve_balances_billions=
            current.reserve_balances_billions,

        on_rrp_billions=
            current.on_rrp_billions,

        tga_billions=
            current.tga_billions,

        net_liquidity_proxy_billions=
            current.net_liquidity_proxy_billions,

        weekly_change_billions=(
            current.net_liquidity_proxy_billions
            - previous.net_liquidity_proxy_billions
        ),

        four_week_change_billions=(
            current.net_liquidity_proxy_billions
            - four_week.net_liquidity_proxy_billions
        ),

        reserve_weekly_contribution_billions=
            reserve_weekly,

        rrp_weekly_contribution_billions=
            rrp_weekly,

        tga_weekly_contribution_billions=
            tga_weekly,

        reserve_4_week_contribution_billions=
            reserve_4_week,

        rrp_4_week_contribution_billions=
            rrp_4_week,

        tga_4_week_contribution_billions=
            tga_4_week,
    )


# =============================================================
# HISTORICAL ANALYTICS
# =============================================================


def system_liquidity_history_metrics(
    lookback: int = 52,
) -> SystemLiquidityHistoryMetrics:
    """
    Calculate historical context for the weekly
    system-liquidity proxy.

    Includes:

        4-week change
        13-week change
        13-week average
        52-week average
        52-week range
        52-week percentile
        52-week z-score
    """

    if lookback < 14:
        raise ValueError(
            "lookback must be at least 14"
        )


    history = build_system_liquidity_history(
        lookback=lookback
    )


    if len(history) < 14:
        raise RuntimeError(
            "At least 14 system-liquidity "
            "observations are required."
        )


    values = [
        point.net_liquidity_proxy_billions
        for point in history
    ]


    current = values[0]


    # ---------------------------------------------------------
    # Changes
    # ---------------------------------------------------------

    if len(values) >= 5:

        four_week_change = (
            current
            - values[4]
        )

    else:

        four_week_change = Decimal("0")


    thirteen_week_change = (
        current
        - values[13]
    )


    # ---------------------------------------------------------
    # Averages
    # ---------------------------------------------------------

    last_13 = values[:13]


    average_13 = (
        sum(
            last_13,
            Decimal("0"),
        )
        / Decimal(
            len(last_13)
        )
    )


    average_full = (
        sum(
            values,
            Decimal("0"),
        )
        / Decimal(
            len(values)
        )
    )


    # ---------------------------------------------------------
    # Range
    # ---------------------------------------------------------

    minimum = min(
        values
    )

    maximum = max(
        values
    )


    # ---------------------------------------------------------
    # Percentile
    # ---------------------------------------------------------

    at_or_below_current = sum(
        1
        for value in values
        if value <= current
    )


    percentile = (
        at_or_below_current
        / len(values)
        * 100
    )


    # ---------------------------------------------------------
    # Z-score
    # ---------------------------------------------------------

    float_values = [
        float(value)
        for value in values
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
            float(current)
            - historical_mean
        ) / historical_std


    return SystemLiquidityHistoryMetrics(
        observation_date=
            history[0].observation_date,

        observations_used=
            len(values),

        current_proxy_billions=
            current,

        four_week_change_billions=
            four_week_change,

        thirteen_week_change_billions=
            thirteen_week_change,

        average_13_week_billions=
            average_13,

        average_52_week_billions=
            average_full,

        minimum_52_week_billions=
            minimum,

        maximum_52_week_billions=
            maximum,

        percentile_52_week=
            percentile,

        zscore_52_week=
            zscore,
    )