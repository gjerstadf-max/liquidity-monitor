from __future__ import annotations

import subprocess
import sys
from datetime import datetime, timezone

from backend.database.seed import seed_database


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
    print(f"Refreshing {name}")
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
    print(f"{name}: COMPLETE")


# =============================================================
# DAILY REFRESH
# =============================================================


def daily_refresh() -> None:
    """
    Refresh all Liquidity Monitor data sources.

    The database indicator catalog is seeded first.
    Seeding is idempotent and ensures new indicators
    exist before any loader attempts to write data.

    Order:

        0. Seed / verify indicator catalog
        1. SOFR / EFFR
        2. ON RRP
        3. Reserve Balances
        4. Treasury General Account
        5. Primary Dealer Treasury Data

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

    # =========================================================
    # SEED INDICATOR CATALOG
    # =========================================================

    print()
    print("=" * 60)
    print(
        "Verifying indicator catalog"
    )
    print("=" * 60)

    try:

        seed_database()

    except Exception as exc:

        print()
        print("=" * 60)
        print(
            "DAILY REFRESH FAILED"
        )
        print("=" * 60)

        print()
        print(
            "Failed component: "
            "Indicator catalog"
        )

        print(
            f"Error: {exc}"
        )

        raise

    print()
    print(
        "Indicator catalog: COMPLETE"
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
    print(
        "✓ Indicator catalog"
    )

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