from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy import select

from backend.database.connection import (
    get_session,
)
from backend.database.models import (
    Indicator,
    Observation,
)


# =============================================================
# RESULT
# =============================================================


@dataclass(frozen=True)
class StoreResult:
    """
    Result of storing one normalized indicator series.
    """

    symbol: str

    received: int
    inserted: int
    skipped: int

    latest_date: date | None
    latest_value: Decimal | None


# =============================================================
# STORE VALUES
# =============================================================


def store_values(
    indicator_symbol: str,
    values: list[
        tuple[
            date,
            Decimal,
        ]
    ],
) -> StoreResult:
    """
    Store normalized date/value observations for one
    Liquidity Monitor indicator.

    Existing dates are skipped.

    This function knows nothing about the data provider.
    By the time values reach this layer they must already
    be normalized into the units specified by the
    Indicator catalog.
    """

    symbol = (
        indicator_symbol
        .strip()
        .lower()
    )


    if not symbol:

        raise ValueError(
            "indicator_symbol cannot be empty."
        )


    # ---------------------------------------------------------
    # NORMALIZE INPUT ORDER
    # ---------------------------------------------------------

    ordered_values = sorted(
        values,
        key=lambda item:
            item[0],
    )


    # ---------------------------------------------------------
    # EMPTY INPUT
    # ---------------------------------------------------------

    if not ordered_values:

        return StoreResult(
            symbol=
                symbol,

            received=
                0,

            inserted=
                0,

            skipped=
                0,

            latest_date=
                None,

            latest_value=
                None,
        )


    # ---------------------------------------------------------
    # DATABASE
    # ---------------------------------------------------------

    with get_session() as session:

        indicator = session.scalar(
            select(
                Indicator
            ).where(
                Indicator.symbol
                == symbol
            )
        )


        if indicator is None:

            raise RuntimeError(
                "Indicator not found "
                "in database: "
                f"{symbol}"
            )


        existing_dates = set(
            session.scalars(
                select(
                    Observation.observation_date
                ).where(
                    Observation.indicator_id
                    == indicator.id
                )
            ).all()
        )


        inserted = 0
        skipped = 0


        for (
            observation_date,
            value,
        ) in ordered_values:

            if (
                observation_date
                in existing_dates
            ):

                skipped += 1

                continue


            session.add(
                Observation(
                    indicator_id=
                        indicator.id,

                    observation_date=
                        observation_date,

                    value=
                        value,
                )
            )


            # Protect against duplicate dates within the
            # incoming payload as well as dates already
            # stored in the database.

            existing_dates.add(
                observation_date
            )


            inserted += 1


        session.commit()


    # ---------------------------------------------------------
    # RESULT
    # ---------------------------------------------------------

    latest_date, latest_value = (
        ordered_values[
            -1
        ]
    )


    return StoreResult(
        symbol=
            symbol,

        received=
            len(
                ordered_values
            ),

        inserted=
            inserted,

        skipped=
            skipped,

        latest_date=
            latest_date,

        latest_value=
            latest_value,
    )