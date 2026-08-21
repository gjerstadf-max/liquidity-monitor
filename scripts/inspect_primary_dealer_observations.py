from __future__ import annotations

from typing import Any

from backend.collectors.nyfed_primary_dealers import (
    fetch_primary_dealer_timeseries,
)


CURRENT_SERIES_BREAK = "SBN2024"


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
# GENERIC PAYLOAD INSPECTION
# =============================================================


def print_structure(
    value: Any,
    indent: int = 0,
    max_depth: int = 4,
) -> None:
    """
    Print the structure of a JSON payload without
    assuming the NY Fed observation schema in advance.
    """

    prefix = " " * indent


    if max_depth < 0:

        print(
            f"{prefix}..."
        )

        return


    if isinstance(
        value,
        dict,
    ):

        print(
            f"{prefix}dict "
            f"({len(value)} keys)"
        )


        for key, child in (
            value.items()
        ):

            print(
                f"{prefix}  {key}:"
            )

            print_structure(
                child,
                indent=
                    indent + 4,
                max_depth=
                    max_depth - 1,
            )


    elif isinstance(
        value,
        list,
    ):

        print(
            f"{prefix}list "
            f"({len(value)} items)"
        )


        if value:

            print(
                f"{prefix}  first item:"
            )

            print_structure(
                value[0],
                indent=
                    indent + 4,
                max_depth=
                    max_depth - 1,
            )


    else:

        print(
            f"{prefix}"
            f"{type(value).__name__}: "
            f"{value}"
        )


# =============================================================
# FIND RECORD LISTS
# =============================================================


def find_record_lists(
    value: Any,
    path: str = "root",
) -> list[
    tuple[
        str,
        list,
    ]
]:
    """
    Find lists inside the payload that appear to
    contain observation records.
    """

    matches = []


    if isinstance(
        value,
        dict,
    ):

        for key, child in (
            value.items()
        ):

            child_path = (
                f"{path}.{key}"
            )


            matches.extend(
                find_record_lists(
                    child,
                    path=
                        child_path,
                )
            )


    elif isinstance(
        value,
        list,
    ):

        if (
            value
            and
            isinstance(
                value[0],
                dict,
            )
        ):

            matches.append(
                (
                    path,
                    value,
                )
            )


        for index, child in enumerate(
            value[:3]
        ):

            matches.extend(
                find_record_lists(
                    child,
                    path=
                        f"{path}[{index}]",
                )
            )


    return matches


# =============================================================
# PRINT SAMPLE RECORDS
# =============================================================


def print_record_sample(
    records: list,
) -> None:

    print()
    print(
        f"Observation records: "
        f"{len(records)}"
    )


    if not records:

        return


    print()
    print(
        "FIRST RECORD"
    )

    print("-" * 100)


    for key, value in (
        records[0].items()
    ):

        print(
            f"{key:<30} "
            f"{value}"
        )


    if len(records) > 1:

        print()
        print(
            "LAST RECORD"
        )

        print("-" * 100)


        for key, value in (
            records[-1].items()
        ):

            print(
                f"{key:<30} "
                f"{value}"
            )


# =============================================================
# INSPECT ONE SERIES
# =============================================================


def inspect_series(
    label: str,
    key_id: str,
) -> None:

    print()
    print("=" * 110)

    print(
        label
    )

    print(
        f"Key: {key_id}"
    )

    print("=" * 110)


    payload = (
        fetch_primary_dealer_timeseries(
            key_id=
                key_id,

            series_break=
                CURRENT_SERIES_BREAK,
        )
    )


    print()
    print(
        "PAYLOAD STRUCTURE"
    )

    print("-" * 100)


    print_structure(
        payload
    )


    record_lists = (
        find_record_lists(
            payload
        )
    )


    print()
    print(
        "RECORD LIST CANDIDATES"
    )

    print("-" * 100)


    if not record_lists:

        print(
            "No list-of-dict observation "
            "structures found."
        )

        return


    for (
        path,
        records,
    ) in record_lists:

        print(
            f"{path:<60} "
            f"{len(records):>6} records"
        )


    # Use the largest list-of-dictionaries as the
    # likely observation history.

    observation_path, observations = max(
        record_lists,
        key=lambda item:
            len(
                item[1]
            ),
    )


    print()
    print(
        f"Selected observation path: "
        f"{observation_path}"
    )


    print_record_sample(
        observations
    )


# =============================================================
# MAIN
# =============================================================


def main() -> None:

    print()
    print(
        "Liquidity Monitor — "
        "Primary Dealer Observation Inspection"
    )

    print("=" * 110)


    for (
        label,
        key_id,
    ) in CORE_SERIES.items():

        try:

            inspect_series(
                label=
                    label,

                key_id=
                    key_id,
            )


        except Exception as exc:

            print()
            print(
                f"ERROR — {label}"
            )

            print(
                f"{type(exc).__name__}: "
                f"{exc}"
            )


    print()
    print("=" * 110)

    print(
        "Primary Dealer observation "
        "inspection complete."
    )

    print("=" * 110)


if __name__ == "__main__":
    main()