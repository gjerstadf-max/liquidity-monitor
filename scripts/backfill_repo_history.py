from __future__ import annotations

from datetime import date
from decimal import Decimal

import httpx

from backend.database.seed import (
    seed_database,
)
from scripts.load_reference_rates import (
    load_values,
)


# =============================================================
# OFR / NY FED REFERENCE-RATE HISTORY
# =============================================================

OFR_DATASET_URL = (
    "https://data.financialresearch.gov/"
    "v1/series/dataset"
)


START_DATE = date(
    2018,
    4,
    2,
)


# =============================================================
# DATABASE SYMBOL -> OFR MNEMONIC RULE
# =============================================================

SERIES_RULES = {
    "sofr": {
        "required": ["SOFR"],
        "excluded": [
            "Pctl",
            "_TV",
            "_UV",
        ],
    },

    "tgcr": {
        "required": ["TGCR"],
        "excluded": [
            "Pctl",
            "_TV",
            "_UV",
        ],
    },

    "bgcr": {
        "required": ["BGCR"],
        "excluded": [
            "Pctl",
            "_TV",
            "_UV",
        ],
    },

    "effr": {
        "required": ["EFFR"],
        "excluded": [
            "Pctl",
            "_TV",
            "_UV",
        ],
    },

    "obfr": {
        "required": ["OBFR"],
        "excluded": [
            "Pctl",
            "_TV",
            "_UV",
        ],
    },

    "sofr_p25": {
        "required": [
            "SOFR",
            "25Pctl",
        ],
        "excluded": [],
    },

    "sofr_p75": {
        "required": [
            "SOFR",
            "75Pctl",
        ],
        "excluded": [],
    },

    "sofr_p99": {
        "required": [
            "SOFR",
            "99Pctl",
        ],
        "excluded": [],
    },

    "sofr_volume": {
        "required": [
            "SOFR",
        ],

        # Volume series are resolved separately below.
        "excluded": [
            "Pctl",
        ],
    },
}


# =============================================================
# FETCH FULL OFR DATASET
# =============================================================


def fetch_ofr_reference_rates() -> dict:

    print()
    print(
        "Fetching historical FRBNY "
        "reference-rate dataset from OFR..."
    )


    response = httpx.get(
        OFR_DATASET_URL,

        params={
            "dataset":
                "fnyr",

            "vintage":
                "a",

            "start_date":
                START_DATE.isoformat(),

            "end_date":
                date.today().isoformat(),

            "remove_nulls":
                "true",

            "time_format":
                "date",
        },

        headers={
            "Accept":
                "application/json",

            "User-Agent":
                "LiquidityMonitor/0.1",
        },

        timeout=90.0,

        follow_redirects=True,
    )


    response.raise_for_status()


    payload = response.json()


    timeseries = payload.get(
        "timeseries"
    )


    if not isinstance(
        timeseries,
        dict,
    ):

        raise RuntimeError(
            "OFR response did not contain "
            "a timeseries dictionary."
        )


    print(
        f"Dataset contains "
        f"{len(timeseries)} series."
    )


    return timeseries


# =============================================================
# FIND SERIES
# =============================================================


def find_series_mnemonic(
    timeseries: dict,
    required: list[str],
    excluded: list[str],
) -> str | None:

    matches = []


    for mnemonic in timeseries:

        if not mnemonic.startswith(
            "FNYR-"
        ):
            continue


        if not all(
            token in mnemonic
            for token in required
        ):
            continue


        if any(
            token in mnemonic
            for token in excluded
        ):
            continue


        matches.append(
            mnemonic
        )


    if len(matches) == 1:

        return matches[0]


    if len(matches) > 1:

        # Prefer simple rate series ending in -A.
        simple = [
            mnemonic
            for mnemonic in matches
            if mnemonic.count("_") == 0
        ]


        if len(simple) == 1:

            return simple[0]


    return None


def find_sofr_volume_mnemonic(
    timeseries: dict,
) -> str | None:

    candidates = []


    for mnemonic in timeseries:

        if "SOFR" not in mnemonic:
            continue


        if "Pctl" in mnemonic:
            continue


        if (
            "_TV" in mnemonic
            or "_UV" in mnemonic
        ):

            candidates.append(
                mnemonic
            )


    if len(candidates) == 1:

        return candidates[0]


    # Prefer transaction volume if both
    # transaction and underlying volume exist.

    tv_candidates = [
        mnemonic
        for mnemonic in candidates
        if "_TV" in mnemonic
    ]


    if len(tv_candidates) == 1:

        return tv_candidates[0]


    return None


# =============================================================
# PARSE VALUES
# =============================================================


def extract_values(
    series_payload: dict,
) -> list[
    tuple[
        date,
        Decimal,
    ]
]:

    timeseries = (
        series_payload.get(
            "timeseries",
            {}
        )
    )


    aggregation = (
        timeseries.get(
            "aggregation",
            []
        )
    )


    values: list[
        tuple[
            date,
            Decimal,
        ]
    ] = []


    for point in aggregation:

        if (
            not isinstance(
                point,
                list,
            )
            or len(point) < 2
        ):
            continue


        raw_date = point[0]
        raw_value = point[1]


        if raw_value is None:
            continue


        try:

            observation_date = (
                date.fromisoformat(
                    str(raw_date)
                )
            )

            value = Decimal(
                str(raw_value)
            )

        except Exception:
            continue


        values.append(
            (
                observation_date,
                value,
            )
        )


    return values


# =============================================================
# LOAD ONE SERIES
# =============================================================


def load_ofr_series(
    db_symbol: str,
    mnemonic: str,
    timeseries: dict,
) -> None:

    payload = timeseries[
        mnemonic
    ]


    values = extract_values(
        payload
    )

    # OFR reference-rate volume is returned
    # in U.S. dollars. Liquidity Monitor stores
    # repo volume in USD billions to match the
    # live New York Fed collector.

    if db_symbol.endswith(
        "_volume"
    ):

        values = [
            (
                observation_date,
                value
                / Decimal("1000000000"),
            )

            for (
                observation_date,
                value,
            ) in values
        ]

    if not values:

        print(
            f"{db_symbol.upper():15} "
            f"{mnemonic}: no observations"
        )

        return


    inserted, skipped = (
        load_values(
            db_symbol,
            values,
        )
    )


    earliest = min(
        observation_date
        for observation_date, _
        in values
    )

    latest = max(
        observation_date
        for observation_date, _
        in values
    )


    print(
        f"{db_symbol.upper():15} "
        f"{mnemonic:<25} "
        f"{len(values):>5} observations   "
        f"{earliest} -> {latest}   "
        f"inserted={inserted} "
        f"skipped={skipped}"
    )


# =============================================================
# DIAGNOSTIC
# =============================================================


def print_available_sofr_series(
    timeseries: dict,
) -> None:

    print()
    print(
        "Available OFR SOFR series"
    )
    print("-" * 72)


    for mnemonic in sorted(
        timeseries
    ):

        if "SOFR" in mnemonic:

            print(
                mnemonic
            )


# =============================================================
# MAIN
# =============================================================


def main() -> None:

    print()
    print(
        "Liquidity Monitor — "
        "Repo Historical Backfill"
    )

    print("=" * 72)


    seed_database()


    timeseries = (
        fetch_ofr_reference_rates()
    )


    print_available_sofr_series(
        timeseries
    )


    print()
    print(
        "Loading historical repo data"
    )
    print("-" * 72)


    # ---------------------------------------------------------
    # CORE RATES + PERCENTILES
    # ---------------------------------------------------------

    for (
        db_symbol,
        rule,
    ) in SERIES_RULES.items():

        if db_symbol == "sofr_volume":
            continue


        mnemonic = (
            find_series_mnemonic(
                timeseries=
                    timeseries,

                required=
                    rule["required"],

                excluded=
                    rule["excluded"],
            )
        )


        if mnemonic is None:

            print(
                f"{db_symbol.upper():15} "
                "OFR series not resolved"
            )

            continue


        load_ofr_series(
            db_symbol=
                db_symbol,

            mnemonic=
                mnemonic,

            timeseries=
                timeseries,
        )


    # ---------------------------------------------------------
    # SOFR VOLUME
    # ---------------------------------------------------------

    volume_mnemonic = (
        find_sofr_volume_mnemonic(
            timeseries
        )
    )


    if volume_mnemonic is None:

        print(
            "SOFR_VOLUME     "
            "OFR volume series not resolved"
        )

    else:

        load_ofr_series(
            db_symbol=
                "sofr_volume",

            mnemonic=
                volume_mnemonic,

            timeseries=
                timeseries,
        )


    print()
    print("=" * 72)

    print(
        "Historical repo backfill complete."
    )

    print("=" * 72)


if __name__ == "__main__":
    main()