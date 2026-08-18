from decimal import Decimal

from sqlalchemy import select

from backend.collectors.fred import fetch_tga
from backend.database.connection import get_session
from backend.database.models import (
    Indicator,
    Observation,
)


INDICATOR_SYMBOL = "tga"


def load_tga(
    observation_count: int = 100,
) -> None:
    """
    Fetch Treasury General Account observations from FRED
    and persist new observations to SQLite.

    WDTGAL is published in millions of dollars.
    Values are stored in USD billions.
    """

    observations = fetch_tga(
        observation_count
    )

    if not observations:
        raise RuntimeError(
            "No TGA observations returned."
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
                "TGA indicator not found. "
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

            # WDTGAL is millions.
            # Store as billions.
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

    latest = observations[0]

    latest_billions = (
        latest.value
        / Decimal("1000")
    )

    print()
    print("TGA Ingestion")
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

    print()

    print(
        f"Latest Date:   "
        f"{latest.observation_date}"
    )

    print(
        f"Latest TGA:    "
        f"${latest_billions:,.3f} billion"
    )


if __name__ == "__main__":
    load_tga()