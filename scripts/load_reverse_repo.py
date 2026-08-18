from decimal import Decimal

from sqlalchemy import select

from backend.collectors.nyfed_rrp import (
    fetch_latest_reverse_repo,
)
from backend.database.connection import get_session
from backend.database.models import (
    Indicator,
    Observation,
)


INDICATOR_SYMBOL = "on_rrp"


def load_reverse_repo(
    observation_count: int = 400,
) -> None:
    """
    Fetch recent New York Fed ON RRP observations
    and persist new dates to SQLite.

    Values are stored in USD billions.
    """

    observations = fetch_latest_reverse_repo(
        observation_count
    )

    if not observations:
        raise RuntimeError(
            "No ON RRP observations returned."
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
                "ON RRP indicator not found. "
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
                item.operation_date
                in existing_dates
            ):
                skipped += 1
                continue

            value_billions = (
                item.total_accepted_dollars
                / Decimal("1000000000")
            )

            observation = Observation(
                indicator_id=indicator.id,
                observation_date=item.operation_date,
                value=value_billions,
            )

            session.add(observation)

            existing_dates.add(
                item.operation_date
            )

            inserted += 1

        session.commit()


    print()
    print("ON RRP Ingestion")
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
        latest.total_accepted_dollars
        / Decimal("1000000000")
    )

    print()
    print(
        f"Latest Date:   "
        f"{latest.operation_date}"
    )

    print(
        f"Latest ON RRP: "
        f"${latest_billions:,.3f} billion"
    )


if __name__ == "__main__":
    load_reverse_repo()