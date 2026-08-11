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
    sofr: Decimal
    effr: Decimal
    spread_basis_points: Decimal


def latest_funding_snapshot() -> FundingSnapshot:
    with get_session() as session:
        sofr = session.scalar(
            select(Observation)
            .join(Indicator)
            .where(Indicator.symbol == "sofr")
            .order_by(Observation.observation_date.desc())
        )

        effr = session.scalar(
            select(Observation)
            .join(Indicator)
            .where(Indicator.symbol == "effr")
            .order_by(Observation.observation_date.desc())
        )

        if sofr is None:
            raise RuntimeError("SOFR observation not found.")

        if effr is None:
            raise RuntimeError("EFFR observation not found.")

        if sofr.observation_date != effr.observation_date:
            raise RuntimeError(
                "Latest SOFR and EFFR observations do not share the same date."
            )

        spread_percentage_points = sofr.value - effr.value
        spread_basis_points = spread_percentage_points * Decimal("100")

        return FundingSnapshot(
            observation_date=sofr.observation_date,
            sofr=sofr.value,
            effr=effr.value,
            spread_basis_points=spread_basis_points,
        )