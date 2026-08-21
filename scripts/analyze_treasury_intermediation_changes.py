from __future__ import annotations

from datetime import date, timedelta
from statistics import mean, pstdev

from backend.metrics.treasury_intermediation import (
    _load_intermediation_history,
)


# =============================================================
# KNOWN EVENT DATES
# =============================================================


EVENTS = {

    "September 2019 Repo Stress":
        date(2019, 9, 17),

    "March 2020 Treasury Stress":
        date(2020, 3, 18),

    "2022 Treasury Volatility":
        date(2022, 10, 12),

    "March 2023 Banking Stress":
        date(2023, 3, 15),

    "October 2025 Liquidity Stress":
        date(2025, 10, 16),
}


# =============================================================
# HELPERS
# =============================================================


def rolling_zscore(
    values: list[float],
) -> float:
    """
    Calculate z-score of the latest observation
    against the latest 52 observations.
    """

    if len(values) < 52:
        raise RuntimeError(
            "At least 52 observations required."
        )

    window = values[-52:]

    current = window[-1]

    avg = mean(window)

    std = pstdev(window)

    if std == 0:
        return 0.0

    return (
        current - avg
    ) / std


def rolling_percentile(
    values: list[float],
) -> float:

    if len(values) < 52:
        raise RuntimeError(
            "At least 52 observations required."
        )

    window = values[-52:]

    current = window[-1]

    below_or_equal = sum(
        1
        for value in window
        if value <= current
    )

    return (
        below_or_equal
        / len(window)
        * 100
    )


# =============================================================
# BUILD CHANGE HISTORY
# =============================================================


def build_change_history() -> list[dict]:

    history = (
        _load_intermediation_history()
    )

    raw_rows: list[dict] = []

    # Need at least 13 weeks to calculate both
    # 4-week and 13-week changes.

    for index in range(
        13,
        len(history),
    ):

        current = history[index]

        four_week = (
            history[
                index - 4
            ]
        )

        thirteen_week = (
            history[
                index - 13
            ]
        )

        raw_rows.append(
            {
                "observation_date":
                    current.observation_date,

                # ---------------------------------------------
                # POSITIONS
                # ---------------------------------------------

                "positions":
                    float(
                        current.dealer_positions_billions
                    ),

                "positions_change_4w":
                    float(
                        current.dealer_positions_billions
                        -
                        four_week.dealer_positions_billions
                    ),

                "positions_change_13w":
                    float(
                        current.dealer_positions_billions
                        -
                        thirteen_week.dealer_positions_billions
                    ),

                # ---------------------------------------------
                # TRANSACTIONS
                # ---------------------------------------------

                "transactions":
                    float(
                        current.treasury_transactions_billions
                    ),

                "transactions_change_4w":
                    float(
                        current.treasury_transactions_billions
                        -
                        four_week.treasury_transactions_billions
                    ),

                "transactions_change_13w":
                    float(
                        current.treasury_transactions_billions
                        -
                        thirteen_week.treasury_transactions_billions
                    ),

                # ---------------------------------------------
                # SECURITIES BORROWED
                # ---------------------------------------------

                "borrowed":
                    float(
                        current.securities_borrowed_billions
                    ),

                "borrowed_change_4w":
                    float(
                        current.securities_borrowed_billions
                        -
                        four_week.securities_borrowed_billions
                    ),

                "borrowed_change_13w":
                    float(
                        current.securities_borrowed_billions
                        -
                        thirteen_week.securities_borrowed_billions
                    ),

                # ---------------------------------------------
                # TOTAL FAILS
                # ---------------------------------------------

                "total_fails":
                    float(
                        current.total_fails_billions
                    ),

                "fails_change_4w":
                    float(
                        current.total_fails_billions
                        -
                        four_week.total_fails_billions
                    ),

                "fails_change_13w":
                    float(
                        current.total_fails_billions
                        -
                        thirteen_week.total_fails_billions
                    ),
            }
        )

    # =========================================================
    # ROLLING CONTEXT FOR CHANGES
    # =========================================================

    rows: list[dict] = []

    for index in range(
        51,
        len(raw_rows),
    ):

        available = (
            raw_rows[
                : index + 1
            ]
        )

        current = dict(
            available[
                -1
            ]
        )

        metrics = [
            "positions_change_4w",
            "positions_change_13w",

            "transactions_change_4w",
            "transactions_change_13w",

            "borrowed_change_4w",
            "borrowed_change_13w",

            "fails_change_4w",
            "fails_change_13w",
        ]

        for metric in metrics:

            values = [
                row[
                    metric
                ]
                for row in available
            ]

            current[
                f"{metric}_z"
            ] = rolling_zscore(
                values
            )

            current[
                f"{metric}_pct"
            ] = rolling_percentile(
                values
            )

        rows.append(
            current
        )

    return rows


# =============================================================
# RANKINGS
# =============================================================


def print_top_changes(
    rows: list[dict],
    title: str,
    metric: str,
    limit: int = 15,
    absolute: bool = False,
) -> None:

    if absolute:

        ranked = sorted(
            rows,
            key=lambda row:
                abs(
                    row[
                        f"{metric}_z"
                    ]
                ),
            reverse=True,
        )

    else:

        ranked = sorted(
            rows,
            key=lambda row:
                row[
                    f"{metric}_z"
                ],
            reverse=True,
        )

    print()
    print("=" * 105)

    print(title)

    print("=" * 105)

    print(
        f"{'Date':<14}"
        f"{'Change':>15}"
        f"{'Z-score':>12}"
        f"{'Percentile':>14}"
    )

    print("-" * 105)

    for row in ranked[
        :limit
    ]:

        print(
            f"{str(row['observation_date']):<14}"
            f"{row[metric]:>+15,.1f}"
            f"{row[f'{metric}_z']:>12.2f}"
            f"{row[f'{metric}_pct']:>13.0f}"
        )


# =============================================================
# EVENT WINDOWS
# =============================================================


def event_window(
    rows: list[dict],
    event_date: date,
    days: int = 28,
) -> list[dict]:

    start = (
        event_date
        -
        timedelta(
            days=days
        )
    )

    end = (
        event_date
        +
        timedelta(
            days=days
        )
    )

    return [
        row
        for row in rows
        if (
            row[
                "observation_date"
            ]
            >= start

            and

            row[
                "observation_date"
            ]
            <= end
        )
    ]


def max_positive(
    rows: list[dict],
    metric: str,
) -> tuple[
    date,
    float,
]:
    row = max(
        rows,
        key=lambda item:
            item[
                metric
            ],
    )

    return (
        row[
            "observation_date"
        ],
        row[
            metric
        ],
    )


def max_absolute(
    rows: list[dict],
    metric: str,
) -> tuple[
    date,
    float,
]:
    row = max(
        rows,
        key=lambda item:
            abs(
                item[
                    metric
                ]
            ),
    )

    return (
        row[
            "observation_date"
        ],
        row[
            metric
        ],
    )


def print_event_windows(
    rows: list[dict],
) -> None:

    print()
    print("=" * 125)

    print(
        "KNOWN EVENT WINDOWS — MAXIMUM 4-WEEK CHANGE Z-SCORE "
        "WITHIN ±4 WEEKS"
    )

    print("=" * 125)

    print(
        f"{'Event':<32}"
        f"{'Position':>18}"
        f"{'Transactions':>18}"
        f"{'Borrowed':>18}"
        f"{'Fails':>18}"
    )

    print("-" * 125)

    for (
        label,
        event_date,
    ) in EVENTS.items():

        window = (
            event_window(
                rows,
                event_date,
            )
        )

        if not window:
            continue

        (
            position_date,
            position_z,
        ) = max_absolute(
            window,
            "positions_change_4w_z",
        )

        (
            transaction_date,
            transaction_z,
        ) = max_positive(
            window,
            "transactions_change_4w_z",
        )

        (
            borrowed_date,
            borrowed_z,
        ) = max_positive(
            window,
            "borrowed_change_4w_z",
        )

        (
            fails_date,
            fails_z,
        ) = max_positive(
            window,
            "fails_change_4w_z",
        )

        print(
            f"{label:<32}"
            f"{position_z:>+8.2f} "
            f"{str(position_date)[5:]:<9}"
            f"{transaction_z:>+8.2f} "
            f"{str(transaction_date)[5:]:<9}"
            f"{borrowed_z:>+8.2f} "
            f"{str(borrowed_date)[5:]:<9}"
            f"{fails_z:>+8.2f} "
            f"{str(fails_date)[5:]:<9}"
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
    print("=" * 100)

    print(
        "CURRENT 4-WEEK CHANGE DIAGNOSTICS"
    )

    print("=" * 100)

    print(
        f"Observation date: "
        f"{row['observation_date']}"
    )

    print()

    print(
        f"Dealer positions       "
        f"{row['positions_change_4w']:+,.1f}B   "
        f"z="
        f"{row['positions_change_4w_z']:+.2f}"
    )

    print(
        f"Treasury transactions  "
        f"{row['transactions_change_4w']:+,.1f}B   "
        f"z="
        f"{row['transactions_change_4w_z']:+.2f}"
    )

    print(
        f"Securities borrowed    "
        f"{row['borrowed_change_4w']:+,.1f}B   "
        f"z="
        f"{row['borrowed_change_4w_z']:+.2f}"
    )

    print(
        f"Total Treasury fails   "
        f"{row['fails_change_4w']:+,.1f}B   "
        f"z="
        f"{row['fails_change_4w_z']:+.2f}"
    )


# =============================================================
# MAIN
# =============================================================


def main() -> None:

    print()
    print(
        "Liquidity Monitor — "
        "Treasury Intermediation Change Analysis"
    )

    print("=" * 105)

    rows = (
        build_change_history()
    )

    print()
    print(
        f"Diagnostic observations: "
        f"{len(rows)}"
    )

    print(
        f"First date: "
        f"{rows[0]['observation_date']}"
    )

    print(
        f"Latest date: "
        f"{rows[-1]['observation_date']}"
    )

    # =========================================================
    # POSITION CHANGES
    # =========================================================

    print_top_changes(
        rows,
        title=
            "LARGEST ABSOLUTE 4-WEEK "
            "DEALER POSITION MOVES",

        metric=
            "positions_change_4w",

        absolute=True,
    )

    # =========================================================
    # TRANSACTIONS
    # =========================================================

    print_top_changes(
        rows,
        title=
            "LARGEST POSITIVE 4-WEEK "
            "TREASURY TRANSACTION MOVES",

        metric=
            "transactions_change_4w",
    )

    # =========================================================
    # BORROWING
    # =========================================================

    print_top_changes(
        rows,
        title=
            "LARGEST POSITIVE 4-WEEK "
            "SECURITIES-BORROWED MOVES",

        metric=
            "borrowed_change_4w",
    )

    # =========================================================
    # FAILS
    # =========================================================

    print_top_changes(
        rows,
        title=
            "LARGEST POSITIVE 4-WEEK "
            "TREASURY FAILS MOVES",

        metric=
            "fails_change_4w",
    )

    # =========================================================
    # EVENTS
    # =========================================================

    print_event_windows(
        rows
    )

    # =========================================================
    # CURRENT
    # =========================================================

    print_current(
        rows
    )

    print()
    print("=" * 105)

    print(
        "Treasury Intermediation "
        "change analysis complete."
    )

    print("=" * 105)


if __name__ == "__main__":
    main()