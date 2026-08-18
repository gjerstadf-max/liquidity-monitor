from decimal import Decimal

from sqlalchemy import select

from backend.collectors.fred import (
    fetch_reserve_balances,
)
from backend.database.connection import get_session
from backend.database.models import (
    Indicator,
    Observation,
)


INDICATOR_SYMBOL = "reserve_balances"


def load_reserve_balances(
    observation_count: int = 100,
) -> None:
    """
    Fetch Federal Reserve reserve balances from FRED
    and persist new observations to SQLite.

    WRESBAL is published in millions of dollars.
    We store values in USD billions.
    """

    observations = fetch_reserve_balances(
        observation_count
    )

    if not observations:
        raise RuntimeError(
            "No reserve balance observations returned."
        )

    with get_session() as session:

        indicator = session.scalar(
            select(Indicator).where(
                Indicator.symbol
                == INDICATOR_SYMBOL
            )
        )

        if indicator is None:
            raise RuntimeError(
                "Reserve balances indicator not found. "
                "Run the database seed first."
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

        for item in observations:

            if (
                item.observation_date
                in existing_dates
            ):
                skipped += 1
                continue

            # WRESBAL is millions.
            # Convert to billions for storage.
            value_billions = (
                item.value
                / Decimal("1000")
            )

            observation = Observation(
                indicator_id=indicator.id,
                observation_date=item.observation_date,
                value=value_billions,
            )

            session.add(observation)

            existing_dates.add(
                item.observation_date
            )

            inserted += 1

        session.commit()

    print()
    print("Reserve Balance Ingestion")
    print("================================")

    print(
        f"Fetched:       "
        f"{len(observations)}"
    )

    print(
        f"Inserted:      "
        f"{inserted}"
    )

    print(
        f"Skipped:       "
        f"{skipped}"
    )

    latest = observations[0]

    latest_billions = (
        latest.value
        / Decimal("1000")
    )

    print()

    print(
        f"Latest Date:   "
        f"{latest.observation_date}"
    )

    print(
        f"Latest Level:  "
        f"${latest_billions:,.3f} billion"
    )


if __name__ == "__main__":
    load_reserve_balances()