from __future__ import annotations

from sqlalchemy import select

from backend.catalog.series import (
    SERIES_CATALOG,
    validate_series_catalog,
)
from backend.database.connection import (
    get_session,
)
from backend.database.models import (
    Indicator,
)


# =============================================================
# EXPECTED DATABASE FIELDS
# =============================================================


DATABASE_FIELDS = (
    "name",
    "category",
    "frequency",
    "units",
    "active",
)


# =============================================================
# MAIN
# =============================================================


def main() -> None:

    print()

    print(
        "Liquidity Monitor Series Catalog"
    )

    print(
        "================================"
    )


    # =========================================================
    # VALIDATE CATALOG STRUCTURE
    # =========================================================

    validate_series_catalog()


    catalog_by_symbol = {
        series.symbol:
            series

        for series in SERIES_CATALOG
    }


    catalog_symbols = set(
        catalog_by_symbol
    )


    # =========================================================
    # LOAD DATABASE INDICATORS
    # =========================================================

    with get_session() as session:

        indicators = (
            session.scalars(
                select(
                    Indicator
                )
            ).all()
        )


    database_by_symbol = {
        indicator.symbol:
            indicator

        for indicator in indicators
    }


    database_symbols = set(
        database_by_symbol
    )


    # =========================================================
    # SYMBOL RECONCILIATION
    # =========================================================

    missing_from_database = (
        catalog_symbols
        - database_symbols
    )


    missing_from_catalog = (
        database_symbols
        - catalog_symbols
    )


    # =========================================================
    # METADATA RECONCILIATION
    # =========================================================

    metadata_mismatches: list[
        tuple[
            str,
            str,
            object,
            object,
        ]
    ] = []


    common_symbols = (
        catalog_symbols
        & database_symbols
    )


    for symbol in sorted(
        common_symbols
    ):

        catalog_series = (
            catalog_by_symbol[
                symbol
            ]
        )

        database_indicator = (
            database_by_symbol[
                symbol
            ]
        )


        for field_name in DATABASE_FIELDS:

            expected = getattr(
                catalog_series,
                field_name,
            )

            actual = getattr(
                database_indicator,
                field_name,
            )


            if actual != expected:

                metadata_mismatches.append(
                    (
                        symbol,
                        field_name,
                        expected,
                        actual,
                    )
                )


    # =========================================================
    # SUMMARY
    # =========================================================

    print()

    print(
        "Catalog series: "
        f"{len(catalog_symbols)}"
    )

    print(
        "Database indicators: "
        f"{len(database_symbols)}"
    )


    # =========================================================
    # PROVIDER BREAKDOWN
    # =========================================================

    print()

    print(
        "Provider breakdown"
    )

    print(
        "--------------------------------"
    )


    providers = sorted(
        {
            series.provider

            for series in SERIES_CATALOG
        }
    )


    for provider in providers:

        count = sum(
            1

            for series in SERIES_CATALOG

            if series.provider
            == provider
        )


        print(
            f"{provider:<28} "
            f"{count:>3}"
        )


    # =========================================================
    # ROLE BREAKDOWN
    # =========================================================

    print()

    print(
        "Role breakdown"
    )

    print(
        "--------------------------------"
    )


    for role in (
        "core",
        "supporting",
        "research",
    ):

        count = sum(
            1

            for series in SERIES_CATALOG

            if series.role == role
        )


        print(
            f"{role:<28} "
            f"{count:>3}"
        )


    # =========================================================
    # DIFFERENCES
    # =========================================================

    if missing_from_database:

        print()

        print(
            "Catalog series missing "
            "from database:"
        )


        for symbol in sorted(
            missing_from_database
        ):

            print(
                f"  - {symbol}"
            )


    if missing_from_catalog:

        print()

        print(
            "Database indicators missing "
            "from catalog:"
        )


        for symbol in sorted(
            missing_from_catalog
        ):

            print(
                f"  - {symbol}"
            )


    # =========================================================
    # METADATA DIFFERENCES
    # =========================================================

    print()

    print(
        "Metadata mismatches: "
        f"{len(metadata_mismatches)}"
    )


    if metadata_mismatches:

        print()

        print(
            "Metadata differences"
        )

        print(
            "--------------------------------"
        )


        for (
            symbol,
            field_name,
            expected,
            actual,
        ) in metadata_mismatches:

            print(
                f"{symbol}.{field_name}"
            )

            print(
                f"    catalog:  {expected!r}"
            )

            print(
                f"    database: {actual!r}"
            )


    # =========================================================
    # FINAL RESULT
    # =========================================================

    print()


    failed = any(
        (
            missing_from_database,
            missing_from_catalog,
            metadata_mismatches,
        )
    )


    if failed:

        print(
            "RESULT: RECONCILIATION FAILED"
        )

        raise SystemExit(
            1
        )


    print(
        "RESULT: EXACT MATCH"
    )

    print(
        "Symbols and stored indicator metadata "
        "match the market-data catalog."
    )

    print()


if __name__ == "__main__":

    main()