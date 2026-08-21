from __future__ import annotations

import subprocess
import sys
from datetime import datetime, timezone


# =============================================================
# DATA LOADERS
# =============================================================


LOADERS = [
    (
        "SOFR / EFFR",
        "scripts.load_reference_rates",
    ),
    (
        "ON RRP",
        "scripts.load_reverse_repo",
    ),
    (
        "Reserve Balances",
        "scripts.load_reserve_balances",
    ),
    (
        "Treasury General Account",
        "scripts.load_tga",
    ),
    (
        "Primary Dealer Treasury Data",
        "scripts.load_primary_dealer_treasury",
    ),
]


# =============================================================
# RUN ONE LOADER
# =============================================================


def run_loader(
    name: str,
    module: str,
) -> None:
    """
    Run one ingestion module using the
    current Python interpreter.

    Stop immediately if the loader fails.
    """

    print()
    print("=" * 60)

    print(
        f"Refreshing {name}"
    )

    print("=" * 60)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            module,
        ],
        check=False,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"{name} refresh failed "
            f"with exit code "
            f"{result.returncode}."
        )

    print()

    print(
        f"{name}: COMPLETE"
    )


# =============================================================
# DAILY REFRESH
# =============================================================


def daily_refresh() -> None:
    """
    Refresh all Liquidity Monitor data sources.

    Order:

        1. SOFR / EFFR
        2. ON RRP
        3. Reserve Balances
        4. Treasury General Account
        5. Primary Dealer Treasury Data

    Analytics do not require a separate refresh.

    Metrics, signals, assessments and commentary are
    calculated from the database when requested.
    """

    started_at = datetime.now(
        timezone.utc
    )

    print()

    print(
        "Liquidity Monitor Daily Refresh"
    )

    print("=" * 60)

    print(
        "Started: "
        f"{started_at.isoformat()}"
    )

    completed: list[str] = []

    # =========================================================
    # RUN LOADERS SEQUENTIALLY
    # =========================================================

    for name, module in LOADERS:

        try:
            run_loader(
                name=name,
                module=module,
            )

            completed.append(
                name
            )

        except Exception as exc:

            print()
            print("=" * 60)

            print(
                "DAILY REFRESH FAILED"
            )

            print("=" * 60)

            print()

            print(
                f"Failed component: "
                f"{name}"
            )

            print(
                f"Error: "
                f"{exc}"
            )

            print()

            print(
                "Successfully completed:"
            )

            if completed:

                for item in completed:
                    print(
                        f"  ✓ {item}"
                    )

            else:
                print(
                    "  None"
                )

            raise

    # =========================================================
    # COMPLETE
    # =========================================================

    completed_at = datetime.now(
        timezone.utc
    )

    print()
    print("=" * 60)

    print(
        "DAILY REFRESH COMPLETE"
    )

    print("=" * 60)

    print()

    for name in completed:
        print(
            f"✓ {name}"
        )

    print()

    print(
        "Completed: "
        f"{completed_at.isoformat()}"
    )


# =============================================================
# DIRECT EXECUTION
# =============================================================


if __name__ == "__main__":
    daily_refresh()