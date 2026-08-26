from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from backend.collectors.treasury_fiscaldata import (
    fetch_treasury_bill_auctions,
)
from backend.database.seed import (
    seed_database,
)
from backend.services.auction_store import (
    store_treasury_auctions,
)
from backend.services.provider_refresh import (
    ProviderRefreshResult,
    refresh_fred_provider,
    refresh_nyfed_primary_dealers,
    refresh_nyfed_reference_rates,
    refresh_nyfed_reverse_repo,
)


# =============================================================
# SCALAR SERIES PROVIDERS
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
# STRUCTURED DATA
# =============================================================


@dataclass(frozen=True)
class StructuredRefreshResult:
    """
    Summary of one structured market-data refresh.

    Structured datasets are not ordinary scalar
    Indicator/Observation series.
    """

    dataset: str

    received: int
    inserted: int
    updated: int
    skipped: int


StructuredRefresher = Callable[
    [],
    StructuredRefreshResult,
]


def refresh_treasury_auctions(
) -> StructuredRefreshResult:
    """
    Refresh recent Treasury bill auction records.

    Announced future auctions are retained so the same
    records can later be enriched when auction results
    become available.
    """

    print()
    print(
        "Treasury FiscalData — "
        "Bill Auctions"
    )
    print(
        "-" * 72
    )

    auctions = (
        fetch_treasury_bill_auctions(
            count=100,
            completed_only=False,
        )
    )

    result = (
        store_treasury_auctions(
            auctions
        )
    )

    print(
        "Records received: "
        f"{result.received}"
    )

    print(
        "Inserted: "
        f"{result.inserted}"
    )

    print(
        "Updated: "
        f"{result.updated}"
    )

    print(
        "Skipped: "
        f"{result.skipped}"
    )

    if (
        result.latest_auction_date
        is not None
    ):
        print(
            "Latest auction date: "
            f"{result.latest_auction_date}"
        )

    return StructuredRefreshResult(
        dataset=
            "Treasury Auctions",

        received=
            result.received,

        inserted=
            result.inserted,

        updated=
            result.updated,

        skipped=
            result.skipped,
    )


STRUCTURED_DATASETS: tuple[
    tuple[
        str,
        StructuredRefresher,
    ],
    ...
] = (
    (
        "Treasury Auctions",
        refresh_treasury_auctions,
    ),
)


# =============================================================
# RESULT
# =============================================================


@dataclass(frozen=True)
class MarketDataRefreshResult:
    """
    Summary of one complete market-data refresh.

    Scalar catalog series and structured datasets remain
    separate because they have different storage models.
    """

    provider_results: tuple[
        ProviderRefreshResult,
        ...
    ]

    structured_results: tuple[
        StructuredRefreshResult,
        ...
    ]

    # ---------------------------------------------------------
    # SCALAR PROVIDERS
    # ---------------------------------------------------------

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
        """
        Scalar observations received.
        """

        return sum(
            result.received

            for result
            in self.provider_results
        )

    @property
    def inserted(
        self,
    ) -> int:
        """
        Scalar observations inserted.
        """

        return sum(
            result.inserted

            for result
            in self.provider_results
        )

    @property
    def skipped(
        self,
    ) -> int:
        """
        Scalar observations skipped.
        """

        return sum(
            result.skipped

            for result
            in self.provider_results
        )

    # ---------------------------------------------------------
    # STRUCTURED DATASETS
    # ---------------------------------------------------------

    @property
    def structured_dataset_count(
        self,
    ) -> int:

        return len(
            self.structured_results
        )

    @property
    def structured_received(
        self,
    ) -> int:

        return sum(
            result.received

            for result
            in self.structured_results
        )

    @property
    def structured_inserted(
        self,
    ) -> int:

        return sum(
            result.inserted

            for result
            in self.structured_results
        )

    @property
    def structured_updated(
        self,
    ) -> int:

        return sum(
            result.updated

            for result
            in self.structured_results
        )

    @property
    def structured_skipped(
        self,
    ) -> int:

        return sum(
            result.skipped

            for result
            in self.structured_results
        )


# =============================================================
# FAILURE DISPLAY
# =============================================================


def _print_refresh_failure(
    component_name: str,
    error: Exception,
    completed: list[str],
) -> None:

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
        "Failed component: "
        f"{component_name}"
    )

    print(
        "Error: "
        f"{error}"
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


# =============================================================
# MARKET DATA REFRESH
# =============================================================


def refresh_market_data(
) -> MarketDataRefreshResult:
    """
    Refresh all production market data.

    Scalar providers discover their active series from
    the central market-data catalog.

    Structured datasets use dedicated storage models
    appropriate to their source data.

    This orchestrator knows which data sources participate
    in production refresh, but it does not know individual
    market-data symbols, external IDs, transformations,
    auction fields or database-writing details.
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
    # RESULTS
    # ---------------------------------------------------------

    provider_results: list[
        ProviderRefreshResult
    ] = []

    structured_results: list[
        StructuredRefreshResult
    ] = []

    completed: list[
        str
    ] = []

    # ---------------------------------------------------------
    # SCALAR SERIES PROVIDERS
    # ---------------------------------------------------------

    for (
        provider_name,
        refresher,
    ) in PROVIDERS:

        try:

            result = (
                refresher()
            )

        except Exception as exc:

            _print_refresh_failure(
                component_name=
                    provider_name,

                error=
                    exc,

                completed=
                    completed,
            )

            raise

        provider_results.append(
            result
        )

        completed.append(
            provider_name
        )

    # ---------------------------------------------------------
    # STRUCTURED DATASETS
    # ---------------------------------------------------------

    for (
        dataset_name,
        refresher,
    ) in STRUCTURED_DATASETS:

        try:

            result = (
                refresher()
            )

        except Exception as exc:

            _print_refresh_failure(
                component_name=
                    dataset_name,

                error=
                    exc,

                completed=
                    completed,
            )

            raise

        structured_results.append(
            result
        )

        completed.append(
            dataset_name
        )

    # ---------------------------------------------------------
    # RESULT
    # ---------------------------------------------------------

    refresh_result = (
        MarketDataRefreshResult(

            provider_results=
                tuple(
                    provider_results
                ),

            structured_results=
                tuple(
                    structured_results
                ),
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
        "Scalar providers: "
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
        "Observations inserted: "
        f"{refresh_result.inserted}"
    )

    print(
        "Observations skipped: "
        f"{refresh_result.skipped}"
    )

    print()

    print(
        "Structured datasets: "
        f"{refresh_result.structured_dataset_count}"
    )

    print(
        "Structured records received: "
        f"{refresh_result.structured_received}"
    )

    print(
        "Structured records inserted: "
        f"{refresh_result.structured_inserted}"
    )

    print(
        "Structured records updated: "
        f"{refresh_result.structured_updated}"
    )

    print(
        "Structured records skipped: "
        f"{refresh_result.structured_skipped}"
    )

    return refresh_result


# =============================================================
# DIRECT EXECUTION
# =============================================================


if __name__ == "__main__":
    refresh_market_data()