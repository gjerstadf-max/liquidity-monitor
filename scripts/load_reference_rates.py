from __future__ import annotations

from sqlalchemy import select

from backend.collectors.nyfed import (
    fetch_latest_effr,
    fetch_latest_sofr,
)
from backend.database.connection import get_session
from backend.database.models import Indicator, Observation


def load_observations(
    indicator_symbol: str,
    observations,
) -> tuple[int, int]:
    inserted = 0
    skipped = 0

    with get_session() as session:
        indicator = session.scalar(
            select(Indicator).where(
                Indicator.symbol == indicator_symbol
            )
        )

        if indicator is None:
            raise RuntimeError(
                f"Indicator not found in database: {indicator_symbol}"
            )

        for item in observations:
            existing = session.scalar(
                select(Observation).where(
                    Observation.indicator_id == indicator.id,
                    Observation.observation_date == item.observation_date,
                )
            )

            if existing is not None:
                skipped += 1
                continue

            observation = Observation(
                indicator_id=indicator.id,
                observation_date=item.observation_date,
                value=item.rate,
            )

            session.add(observation)
            inserted += 1

        session.commit()

    return inserted, skipped


def main() -> None:
    print("Loading New York Fed reference rates...\n")

    sofr = fetch_latest_sofr(100)
    effr = fetch_latest_effr(100)

    sofr_inserted, sofr_skipped = load_observations(
        "sofr",
        sofr,
    )

    effr_inserted, effr_skipped = load_observations(
        "effr",
        effr,
    )

    print(
        f"SOFR: inserted {sofr_inserted}, "
        f"skipped {sofr_skipped}"
    )

    print(
        f"EFFR: inserted {effr_inserted}, "
        f"skipped {effr_skipped}"
    )

    print("\nReference-rate load complete.")


if __name__ == "__main__":
    main()