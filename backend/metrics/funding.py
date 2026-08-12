from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

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


def latest_funding_snapshot() -> FundingSnapshot:
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
        raise RuntimeError("SOFR observations not found.")

    if not effr_rows:
        raise RuntimeError("EFFR observations not found.")

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

    if len(common_dates) < 2:
        raise RuntimeError(
            "At least two common SOFR/EFFR observation dates are required."
        )

    current_date = common_dates[0]
    previous_date = common_dates[1]

    sofr = sofr_by_date[current_date]
    previous_sofr = sofr_by_date[previous_date]

    effr = effr_by_date[current_date]
    previous_effr = effr_by_date[previous_date]

    spread = (sofr - effr) * Decimal("100")
    previous_spread = (
        previous_sofr - previous_effr
    ) * Decimal("100")

    return FundingSnapshot(
        observation_date=current_date,
        previous_observation_date=previous_date,

        sofr=sofr,
        previous_sofr=previous_sofr,
        sofr_change_bp=(sofr - previous_sofr) * Decimal("100"),

        effr=effr,
        previous_effr=previous_effr,
        effr_change_bp=(effr - previous_effr) * Decimal("100"),

        spread_basis_points=spread,
        previous_spread_basis_points=previous_spread,
        spread_change_bp=spread - previous_spread,
    )