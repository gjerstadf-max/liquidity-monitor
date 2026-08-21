from __future__ import annotations

from backend.collectors.nyfed_primary_dealers import (
    PrimaryDealerSeries,
    fetch_primary_dealer_series_catalog,
)


CURRENT_SERIES_BREAK = "SBN2024"


# =============================================================
# CORE TREASURY INTERMEDIATION SERIES
# =============================================================

CORE_SERIES = {

    "Treasury Dealer Positions":
        "PDPOSGST-TOT",

    "Treasury Transactions":
        "PDGSWOEXTTOT",

    "Treasury Repo Financing":
        "PDSORA-UTSETTOT",

    "Treasury Reverse Repo Financing":
        "PDSIRRA-UTSETTOT",

    "Treasury Securities Borrowed":
        "PDSIOSB-UTSETTOT",

    "Treasury Securities Lent":
        "PDSOOS-UTSETTOT",

    "Treasury Fails to Receive":
        "PDFTR-USTET",

    "Treasury Fails to Deliver":
        "PDFTD-USTET",
}


# =============================================================
# LOOKUP
# =============================================================


def build_catalog_lookup(
    catalog: list[
        PrimaryDealerSeries
    ],
) -> dict[
    str,
    PrimaryDealerSeries,
]:

    return {
        item.key_id:
            item

        for item in catalog

        if item.series_break
        == CURRENT_SERIES_BREAK
    }


# =============================================================
# MAIN
# =============================================================


def main() -> None:

    print()
    print(
        "Liquidity Monitor — "
        "Primary Dealer Treasury Series Discovery"
    )

    print("=" * 110)


    catalog = (
        fetch_primary_dealer_series_catalog()
    )


    current_catalog = [
        item
        for item
        in catalog
        if item.series_break
        == CURRENT_SERIES_BREAK
    ]


    lookup = (
        build_catalog_lookup(
            catalog
        )
    )


    print()
    print(
        f"Series definitions returned: "
        f"{len(catalog)}"
    )

    print(
        f"Current {CURRENT_SERIES_BREAK} series: "
        f"{len(current_catalog)}"
    )


    print()
    print(
        "CORE TREASURY INTERMEDIATION SERIES"
    )

    print("-" * 110)


    missing = []


    for (
        label,
        key_id,
    ) in CORE_SERIES.items():

        series = (
            lookup.get(
                key_id
            )
        )


        if series is None:

            print(
                f"{label:<38} "
                f"{key_id:<25} "
                "NOT FOUND"
            )

            missing.append(
                key_id
            )

            continue


        print()
        print(
            f"{label}"
        )

        print(
            f"  Key:         "
            f"{series.key_id}"
        )

        print(
            f"  Series break:"
            f" {series.series_break}"
        )

        print(
            f"  Description: "
            f"{series.description}"
        )


    print()
    print("=" * 110)


    if missing:

        print(
            "WARNING — missing expected series:"
        )

        for key_id in missing:

            print(
                f"  {key_id}"
            )

    else:

        print(
            "All core Treasury intermediation "
            "series found."
        )


    print("=" * 110)


if __name__ == "__main__":
    main()