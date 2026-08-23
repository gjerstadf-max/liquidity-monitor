from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from backend.catalog.series import (
    SeriesDefinition,
    series_for_provider,
)
from backend.collectors.fred import (
    fetch_fred_series,
)
from backend.services.observation_store import (
    StoreResult,
    store_values,
)


# =============================================================
# TRANSFORMS
# =============================================================


def normalize_value(
    value: Decimal,
    transform: str | None,
) -> Decimal:
    """
    Apply a catalog-defined normalization transform.

    The catalog stores the NAME of the transformation.
    Actual arithmetic remains explicit here.
    """

    if transform is None:

        return value


    if transform == "millions_to_billions":

        return (
            value
            / Decimal(
                "1000"
            )
        )


    if transform == "dollars_to_billions":

        return (
            value
            / Decimal(
                "1000000000"
            )
        )


    raise ValueError(
        "Unknown market-data transform: "
        f"{transform}"
    )


# =============================================================
# PROVIDER RESULT
# =============================================================


@dataclass(frozen=True)
class ProviderRefreshResult:
    """
    Summary of one provider refresh.
    """

    provider: str

    series_results: tuple[
        StoreResult,
        ...
    ]

    @property
    def inserted(
        self,
    ) -> int:

        return sum(
            result.inserted

            for result
            in self.series_results
        )


    @property
    def skipped(
        self,
    ) -> int:

        return sum(
            result.skipped

            for result
            in self.series_results
        )


# =============================================================
# FRED — ONE SERIES
# =============================================================


def refresh_fred_series(
    definition: SeriesDefinition,
    observation_count: int = 100,
) -> StoreResult:
    """
    Refresh one FRED series using its catalog definition.

    Adding another ordinary FRED series should therefore
    require only a new SeriesDefinition.
    """

    if (
        definition.provider
        != "fred"
    ):

        raise ValueError(
            "Series is not configured "
            "for the FRED provider: "
            f"{definition.symbol}"
        )


    observations = (
        fetch_fred_series(
            series_id=
                definition.external_id,

            count=
                observation_count,
        )
    )


    if not observations:

        raise RuntimeError(
            "FRED returned no observations "
            f"for {definition.symbol} "
            f"({definition.external_id})."
        )


    values = [

        (
            observation.observation_date,

            normalize_value(
                observation.value,
                definition.transform,
            ),
        )

        for observation
        in observations
    ]


    return store_values(
        indicator_symbol=
            definition.symbol,

        values=
            values,
    )


# =============================================================
# FRED — PROVIDER REFRESH
# =============================================================


def refresh_fred_provider(
    observation_count: int = 100,
) -> ProviderRefreshResult:
    """
    Refresh every active FRED series registered
    in the market-data catalog.
    """

    definitions = (
        series_for_provider(
            "fred"
        )
    )


    if not definitions:

        raise RuntimeError(
            "No active FRED series "
            "are registered."
        )


    print()

    print(
        "FRED Market Data"
    )

    print(
        "=" * 72
    )


    results: list[
        StoreResult
    ] = []


    for definition in definitions:

        print()

        print(
            f"{definition.symbol.upper()}"
        )

        print(
            f"FRED series: "
            f"{definition.external_id}"
        )

        print(
            f"Stored units: "
            f"{definition.units}"
        )


        result = (
            refresh_fred_series(
                definition=
                    definition,

                observation_count=
                    observation_count,
            )
        )


        results.append(
            result
        )


        print(
            f"Received: "
            f"{result.received}"
        )

        print(
            f"Inserted: "
            f"{result.inserted}"
        )

        print(
            f"Skipped:  "
            f"{result.skipped}"
        )


        if (
            result.latest_date
            is not None
        ):

            print(
                "Latest:   "
                f"{result.latest_date}"
            )


        if (
            result.latest_value
            is not None
        ):

            print(
                "Value:    "
                f"{result.latest_value}"
            )


    provider_result = (
        ProviderRefreshResult(
            provider=
                "fred",

            series_results=
                tuple(
                    results
                ),
        )
    )


    print()

    print(
        "-" * 72
    )

    print(
        "FRED provider refresh complete."
    )

    print(
        f"Inserted: "
        f"{provider_result.inserted}"
    )

    print(
        f"Skipped:  "
        f"{provider_result.skipped}"
    )


    return provider_result