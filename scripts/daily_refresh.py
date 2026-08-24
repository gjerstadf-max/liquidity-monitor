from __future__ import annotations

from datetime import (
    datetime,
    timezone,
)

from backend.services.market_data_refresh import (
    refresh_market_data,
)


# =============================================================
# DAILY REFRESH
# =============================================================


def daily_refresh() -> None:
    """
    Run the Liquidity Monitor production
    market-data refresh.

    Individual providers and their catalog-defined
    series are managed by refresh_market_data().

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

    print(
        "=" * 72
    )

    print(
        "Started: "
        f"{started_at.isoformat()}"
    )

    # ---------------------------------------------------------
    # MARKET DATA
    # ---------------------------------------------------------

    try:

        result = (
            refresh_market_data()
        )

    except Exception as exc:

        print()

        print(
            "=" * 72
        )

        print(
            "DAILY REFRESH FAILED"
        )

        print(
            "=" * 72
        )

        print()

        print(
            f"Error: {exc}"
        )

        raise

    # ---------------------------------------------------------
    # COMPLETE
    # ---------------------------------------------------------

    completed_at = datetime.now(
        timezone.utc
    )

    print()

    print(
        "=" * 72
    )

    print(
        "DAILY REFRESH COMPLETE"
    )

    print(
        "=" * 72
    )

    print()

    print(
        "Providers refreshed: "
        f"{result.provider_count}"
    )

    print(
        "Catalog series refreshed: "
        f"{result.series_count}"
    )

    print(
        "Observations inserted: "
        f"{result.inserted}"
    )

    print(
        "Observations skipped: "
        f"{result.skipped}"
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