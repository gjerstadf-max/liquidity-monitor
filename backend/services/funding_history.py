from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy import select

from backend.database.connection import get_session
from backend.database.models import Indicator, Observation


@dataclass(frozen=True)
class FundingHistoryPoint:
    observation_date: date
    sofr: Decimal
    effr: Decimal
    spread_basis_points: Decimal


def get_funding_history(
    observation_count: int = 60,
) -> list[FundingHistoryPoint]:

    if observation_count < 1 or observation_count > 1000:
        raise ValueError(
            "observation_count must be between 1 and 1000"
        )

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
    )[:observation_count]

    history = []

    for observation_date in reversed(common_dates):
        sofr = sofr_by_date[observation_date]
        effr = effr_by_date[observation_date]

        history.append(
            FundingHistoryPoint(
                observation_date=observation_date,
                sofr=sofr,
                effr=effr,
                spread_basis_points=(
                    sofr - effr
                ) * Decimal("100"),
            )
        )

    return history