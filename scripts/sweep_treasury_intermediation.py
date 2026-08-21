from __future__ import annotations

import csv
from pathlib import Path

from backend.metrics.treasury_intermediation import (
    _load_intermediation_history,
    _metric_context,
)


OUTPUT_PATH = Path(
    "data/treasury_intermediation_history.csv"
)


# =============================================================
# BUILD FULL DIAGNOSTIC HISTORY
# =============================================================


def build_history() -> list[dict]:

    history = (
        _load_intermediation_history()
    )

    if len(history) < 52:
        raise RuntimeError(
            "At least 52 observations are required."
        )

    rows: list[dict] = []

    # Start when a complete trailing 52-week window exists.
    for index in range(
        51,
        len(history),
    ):

        available = (
            history[
                : index + 1
            ]
        )

        current_snapshot = (
            available[
                -1
            ]
        )

        positions = (
            _metric_context(
                [
                    item.dealer_positions_billions
                    for item in available
                ]
            )
        )

        transactions = (
            _metric_context(
                [
                    item.treasury_transactions_billions
                    for item in available
                ]
            )
        )

        borrowed = (
            _metric_context(
                [
                    item.securities_borrowed_billions
                    for item in available
                ]
            )
        )

        fails_receive = (
            _metric_context(
                [
                    item.fails_receive_billions
                    for item in available
                ]
            )
        )

        fails_deliver = (
            _metric_context(
                [
                    item.fails_deliver_billions
                    for item in available
                ]
            )
        )

        total_fails = (
            _metric_context(
                [
                    item.total_fails_billions
                    for item in available
                ]
            )
        )

        rows.append(
            {
                "observation_date":
                    current_snapshot.observation_date,

                # ---------------------------------------------
                # DEALER POSITIONS
                # ---------------------------------------------

                "positions":
                    float(
                        positions.current
                    ),

                "positions_change_4w":
                    float(
                        positions.change_4_week
                    ),

                "positions_change_13w":
                    float(
                        positions.change_13_week
                    ),

                "positions_pct_52w":
                    positions.percentile_52_week,

                "positions_z_52w":
                    positions.zscore_52_week,

                # ---------------------------------------------
                # TRANSACTIONS
                # ---------------------------------------------

                "transactions":
                    float(
                        transactions.current
                    ),

                "transactions_change_4w":
                    float(
                        transactions.change_4_week
                    ),

                "transactions_change_13w":
                    float(
                        transactions.change_13_week
                    ),

                "transactions_pct_52w":
                    transactions.percentile_52_week,

                "transactions_z_52w":
                    transactions.zscore_52_week,

                # ---------------------------------------------
                # SECURITIES BORROWED
                # ---------------------------------------------

                "borrowed":
                    float(
                        borrowed.current
                    ),

                "borrowed_change_4w":
                    float(
                        borrowed.change_4_week
                    ),

                "borrowed_change_13w":
                    float(
                        borrowed.change_13_week
                    ),

                "borrowed_pct_52w":
                    borrowed.percentile_52_week,

                "borrowed_z_52w":
                    borrowed.zscore_52_week,

                # ---------------------------------------------
                # FAILS TO RECEIVE
                # ---------------------------------------------

                "fails_receive":
                    float(
                        fails_receive.current
                    ),

                "fails_receive_change_4w":
                    float(
                        fails_receive.change_4_week
                    ),

                "fails_receive_pct_52w":
                    fails_receive.percentile_52_week,

                "fails_receive_z_52w":
                    fails_receive.zscore_52_week,

                # ---------------------------------------------
                # FAILS TO DELIVER
                # ---------------------------------------------

                "fails_deliver":
                    float(
                        fails_deliver.current
                    ),

                "fails_deliver_change_4w":
                    float(
                        fails_deliver.change_4_week
                    ),

                "fails_deliver_pct_52w":
                    fails_deliver.percentile_52_week,

                "fails_deliver_z_52w":
                    fails_deliver.zscore_52_week,

                # ---------------------------------------------
                # TOTAL FAILS
                # ---------------------------------------------

                "total_fails":
                    float(
                        total_fails.current
                    ),

                "total_fails_change_4w":
                    float(
                        total_fails.change_4_week
                    ),

                "total_fails_change_13w":
                    float(
                        total_fails.change_13_week
                    ),

                "total_fails_pct_52w":
                    total_fails.percentile_52_week,

                "total_fails_z_52w":
                    total_fails.zscore_52_week,

                # ---------------------------------------------
                # SUPPORTING FINANCING
                # ---------------------------------------------

                "repo":
                    (
                        float(
                            current_snapshot.repo_billions
                        )
                        if current_snapshot.repo_billions
                        is not None
                        else None
                    ),

                "reverse_repo":
                    (
                        float(
                            current_snapshot.reverse_repo_billions
                        )
                        if current_snapshot.reverse_repo_billions
                        is not None
                        else None
                    ),
            }
        )

    return rows


# =============================================================
# CSV
# =============================================================


def write_csv(
    rows: list[dict],
) -> None:

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT_PATH.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as handle:

        writer = csv.DictWriter(
            handle,
            fieldnames=list(
                rows[
                    0
                ].keys()
            ),
        )

        writer.writeheader()

        writer.writerows(
            rows
        )


# =============================================================
# DISPLAY HELPERS
# =============================================================


def print_ranked(
    rows: list[dict],
    title: str,
    metric: str,
    current_field: str,
    reverse: bool = True,
    limit: int = 15,
) -> None:

    ranked = sorted(
        rows,
        key=lambda row:
            row[
                metric
            ],
        reverse=reverse,
    )

    print()
    print(
        "=" * 100
    )

    print(
        title
    )

    print(
        "=" * 100
    )

    print(
        f"{'Date':<14}"
        f"{'Current':>14}"
        f"{'Z-score':>12}"
        f"{'Percentile':>14}"
    )

    print(
        "-" * 100
    )

    percentile_field = (
        metric.replace(
            "_z_52w",
            "_pct_52w",
        )
    )

    for row in ranked[
        :limit
    ]:

        print(
            f"{str(row['observation_date']):<14}"
            f"{row[current_field]:>14,.1f}"
            f"{row[metric]:>12.2f}"
            f"{row[percentile_field]:>13.0f}"
        )


# =============================================================
# EVENT WINDOWS
# =============================================================


EVENT_DATES = {
    "September 2019 Repo Stress":
        "2019-09-18",

    "March 2020 Treasury Stress":
        "2020-03-18",

    "March 2020 Aftermath":
        "2020-03-25",

    "2022 Treasury Volatility":
        "2022-10-12",

    "March 2023 Banking Stress":
        "2023-03-15",

    "October 2025":
        "2025-10-15",
}


def closest_row(
    rows: list[dict],
    target: str,
) -> dict | None:

    eligible = [
        row
        for row in rows
        if str(
            row[
                "observation_date"
            ]
        ) <= target
    ]

    if not eligible:
        return None

    return eligible[
        -1
    ]


def print_event_review(
    rows: list[dict],
) -> None:

    print()
    print(
        "=" * 115
    )

    print(
        "KNOWN MARKET-STRESS WINDOWS"
    )

    print(
        "=" * 115
    )

    print(
        f"{'Event':<32}"
        f"{'Date':<12}"
        f"{'Pos Z':>8}"
        f"{'Txn Z':>8}"
        f"{'Borrow Z':>10}"
        f"{'Fails Z':>10}"
    )

    print(
        "-" * 115
    )

    for (
        label,
        target_date,
    ) in EVENT_DATES.items():

        row = (
            closest_row(
                rows,
                target_date,
            )
        )

        if row is None:
            continue

        print(
            f"{label:<32}"
            f"{str(row['observation_date']):<12}"
            f"{row['positions_z_52w']:>8.2f}"
            f"{row['transactions_z_52w']:>8.2f}"
            f"{row['borrowed_z_52w']:>10.2f}"
            f"{row['total_fails_z_52w']:>10.2f}"
        )


# =============================================================
# CURRENT
# =============================================================


def print_current(
    rows: list[dict],
) -> None:

    row = (
        rows[
            -1
        ]
    )

    print()
    print(
        "=" * 100
    )

    print(
        "CURRENT TREASURY INTERMEDIATION"
    )

    print(
        "=" * 100
    )

    print(
        f"Observation date: "
        f"{row['observation_date']}"
    )

    print()

    print(
        f"Dealer positions       "
        f"${row['positions']:,.1f}B   "
        f"z={row['positions_z_52w']:+.2f}"
    )

    print(
        f"Treasury transactions  "
        f"${row['transactions']:,.1f}B   "
        f"z={row['transactions_z_52w']:+.2f}"
    )

    print(
        f"Securities borrowed    "
        f"${row['borrowed']:,.1f}B   "
        f"z={row['borrowed_z_52w']:+.2f}"
    )

    print(
        f"Total Treasury fails   "
        f"${row['total_fails']:,.1f}B   "
        f"z={row['total_fails_z_52w']:+.2f}"
    )


# =============================================================
# MAIN
# =============================================================


def main() -> None:

    print()
    print(
        "Liquidity Monitor — "
        "Treasury Intermediation Historical Sweep"
    )

    print(
        "=" * 100
    )

    rows = (
        build_history()
    )

    write_csv(
        rows
    )

    print()
    print(
        f"Historical observations analyzed: "
        f"{len(rows)}"
    )

    print(
        f"First diagnostic date: "
        f"{rows[0]['observation_date']}"
    )

    print(
        f"Latest diagnostic date: "
        f"{rows[-1]['observation_date']}"
    )

    print(
        f"CSV written to: "
        f"{OUTPUT_PATH}"
    )

    # ---------------------------------------------------------
    # POSITIONS
    # ---------------------------------------------------------

    print_ranked(
        rows,
        title=
            "HIGHEST DEALER POSITION Z-SCORES",

        metric=
            "positions_z_52w",

        current_field=
            "positions",

        reverse=True,
    )

    print_ranked(
        rows,
        title=
            "LOWEST DEALER POSITION Z-SCORES",

        metric=
            "positions_z_52w",

        current_field=
            "positions",

        reverse=False,
    )

    # ---------------------------------------------------------
    # TRANSACTIONS
    # ---------------------------------------------------------

    print_ranked(
        rows,
        title=
            "HIGHEST TREASURY TRANSACTION Z-SCORES",

        metric=
            "transactions_z_52w",

        current_field=
            "transactions",

        reverse=True,
    )

    # ---------------------------------------------------------
    # BORROWING
    # ---------------------------------------------------------

    print_ranked(
        rows,
        title=
            "HIGHEST SECURITIES-BORROWED Z-SCORES",

        metric=
            "borrowed_z_52w",

        current_field=
            "borrowed",

        reverse=True,
    )

    # ---------------------------------------------------------
    # SETTLEMENT FAILS
    # ---------------------------------------------------------

    print_ranked(
        rows,
        title=
            "HIGHEST TOTAL TREASURY FAILS Z-SCORES",

        metric=
            "total_fails_z_52w",

        current_field=
            "total_fails",

        reverse=True,
        limit=20,
    )

    # ---------------------------------------------------------
    # KNOWN EVENTS
    # ---------------------------------------------------------

    print_event_review(
        rows
    )

    # ---------------------------------------------------------
    # CURRENT
    # ---------------------------------------------------------

    print_current(
        rows
    )

    print()
    print(
        "=" * 100
    )

    print(
        "Treasury Intermediation historical "
        "sweep complete."
    )

    print(
        "=" * 100
    )


if __name__ == "__main__":
    main()