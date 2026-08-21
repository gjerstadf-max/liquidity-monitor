from __future__ import annotations

import csv
from pathlib import Path

from backend.signals.treasury_intermediation import (
    build_treasury_intermediation_diagnostics_history,
    evaluate_treasury_intermediation_diagnostics,
    treasury_intermediation_dimension_state,
)


OUTPUT_PATH = Path(
    "data/treasury_intermediation_alert_review.csv"
)


def main() -> None:

    diagnostics_history = (
        build_treasury_intermediation_diagnostics_history()
    )

    rows = []

    for diagnostics in diagnostics_history:

        signal = (
            evaluate_treasury_intermediation_diagnostics(
                diagnostics
            )
        )

        if signal.severity not in {
            "Warning",
            "Critical",
        }:
            continue

        (
            elevated,
            strong,
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

                "balance_sheet_z":
                    round(
                        diagnostics.balance_sheet_adjustment_z,
                        2,
                    ),

                "intermediation_load_z":
                    round(
                        diagnostics.intermediation_load_z,
                        2,
                    ),

                "settlement_friction_z":
                    round(
                        diagnostics.settlement_friction_z,
                        2,
                    ),

                "positions_change_4w_z":
                    round(
                        diagnostics.positions_change_4w_z,
                        2,
                    ),

                "transactions_change_4w_z":
                    round(
                        diagnostics.transactions_change_4w_z,
                        2,
                    ),

                "borrowed_change_4w_z":
                    round(
                        diagnostics.borrowed_change_4w_z,
                        2,
                    ),

                "fails_change_4w_z":
                    round(
                        diagnostics.fails_change_4w_z,
                        2,
                    ),

                "fails_level_z":
                    round(
                        diagnostics.total_fails_z_52w,
                        2,
                    ),

                "dealer_positions_billions":
                    round(
                        diagnostics.dealer_positions_billions,
                        1,
                    ),

                "treasury_transactions_billions":
                    round(
                        diagnostics.treasury_transactions_billions,
                        1,
                    ),

                "securities_borrowed_billions":
                    round(
                        diagnostics.securities_borrowed_billions,
                        1,
                    ),

                "total_fails_billions":
                    round(
                        diagnostics.total_fails_billions,
                        1,
                    ),

                "elevated_dimensions":
                    "; ".join(
                        elevated
                    ),

                "strong_dimensions":
                    "; ".join(
                        strong
                    ),

                # Human review fields
                "market_context":
                    "",

                "review_classification":
                    "",

                "review_notes":
                    "",
            }
        )

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
                rows[0].keys()
            ),
        )

        writer.writeheader()
        writer.writerows(
            rows
        )

    print()
    print(
        "Liquidity Monitor — "
        "Treasury Intermediation Alert Review"
    )

    print("=" * 115)

    print()
    print(
        f"Alert observations: {len(rows)}"
    )

    print(
        f"Review file: {OUTPUT_PATH}"
    )

    print()

    print(
        f"{'Date':<14}"
        f"{'Severity':<12}"
        f"{'Balance':>10}"
        f"{'Load':>10}"
        f"{'Settlement':>12}"
        f"{'Fails $B':>12}"
    )

    print("-" * 115)

    for row in rows:

        print(
            f"{str(row['observation_date']):<14}"
            f"{row['severity']:<12}"
            f"{row['balance_sheet_z']:>10.2f}"
            f"{row['intermediation_load_z']:>10.2f}"
            f"{row['settlement_friction_z']:>12.2f}"
            f"{row['total_fails_billions']:>12,.1f}"
        )

    print()
    print("=" * 115)

    print(
        "Review complete."
    )

    print("=" * 115)


if __name__ == "__main__":
    main()