from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from statistics import mean, pstdev

from sqlalchemy import select

from backend.database.connection import get_session
from backend.database.models import Indicator, Observation


@dataclass(frozen=True)
class FundingSnapshot:
    observation_date: date
    previous_observation_date: date

    sofr: Decimal
    previous_sofr: Decimal
    sofr_change_bp: Decimal

    effr: Decimal
    previous_effr: Decimal
    effr_change_bp: Decimal

    spread_basis_points: Decimal
    previous_spread_basis_points: Decimal
    spread_change_bp: Decimal


@dataclass(frozen=True)
class FundingSpreadStatistics:
    observation_date: date
    observations_used: int

    current_spread_bp: Decimal

    average_30d_bp: Decimal
    average_60d_bp: Decimal

    minimum_60d_bp: Decimal
    maximum_60d_bp: Decimal

    percentile_60d: float
    zscore_60d: float


def _load_common_rate_history() -> list[
    tuple[date, Decimal, Decimal]
]:
    """
    Return common SOFR/EFFR observations sorted newest first.

    Each tuple contains:
        observation_date
        SOFR
        EFFR
    """

    with get_session() as session:
        sofr_rows = session.scalars(
            select(Observation)
            .join(Indicator)
            .where(Indicator.symbol == "sofr")
            .order_by(Observation.observation_date.desc())
        ).all()

        effr_rows = session.scalars(
            select(Observation)
            .join(Indicator)
            .where(Indicator.symbol == "effr")
            .order_by(Observation.observation_date.desc())
        ).all()

    if not sofr_rows:
        raise RuntimeError(
            "SOFR observations not found."
        )

    if not effr_rows:
        raise RuntimeError(
            "EFFR observations not found."
        )

    sofr_by_date = {
        row.observation_date: row.value
        for row in sofr_rows
    }

    effr_by_date = {
        row.observation_date: row.value
        for row in effr_rows
    }

    common_dates = sorted(
        set(sofr_by_date) & set(effr_by_date),
        reverse=True,
    )

    if not common_dates:
        raise RuntimeError(
            "No common SOFR/EFFR observation dates found."
        )

    return [
        (
            observation_date,
            sofr_by_date[observation_date],
            effr_by_date[observation_date],
        )
        for observation_date in common_dates
    ]


def latest_funding_snapshot() -> FundingSnapshot:
    history = _load_common_rate_history()

    if len(history) < 2:
        raise RuntimeError(
            "At least two common SOFR/EFFR "
            "observation dates are required."
        )

    current_date, sofr, effr = history[0]

    (
        previous_date,
        previous_sofr,
        previous_effr,
    ) = history[1]

    spread = (
        sofr - effr
    ) * Decimal("100")

    previous_spread = (
        previous_sofr - previous_effr
    ) * Decimal("100")

    return FundingSnapshot(
        observation_date=current_date,
        previous_observation_date=previous_date,

        sofr=sofr,
        previous_sofr=previous_sofr,
        sofr_change_bp=(
            sofr - previous_sofr
        ) * Decimal("100"),

        effr=effr,
        previous_effr=previous_effr,
        effr_change_bp=(
            effr - previous_effr
        ) * Decimal("100"),

        spread_basis_points=spread,
        previous_spread_basis_points=previous_spread,
        spread_change_bp=spread - previous_spread,
    )


def funding_spread_statistics(
    lookback: int = 60,
) -> FundingSpreadStatistics:
    """
    Calculate historical context for the SOFR-EFFR spread.

    Spread values are expressed in basis points.
    """

    if lookback < 2:
        raise ValueError(
            "lookback must be at least 2"
        )

    history = _load_common_rate_history()

    selected = history[:lookback]

    if len(selected) < 2:
        raise RuntimeError(
            "At least two common observations are "
            "required for spread statistics."
        )

    spreads = [
        (
            sofr - effr
        ) * Decimal("100")
        for _, sofr, effr in selected
    ]

    current_spread = spreads[0]

    last_30 = spreads[:30]

    average_30 = (
        sum(last_30, Decimal("0"))
        / Decimal(len(last_30))
    )

    average_60 = (
        sum(spreads, Decimal("0"))
        / Decimal(len(spreads))
    )

    minimum = min(spreads)
    maximum = max(spreads)

    observations_at_or_below_current = sum(
        1
        for value in spreads
        if value <= current_spread
    )

    percentile = (
        observations_at_or_below_current
        / len(spreads)
        * 100
    )

    spread_floats = [
        float(value)
        for value in spreads
    ]

    historical_mean = mean(
        spread_floats
    )

    historical_std = pstdev(
        spread_floats
    )

    if historical_std == 0:
        zscore = 0.0
    else:
        zscore = (
            float(current_spread)
            - historical_mean
        ) / historical_std

    return FundingSpreadStatistics(
        observation_date=selected[0][0],
        observations_used=len(spreads),

        current_spread_bp=current_spread,

        average_30d_bp=average_30,
        average_60d_bp=average_60,

        minimum_60d_bp=minimum,
        maximum_60d_bp=maximum,

        percentile_60d=percentile,
        zscore_60d=zscore,
    )