from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.catalog.series import (
    SERIES_CATALOG,
    validate_series_catalog,
)
from backend.database.connection import (
    get_session,
)
from backend.database.models import (
    DataSource,
    Indicator,
)


# =============================================================
# DATA SOURCE
# =============================================================


def _get_or_create_ny_fed(
    session: Session,
) -> DataSource:
    """
    Return the existing NY Fed data-source record,
    or create it if the database is being initialized
    for the first time.

    NOTE:
    Indicator.source_id currently preserves the
    application's existing single-source convention.

    Provider-specific source attribution will be handled
    separately from this structural refactor.
    """

    ny_fed = session.scalar(
        select(
            DataSource
        ).where(
            DataSource.short_name
            == "NY Fed"
        )
    )

    if ny_fed is not None:

        print(
            "Data source already exists: "
            "NY Fed"
        )

        return ny_fed


    ny_fed = DataSource(
        name=(
            "Federal Reserve Bank "
            "of New York"
        ),
        short_name="NY Fed",
        website=(
            "https://www.newyorkfed.org/"
        ),
        is_primary=True,
    )

    session.add(
        ny_fed
    )

    session.flush()

    print(
        "Added data source: NY Fed"
    )

    return ny_fed


# =============================================================
# INDICATOR SEEDING
# =============================================================


def _seed_indicators(
    session: Session,
    source: DataSource,
) -> None:
    """
    Ensure every catalog series has an Indicator row.

    Existing indicators are left unchanged.

    This preserves the idempotent behavior of the
    previous database seeder.
    """

    for definition in SERIES_CATALOG:

        existing = session.scalar(
            select(
                Indicator
            ).where(
                Indicator.symbol
                == definition.symbol
            )
        )


        if existing is not None:

            print(
                "Indicator already exists: "
                f"{definition.symbol.upper()}"
            )

            continue


        indicator = Indicator(
            symbol=
                definition.symbol,

            name=
                definition.name,

            category=
                definition.category,

            frequency=
                definition.frequency,

            units=
                definition.units,

            source_id=
                source.id,

            active=
                definition.active,
        )


        session.add(
            indicator
        )


        print(
            "Added indicator: "
            f"{definition.symbol.upper()}"
        )


# =============================================================
# PUBLIC SEED FUNCTION
# =============================================================


def seed_database() -> None:
    """
    Seed the Liquidity Monitor reference tables.

    The market-data catalog is now the canonical source
    for indicator definitions.

    Running this function repeatedly is safe.
    """

    validate_series_catalog()


    print()

    print(
        "Seeding Liquidity Monitor database"
    )

    print(
        "=================================="
    )


    with get_session() as session:

        source = (
            _get_or_create_ny_fed(
                session
            )
        )


        _seed_indicators(
            session=
                session,

            source=
                source,
        )


        session.commit()


    print()

    print(
        "Database seed complete."
    )

    print(
        f"Catalog indicators: "
        f"{len(SERIES_CATALOG)}"
    )

    print()


if __name__ == "__main__":

    seed_database()