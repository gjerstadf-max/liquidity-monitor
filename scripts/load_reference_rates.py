from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import select

from backend.collectors.nyfed import (
    ReferenceRateObservation,
    fetch_latest_bgcr,
    fetch_latest_effr,
    fetch_latest_obfr,
    fetch_latest_sofr,
    fetch_latest_tgcr,
)
from backend.database.connection import (
    get_session,
)
from backend.database.models import (
    Indicator,
    Observation,
)


# =============================================================
# GENERIC SERIES LOADER
# =============================================================


def load_values(
    indicator_symbol: str,
    values: list[
        tuple[
            date,
            Decimal,
        ]
    ],
) -> tuple[int, int]:
    """
    Store date/value observations for one indicator.

    Existing dates are skipped, making the loader
    safe to run repeatedly.
    """

    inserted = 0
    skipped = 0


    with get_session() as session:

        indicator = session.scalar(
            select(
                Indicator
            ).where(
                Indicator.symbol
                == indicator_symbol
            )
        )


        if indicator is None:

            raise RuntimeError(
                "Indicator not found "
                "in database: "
                f"{indicator_symbol}"
            )


        for (
            observation_date,
            value,
        ) in values:

            existing = session.scalar(
                select(
                    Observation
                ).where(
                    Observation.indicator_id
                    == indicator.id,

                    Observation.observation_date
                    == observation_date,
                )
            )


            if existing is not None:

                skipped += 1
                continue


            observation = Observation(
                indicator_id=
                    indicator.id,

                observation_date=
                    observation_date,

                value=
                    value,
            )


            session.add(
                observation
            )

            inserted += 1


        session.commit()


    return (
        inserted,
        skipped,
    )


# =============================================================
# FIELD EXTRACTION
# =============================================================


def extract_field(
    observations: list[
        ReferenceRateObservation
    ],
    field_name: str,
) -> list[
    tuple[
        date,
        Decimal,
    ]
]:
    """
    Extract one numeric field from a group
    of New York Fed observations.
    """

    values: list[
        tuple[
            date,
            Decimal,
        ]
    ] = []


    for observation in observations:

        value = getattr(
            observation,
            field_name,
        )


        if value is None:
            continue


        values.append(
            (
                observation.observation_date,
                value,
            )
        )


    return values


# =============================================================
# RATE FAMILY
# =============================================================


def load_reference_rate(
    indicator_symbol: str,
    observations: list[
        ReferenceRateObservation
    ],
) -> None:

    inserted, skipped = (
        load_values(
            indicator_symbol,
            extract_field(
                observations,
                "rate",
            ),
        )
    )


    print(
        f"{indicator_symbol.upper()}: "
        f"inserted {inserted}, "
        f"skipped {skipped}"
    )


# =============================================================
# SECURED REPO INTERNALS
# =============================================================


def load_repo_internals(
    prefix: str,
    observations: list[
        ReferenceRateObservation
    ],
) -> None:
    """
    Store transaction volume and published
    percentile observations for SOFR/TGCR/BGCR.
    """

    field_map = {
        f"{prefix}_volume":
            "volume_billions",

        f"{prefix}_p1":
            "percentile_1",

        f"{prefix}_p25":
            "percentile_25",

        f"{prefix}_p75":
            "percentile_75",

        f"{prefix}_p99":
            "percentile_99",
    }


    for (
        indicator_symbol,
        field_name,
    ) in field_map.items():

        values = extract_field(
            observations,
            field_name,
        )


        inserted, skipped = (
            load_values(
                indicator_symbol,
                values,
            )
        )


        print(
            f"{indicator_symbol.upper()}: "
            f"inserted {inserted}, "
            f"skipped {skipped}"
        )


# =============================================================
# MAIN
# =============================================================


def main() -> None:

    print()
    print(
        "Loading New York Fed "
        "reference rates..."
    )

    print("=" * 72)


    # ---------------------------------------------------------
    # FETCH
    # ---------------------------------------------------------

    sofr = fetch_latest_sofr(
        100
    )

    tgcr = fetch_latest_tgcr(
        100
    )

    bgcr = fetch_latest_bgcr(
        100
    )

    effr = fetch_latest_effr(
        100
    )

    obfr = fetch_latest_obfr(
        100
    )


    # ---------------------------------------------------------
    # CORE RATES
    # ---------------------------------------------------------

    print()
    print("Core Rates")
    print("-" * 72)


    load_reference_rate(
        "sofr",
        sofr,
    )

    load_reference_rate(
        "tgcr",
        tgcr,
    )

    load_reference_rate(
        "bgcr",
        bgcr,
    )

    load_reference_rate(
        "effr",
        effr,
    )

    load_reference_rate(
        "obfr",
        obfr,
    )


    # ---------------------------------------------------------
    # REPO DISTRIBUTIONS
    # ---------------------------------------------------------

    print()
    print("SOFR Internals")
    print("-" * 72)

    load_repo_internals(
        "sofr",
        sofr,
    )


    print()
    print("TGCR Internals")
    print("-" * 72)

    load_repo_internals(
        "tgcr",
        tgcr,
    )


    print()
    print("BGCR Internals")
    print("-" * 72)

    load_repo_internals(
        "bgcr",
        bgcr,
    )


    print()
    print(
        "Reference-rate load complete."
    )


if __name__ == "__main__":
    main()