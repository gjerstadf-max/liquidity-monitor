from __future__ import annotations

from sqlalchemy import select

from backend.database.connection import get_session
from backend.database.models import (
    DataSource,
    Indicator,
)


def seed_database() -> None:

    with get_session() as session:

        # =====================================================
        # NEW YORK FED DATA SOURCE
        # =====================================================

        ny_fed = session.scalar(
            select(DataSource).where(
                DataSource.short_name
                == "NY Fed"
            )
        )


        if ny_fed is None:

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

        else:

            print(
                "Data source already exists: "
                "NY Fed"
            )


        # =====================================================
        # INDICATORS
        # =====================================================

        indicator_definitions = [

            # -------------------------------------------------
            # CORE FUNDING RATES
            # -------------------------------------------------

            {
                "symbol": "sofr",
                "name": (
                    "Secured Overnight "
                    "Financing Rate"
                ),
                "category": "Funding",
                "frequency": "Daily",
                "units": "Percent",
            },

            {
                "symbol": "effr",
                "name": (
                    "Effective Federal "
                    "Funds Rate"
                ),
                "category": "Funding",
                "frequency": "Daily",
                "units": "Percent",
            },

            {
                "symbol": "obfr",
                "name": (
                    "Overnight Bank "
                    "Funding Rate"
                ),
                "category": "Funding",
                "frequency": "Daily",
                "units": "Percent",
            },


            # -------------------------------------------------
            # REPO REFERENCE RATES
            # -------------------------------------------------

            {
                "symbol": "tgcr",
                "name": (
                    "Tri-Party General "
                    "Collateral Rate"
                ),
                "category":
                    "Repo Market",
                "frequency":
                    "Daily",
                "units":
                    "Percent",
            },

            {
                "symbol": "bgcr",
                "name": (
                    "Broad General "
                    "Collateral Rate"
                ),
                "category":
                    "Repo Market",
                "frequency":
                    "Daily",
                "units":
                    "Percent",
            },


            # -------------------------------------------------
            # SOFR INTERNALS
            # -------------------------------------------------

            {
                "symbol":
                    "sofr_volume",

                "name":
                    "SOFR Transaction Volume",

                "category":
                    "Repo Market",

                "frequency":
                    "Daily",

                "units":
                    "USD Billions",
            },

            {
                "symbol":
                    "sofr_p1",

                "name":
                    "SOFR 1st Percentile",

                "category":
                    "Repo Market",

                "frequency":
                    "Daily",

                "units":
                    "Percent",
            },

            {
                "symbol":
                    "sofr_p25",

                "name":
                    "SOFR 25th Percentile",

                "category":
                    "Repo Market",

                "frequency":
                    "Daily",

                "units":
                    "Percent",
            },

            {
                "symbol":
                    "sofr_p75",

                "name":
                    "SOFR 75th Percentile",

                "category":
                    "Repo Market",

                "frequency":
                    "Daily",

                "units":
                    "Percent",
            },

            {
                "symbol":
                    "sofr_p99",

                "name":
                    "SOFR 99th Percentile",

                "category":
                    "Repo Market",

                "frequency":
                    "Daily",

                "units":
                    "Percent",
            },


            # -------------------------------------------------
            # TGCR INTERNALS
            # -------------------------------------------------

            {
                "symbol":
                    "tgcr_volume",

                "name":
                    "TGCR Transaction Volume",

                "category":
                    "Repo Market",

                "frequency":
                    "Daily",

                "units":
                    "USD Billions",
            },

            {
                "symbol":
                    "tgcr_p1",

                "name":
                    "TGCR 1st Percentile",

                "category":
                    "Repo Market",

                "frequency":
                    "Daily",

                "units":
                    "Percent",
            },

            {
                "symbol":
                    "tgcr_p25",

                "name":
                    "TGCR 25th Percentile",

                "category":
                    "Repo Market",

                "frequency":
                    "Daily",

                "units":
                    "Percent",
            },

            {
                "symbol":
                    "tgcr_p75",

                "name":
                    "TGCR 75th Percentile",

                "category":
                    "Repo Market",

                "frequency":
                    "Daily",

                "units":
                    "Percent",
            },

            {
                "symbol":
                    "tgcr_p99",

                "name":
                    "TGCR 99th Percentile",

                "category":
                    "Repo Market",

                "frequency":
                    "Daily",

                "units":
                    "Percent",
            },


            # -------------------------------------------------
            # BGCR INTERNALS
            # -------------------------------------------------

            {
                "symbol":
                    "bgcr_volume",

                "name":
                    "BGCR Transaction Volume",

                "category":
                    "Repo Market",

                "frequency":
                    "Daily",

                "units":
                    "USD Billions",
            },

            {
                "symbol":
                    "bgcr_p1",

                "name":
                    "BGCR 1st Percentile",

                "category":
                    "Repo Market",

                "frequency":
                    "Daily",

                "units":
                    "Percent",
            },

            {
                "symbol":
                    "bgcr_p25",

                "name":
                    "BGCR 25th Percentile",

                "category":
                    "Repo Market",

                "frequency":
                    "Daily",

                "units":
                    "Percent",
            },

            {
                "symbol":
                    "bgcr_p75",

                "name":
                    "BGCR 75th Percentile",

                "category":
                    "Repo Market",

                "frequency":
                    "Daily",

                "units":
                    "Percent",
            },

            {
                "symbol":
                    "bgcr_p99",

                "name":
                    "BGCR 99th Percentile",

                "category":
                    "Repo Market",

                "frequency":
                    "Daily",

                "units":
                    "Percent",
            },


            # -------------------------------------------------
            # SYSTEM LIQUIDITY
            # -------------------------------------------------

            {
                "symbol":
                    "reserve_balances",

                "name":
                    (
                        "Reserve Balances with "
                        "Federal Reserve Banks"
                    ),

                "category":
                    "Funding",

                "frequency":
                    "Daily",

                "units":
                    "USD Billions",
            },

            {
                "symbol":
                    "tga",

                "name":
                    (
                        "U.S. Treasury "
                        "General Account"
                    ),

                "category":
                    "Funding",

                "frequency":
                    "Daily",

                "units":
                    "USD Billions",
            },

            {
                "symbol":
                    "on_rrp",

                "name":
                    (
                        "Overnight Reverse "
                        "Repurchase Agreements"
                    ),

                "category":
                    "Funding",

                "frequency":
                    "Daily",

                "units":
                    "USD Billions",
            },
        ]


        # =====================================================
        # IDEMPOTENT INSERT
        # =====================================================

        for definition in (
            indicator_definitions
        ):

            existing = session.scalar(
                select(
                    Indicator
                ).where(
                    Indicator.symbol
                    == definition[
                        "symbol"
                    ]
                )
            )


            if existing is not None:

                print(
                    "Indicator already exists: "
                    f"{definition['symbol'].upper()}"
                )

                continue


            indicator = Indicator(
                symbol=
                    definition[
                        "symbol"
                    ],

                name=
                    definition[
                        "name"
                    ],

                category=
                    definition[
                        "category"
                    ],

                frequency=
                    definition[
                        "frequency"
                    ],

                units=
                    definition[
                        "units"
                    ],

                source_id=
                    ny_fed.id,

                active=True,
            )


            session.add(
                indicator
            )


            print(
                "Added indicator: "
                f"{definition['symbol'].upper()}"
            )


        session.commit()

        print()
        print(
            "Database seed complete."
        )


if __name__ == "__main__":
    seed_database()