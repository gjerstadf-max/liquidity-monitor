from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from backend.database.seed import (
    seed_database,
)

from backend.services.provider_refresh import (
    ProviderRefreshResult,
    refresh_fred_provider,
    refresh_nyfed_primary_dealers,
    refresh_nyfed_reference_rates,
    refresh_nyfed_reverse_repo,
)


# =============================================================
# PROVIDERS
# =============================================================


ProviderRefresher = Callable[
    [],
    ProviderRefreshResult,
]


PROVIDERS: tuple[
    tuple[
        str,
        ProviderRefresher,
    ],
    ...
] = (
    (
        "NY Fed Reference Rates",
        refresh_nyfed_reference_rates,
    ),
    (
        "NY Fed ON RRP",
        refresh_nyfed_reverse_repo,
    ),
    (
        "FRED Market Data",
        refresh_fred_provider,
    ),
    (
        "NY Fed Primary Dealers",
        refresh_nyfed_primary_dealers,
    ),
)


# =============================================================
# RESULT
# =============================================================


@dataclass(frozen=True)
class MarketDataRefreshResult:
    """
    Summary of one complete market-data refresh.
    """

    provider_results: tuple[
        ProviderRefreshResult,
        ...
    ]

    @property
    def provider_count(
        self,
    ) -> int:

        return len(
            self.provider_results
        )

    @property
    def series_count(
        self,
    ) -> int:

        return sum(
            len(
                result.series_results
            )

            for result
            in self.provider_results
        )

    @property
    def received(
        self,
    ) -> int:

        return sum(
            result.received

            for result
            in self.provider_results
        )

    @property
    def inserted(
        self,
    ) -> int:

        return sum(
            result.inserted

            for result
            in self.provider_results
        )

    @property
    def skipped(
        self,
    ) -> int:

        return sum(
            result.skipped

            for result
            in self.provider_results
        )


# =============================================================
# MARKET DATA REFRESH
# =============================================================


def refresh_market_data(
) -> MarketDataRefreshResult:
    """
    Refresh all production market-data providers.

    Provider implementations discover their active series
    from the central market-data catalog.

    This function knows which providers participate in the
    production refresh, but it does not know individual
    indicator symbols, external source IDs, transforms, or
    database-writing details.
    """

    print()

    print(
        "Liquidity Monitor — "
        "Market Data Refresh"
    )

    print(
        "=" * 72
    )

    # ---------------------------------------------------------
    # VERIFY CATALOG / DATABASE
    # ---------------------------------------------------------

    seed_database()

    print()

    print(
        "Indicator catalog: COMPLETE"
    )

    # ---------------------------------------------------------
    # REFRESH PROVIDERS
    # ---------------------------------------------------------

    results: list[
        ProviderRefreshResult
    ] = []

    completed: list[
        str
    ] = []

    for (
        provider_name,
        refresher,
    ) in PROVIDERS:

        try:

            result = (
                refresher()
            )

        except Exception as exc:

            print()

            print(
                "=" * 72
            )

            print(
                "MARKET DATA REFRESH FAILED"
            )

            print(
                "=" * 72
            )

            print()

            print(
                "Failed provider: "
                f"{provider_name}"
            )

            print(
                "Error: "
                f"{exc}"
            )

            print()

            print(
                "Successfully completed:"
            )

            if completed:

                for name in completed:

                    print(
                        f"  ✓ {name}"
                    )

            else:

                print(
                    "  None"
                )

            raise

        results.append(
            result
        )

        completed.append(
            provider_name
        )

    # ---------------------------------------------------------
    # RESULT
    # ---------------------------------------------------------

    refresh_result = (
        MarketDataRefreshResult(
            provider_results=
                tuple(
                    results
                )
        )
    )

    print()

    print(
        "=" * 72
    )

    print(
        "MARKET DATA REFRESH COMPLETE"
    )

    print(
        "=" * 72
    )

    print()

    print(
        "Providers: "
        f"{refresh_result.provider_count}"
    )

    print(
        "Catalog series refreshed: "
        f"{refresh_result.series_count}"
    )

    print(
        "Observations received: "
        f"{refresh_result.received}"
    )

    print(
        "Inserted: "
        f"{refresh_result.inserted}"
    )

    print(
        "Skipped: "
        f"{refresh_result.skipped}"
    )

    return refresh_result


# =============================================================
# DIRECT EXECUTION
# =============================================================


if __name__ == "__main__":
    refresh_market_data()