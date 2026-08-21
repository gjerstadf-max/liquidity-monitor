from __future__ import annotations

import csv

from collections import Counter
from datetime import (
    date,
    timedelta,
)
from pathlib import Path

from backend.signals.treasury_intermediation import (
    TreasuryIntermediationDiagnostics,
    build_treasury_intermediation_diagnostics_history,
    evaluate_treasury_intermediation_diagnostics,
    treasury_intermediation_dimension_state,
)


OUTPUT_PATH = Path(
    "data/treasury_intermediation_signal_v1.csv"
)


# =============================================================
# EVENTS
# =============================================================


EVENTS = {

    "September 2019 Repo Stress":
        date(
            2019,
            9,
            17,
        ),

    "March 2020 Treasury Stress":
        date(
            2020,
            3,
            18,
        ),

    "2022 Treasury Volatility":
        date(
            2022,
            10,
            12,
        ),

    "March 2023 Banking Stress":
        date(
            2023,
            3,
            15,
        ),

    "October 2025 Liquidity Stress":
        date(
            2025,
            10,
            16,
        ),
}


SEVERITY_RANK = {
    "Normal": 0,
    "Watch": 1,
    "Warning": 2,
    "Critical": 3,
}


# =============================================================
# BUILD SIGNAL HISTORY
# =============================================================


def build_signal_history() -> list[dict]:

    diagnostics_history = (
        build_treasury_intermediation_diagnostics_history()
    )

    rows: list[dict] = []

    for diagnostics in diagnostics_history:

        signal = (
            evaluate_treasury_intermediation_diagnostics(
                diagnostics
            )
        )

        (
            elevated_dimensions,
            strong_dimensions,
        ) = (
            treasury_intermediation_dimension_state(
                diagnostics
            )
        )

        rows.append(
            {
                "observation_date":
                    diagnostics.observation_date,

                "severity":
                    signal.severity,

                "title":
                    signal.title,

                "balance_sheet_z":
                    diagnostics.balance_sheet_adjustment_z,

                "intermediation_load_z":
                    diagnostics.intermediation_load_z,

                "settlement_friction_z":
                    diagnostics.settlement_friction_z,

                "positions_change_4w_z":
                    diagnostics.positions_change_4w_z,

                "transactions_change_4w_z":
                    diagnostics.transactions_change_4w_z,

                "borrowed_change_4w_z":
                    diagnostics.borrowed_change_4w_z,

                "fails_change_4w_z":
                    diagnostics.fails_change_4w_z,

                "fails_level_z":
                    diagnostics.total_fails_z_52w,

                "dealer_positions":
                    diagnostics.dealer_positions_billions,

                "treasury_transactions":
                    diagnostics.treasury_transactions_billions,

                "securities_borrowed":
                    diagnostics.securities_borrowed_billions,

                "total_fails":
                    diagnostics.total_fails_billions,

                "elevated_dimensions":
                    "; ".join(
                        elevated_dimensions
                    ),

                "strong_dimensions":
                    "; ".join(
                        strong_dimensions
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
# DISTRIBUTION
# =============================================================


def print_distribution(
    rows: list[dict],
) -> None:

    counts = Counter(
        row[
            "severity"
        ]
        for row
        in rows
    )

    total = len(
        rows
    )

    print()
    print("=" * 90)

    print(
        "SIGNAL DISTRIBUTION"
    )

    print("=" * 90)

    print(
        f"{'Severity':<16}"
        f"{'Count':>10}"
        f"{'Percent':>14}"
    )

    print("-" * 90)

    for severity in [
        "Normal",
        "Watch",
        "Warning",
        "Critical",
    ]:

        count = (
            counts.get(
                severity,
                0,
            )
        )

        percentage = (
            count
            /
            total
            *
            100
        )

        print(
            f"{severity:<16}"
            f"{count:>10}"
            f"{percentage:>13.2f}%"
        )

    non_normal = (
        total
        -
        counts.get(
            "Normal",
            0,
        )
    )

    print("-" * 90)

    print(
        f"{'Non-Normal':<16}"
        f"{non_normal:>10}"
        f"{(non_normal / total * 100):>13.2f}%"
    )


# =============================================================
# PRINT SEVERITY DATES
# =============================================================


def print_severity_dates(
    rows: list[dict],
    severity: str,
) -> None:

    selected = [
        row
        for row
        in rows
        if row[
            "severity"
        ] == severity
    ]

    print()
    print("=" * 115)

    print(
        f"{severity.upper()} OBSERVATIONS"
    )

    print("=" * 115)

    if not selected:

        print(
            "None."
        )

        return

    print(
        f"{'Date':<14}"
        f"{'Balance':>12}"
        f"{'Load':>12}"
        f"{'Settlement':>14}"
        f"{'Dimensions':>12}"
    )

    print("-" * 115)

    for row in selected:

        dimensions = (
            len(
                [
                    item
                    for item
                    in row[
                        "elevated_dimensions"
                    ].split(
                        "; "
                    )
                    if item
                ]
            )
        )

        print(
            f"{str(row['observation_date']):<14}"
            f"{row['balance_sheet_z']:>12.2f}"
            f"{row['intermediation_load_z']:>12.2f}"
            f"{row['settlement_friction_z']:>14.2f}"
            f"{dimensions:>12}"
        )


# =============================================================
# EVENT WINDOW
# =============================================================


def event_window(
    rows: list[dict],
    event_date: date,
    days: int = 28,
) -> list[dict]:

    start_date = (
        event_date
        -
        timedelta(
            days=days
        )
    )

    end_date = (
        event_date
        +
        timedelta(
            days=days
        )
    )

    return [
        row
        for row
        in rows
        if (
            row[
                "observation_date"
            ]
            >= start_date

            and

            row[
                "observation_date"
            ]
            <= end_date
        )
    ]


def elevated_dimension_count(
    row: dict,
) -> int:

    text = (
        row[
            "elevated_dimensions"
        ]
    )

    if not text:
        return 0

    return len(
        [
            item
            for item
            in text.split(
                "; "
            )
            if item
        ]
    )


def strongest_event_row(
    window: list[dict],
) -> dict:

    return max(
        window,
        key=lambda row: (
            SEVERITY_RANK[
                row[
                    "severity"
                ]
            ],

            elevated_dimension_count(
                row
            ),

            row[
                "settlement_friction_z"
            ],

            row[
                "intermediation_load_z"
            ],

            row[
                "balance_sheet_z"
            ],
        ),
    )


def print_event_review(
    rows: list[dict],
) -> None:

    print()
    print("=" * 135)

    print(
        "KNOWN EVENT WINDOWS — "
        "STRONGEST SIGNAL WITHIN ±4 WEEKS"
    )

    print("=" * 135)

    print(
        f"{'Event':<34}"
        f"{'Signal Date':<14}"
        f"{'Severity':<12}"
        f"{'Balance':>10}"
        f"{'Load':>10}"
        f"{'Settlement':>12}"
    )

    print("-" * 135)

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

        strongest = (
            strongest_event_row(
                window
            )
        )

        print(
            f"{label:<34}"
            f"{str(strongest['observation_date']):<14}"
            f"{strongest['severity']:<12}"
            f"{strongest['balance_sheet_z']:>10.2f}"
            f"{strongest['intermediation_load_z']:>10.2f}"
            f"{strongest['settlement_friction_z']:>12.2f}"
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
        "CURRENT FACTOR #4"
    )

    print("=" * 100)

    print()

    print(
        f"Observation date: "
        f"{row['observation_date']}"
    )

    print(
        f"Severity:         "
        f"{row['severity']}"
    )

    print()

    print(
        f"Balance-sheet adjustment: "
        f"{row['balance_sheet_z']:+.2f}σ"
    )

    print(
        f"Intermediation load:       "
        f"{row['intermediation_load_z']:+.2f}σ"
    )

    print(
        f"Settlement friction:       "
        f"{row['settlement_friction_z']:+.2f}σ"
    )

    print()

    print(
        f"Elevated dimensions: "
        f"{row['elevated_dimensions'] or 'None'}"
    )


# =============================================================
# MAIN
# =============================================================


def main() -> None:

    print()
    print(
        "Liquidity Monitor — "
        "Treasury Intermediation Signal V1 Backtest"
    )

    print("=" * 100)

    rows = (
        build_signal_history()
    )

    write_csv(
        rows
    )

    print()
    print(
        f"Observations tested: "
        f"{len(rows)}"
    )

    print(
        f"First signal date: "
        f"{rows[0]['observation_date']}"
    )

    print(
        f"Latest signal date: "
        f"{rows[-1]['observation_date']}"
    )

    print(
        f"CSV written to: "
        f"{OUTPUT_PATH}"
    )

    # ---------------------------------------------------------
    # DISTRIBUTION
    # ---------------------------------------------------------

    print_distribution(
        rows
    )

    # ---------------------------------------------------------
    # CRITICAL
    # ---------------------------------------------------------

    print_severity_dates(
        rows,
        "Critical",
    )

    # ---------------------------------------------------------
    # WARNING
    # ---------------------------------------------------------

    print_severity_dates(
        rows,
        "Warning",
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
    print("=" * 100)

    print(
        "Treasury Intermediation V1 "
        "backtest complete."
    )

    print("=" * 100)


if __name__ == "__main__":
    main()