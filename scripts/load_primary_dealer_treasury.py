from __future__ import annotations

from datetime import date
from decimal import (
    Decimal,
    InvalidOperation,
)

from backend.collectors.nyfed_primary_dealers import (
    fetch_primary_dealer_timeseries,
)
from backend.database.seed import (
    seed_database,
)
from scripts.load_reference_rates import (
    load_values,
)


# =============================================================
# CONFIGURATION
# =============================================================


CANONICAL_START_DATE = date(
    2013,
    4,
    3,
)


MILLIONS_TO_BILLIONS = (
    Decimal("1000")
)


# =============================================================
# SERIES MAP
# =============================================================


SERIES = {

    "pd_treasury_positions": {
        "key_id":
            "PDPOSGST-TOT",

        "role":
            "CORE",
    },

    "pd_treasury_transactions": {
        "key_id":
            "PDGSWOEXTTOT",

        "role":
            "CORE",
    },

    "pd_treasury_repo": {
        "key_id":
            "PDSORA-UTSETTOT",

        "role":
            "SUPPORTING",
    },

    "pd_treasury_reverse_repo": {
        "key_id":
            "PDSIRRA-UTSETTOT",

        "role":
            "SUPPORTING",
    },

    "pd_treasury_borrowed": {
        "key_id":
            "PDSIOSB-UTSETTOT",

        "role":
            "CORE",
    },

    "pd_treasury_lent": {
        "key_id":
            "PDSOOS-UTSETTOT",

        "role":
            "RESEARCH",
    },

    "pd_treasury_fails_receive": {
        "key_id":
            "PDFTR-USTET",

        "role":
            "CORE",
    },

    "pd_treasury_fails_deliver": {
        "key_id":
            "PDFTD-USTET",

        "role":
            "CORE",
    },
}


# =============================================================
# PARSE
# =============================================================


def extract_numeric_values(
    payload: dict,
) -> tuple[
    list[
        tuple[
            date,
            Decimal,
        ]
    ],
    int,
]:
    """
    Convert NY Fed Primary Dealer observations into
    Liquidity Monitor date/value observations.

    Source values are reported in USD millions.

    Liquidity Monitor stores them in USD billions.

    Suppressed observations ('*') are skipped and
    counted separately. They are NEVER interpreted
    as zero.
    """

    pd_payload = (
        payload.get(
            "pd"
        )
    )


    if not isinstance(
        pd_payload,
        dict,
    ):

        raise RuntimeError(
            "Primary Dealer response did not "
            "contain a pd object."
        )


    records = (
        pd_payload.get(
            "timeseries"
        )
    )


    if not isinstance(
        records,
        list,
    ):

        raise RuntimeError(
            "Primary Dealer response did not "
            "contain a timeseries list."
        )


    values: list[
        tuple[
            date,
            Decimal,
        ]
    ] = []


    suppressed = 0


    for record in records:

        if not isinstance(
            record,
            dict,
        ):
            continue


        raw_date = (
            record.get(
                "asofdate"
            )
        )


        raw_value = (
            record.get(
                "value"
            )
        )


        if raw_date is None:

            continue


        try:

            observation_date = (
                date.fromisoformat(
                    str(
                        raw_date
                    )
                )
            )

        except ValueError:

            continue


        if (
            observation_date
            < CANONICAL_START_DATE
        ):

            continue


        value_text = (
            ""
            if raw_value is None
            else str(
                raw_value
            ).strip()
        )


        # -----------------------------------------------------
        # SUPPRESSED / MISSING
        # -----------------------------------------------------

        if value_text in {
            "",
            "*",
            "NA",
            "N/A",
            "null",
            "None",
        }:

            suppressed += 1

            continue


        # -----------------------------------------------------
        # NUMERIC
        # -----------------------------------------------------

        try:

            value_millions = (
                Decimal(
                    value_text
                )
            )

        except (
            InvalidOperation,
            ValueError,
        ):

            suppressed += 1

            continue


        value_billions = (
            value_millions
            / MILLIONS_TO_BILLIONS
        )


        values.append(
            (
                observation_date,
                value_billions,
            )
        )


    return (
        sorted(
            values,
            key=lambda item:
                item[0],
        ),
        suppressed,
    )


# =============================================================
# LOAD ONE SERIES
# =============================================================


def load_primary_dealer_series(
    indicator_symbol: str,
    key_id: str,
    role: str,
) -> None:

    print()
    print("=" * 80)

    print(
        indicator_symbol.upper()
    )

    print(
        f"NY Fed key: {key_id}"
    )

    print(
        f"Factor role: {role}"
    )

    print("-" * 80)


    # No series break supplied.
    #
    # This retrieves the key across every reporting
    # regime in which the same key exists.

    payload = (
        fetch_primary_dealer_timeseries(
            key_id=
                key_id,

            series_break=
                None,
        )
    )


    (
        values,
        suppressed,
    ) = extract_numeric_values(
        payload
    )


    if not values:

        print(
            "No numeric observations "
            "available."
        )

        print(
            f"Suppressed/missing: "
            f"{suppressed}"
        )

        return


    inserted, skipped = (
        load_values(
            indicator_symbol,
            values,
        )
    )


    earliest = (
        values[
            0
        ][
            0
        ]
    )

    latest = (
        values[
            -1
        ][
            0
        ]
    )


    print(
        f"Numeric observations: "
        f"{len(values)}"
    )

    print(
        f"Suppressed/missing:    "
        f"{suppressed}"
    )

    print(
        f"Earliest:              "
        f"{earliest}"
    )

    print(
        f"Latest:                "
        f"{latest}"
    )

    print(
        f"Inserted:              "
        f"{inserted}"
    )

    print(
        f"Already present:       "
        f"{skipped}"
    )


# =============================================================
# MAIN
# =============================================================


def main() -> None:

    print()
    print(
        "Liquidity Monitor — "
        "Primary Dealer Treasury Loader"
    )

    print("=" * 80)

    print(
        f"Canonical history begins "
        f"{CANONICAL_START_DATE}."
    )

    print(
        "NY Fed USD millions are normalized "
        "to USD billions."
    )

    print(
        "Suppressed observations remain missing."
    )


    # Make sure indicators exist.

    seed_database()


    for (
        indicator_symbol,
        configuration,
    ) in SERIES.items():

        load_primary_dealer_series(
            indicator_symbol=
                indicator_symbol,

            key_id=
                configuration[
                    "key_id"
                ],

            role=
                configuration[
                    "role"
                ],
        )


    print()
    print("=" * 80)

    print(
        "Primary Dealer Treasury "
        "historical load complete."
    )

    print("=" * 80)


if __name__ == "__main__":
    main()