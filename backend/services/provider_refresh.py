from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from backend.catalog.series import (
    SeriesDefinition,
    series_for_provider,
)
from backend.collectors.fred import (
    fetch_fred_series,
)
from backend.collectors.nyfed import (
    ReferenceRateObservation,
    fetch_latest_reference_rate,
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
    def received(
        self,
    ) -> int:

        return sum(
            result.received

            for result
            in self.series_results
        )


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
# RESULT DISPLAY
# =============================================================


def _print_store_result(
    result: StoreResult,
) -> None:
    """
    Print one normalized series refresh result.
    """

    print(
        f"{result.symbol.upper():<28} "
        f"received {result.received:<4} "
        f"inserted {result.inserted:<4} "
        f"skipped {result.skipped:<4}"
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


        _print_store_result(
            result
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


# =============================================================
# NY FED REFERENCE RATES — FIELD EXTRACTION
# =============================================================


def _extract_reference_rate_values(
    observations: list[
        ReferenceRateObservation
    ],
    definition: SeriesDefinition,
) -> list[
    tuple[
        date,
        Decimal,
    ]
]:
    """
    Extract the catalog-selected field from a group
    of New York Fed reference-rate observations.

    Core rate series use the observation's `rate` field.

    Child series such as SOFR volume or SOFR p99 use
    `source_field` from the market-data catalog.
    """

    field_name = (
        definition.source_field
        or "rate"
    )


    values: list[
        tuple[
            date,
            Decimal,
        ]
    ] = []


    for observation in observations:

        value = getattr(
            observation,
            field_name,
        )


        # The NY Fed can omit volume or percentile values.
        # Missing published values remain missing.
        #
        # They must never be converted to zero.

        if value is None:

            continue


        normalized_value = (
            normalize_value(
                value=
                    value,

                transform=
                    definition.transform,
            )
        )


        values.append(
            (
                observation.observation_date,
                normalized_value,
            )
        )


    return values


# =============================================================
# NY FED REFERENCE RATES — GROUP DEFINITIONS
# =============================================================


def _reference_rate_groups(
) -> dict[
    str,
    tuple[
        SeriesDefinition,
        ...
    ],
]:
    """
    Group catalog series by underlying NY Fed
    reference-rate identifier.

    This is important because SOFR, for example, produces
    several stored series from one NY Fed response:

        sofr
        sofr_volume
        sofr_p1
        sofr_p25
        sofr_p75
        sofr_p99

    The API should be called once for SOFR, not six times.
    """

    definitions = (
        series_for_provider(
            "nyfed_reference_rates"
        )
    )


    groups: dict[
        str,
        list[
            SeriesDefinition
        ],
    ] = {}


    for definition in definitions:

        external_id = (
            definition.external_id
            .strip()
            .lower()
        )


        groups.setdefault(
            external_id,
            [],
        ).append(
            definition
        )


    return {
        external_id:
            tuple(
                group
            )

        for (
            external_id,
            group,
        ) in groups.items()
    }


# =============================================================
# NY FED REFERENCE RATES — ONE FAMILY
# =============================================================


def refresh_nyfed_reference_rate_family(
    external_id: str,
    definitions: tuple[
        SeriesDefinition,
        ...
    ],
    observation_count: int = 100,
) -> tuple[
    StoreResult,
    ...
]:
    """
    Fetch one NY Fed reference-rate family once and store
    every catalog-defined series derived from that response.

    Examples:

        SOFR ->
            rate
            volume
            percentiles

        EFFR ->
            rate only
    """

    if not definitions:

        raise ValueError(
            "Reference-rate family "
            "contains no definitions."
        )


    for definition in definitions:

        if (
            definition.provider
            != "nyfed_reference_rates"
        ):

            raise ValueError(
                "Series is not configured for "
                "NY Fed reference rates: "
                f"{definition.symbol}"
            )


        if (
            definition.external_id
            .strip()
            .lower()
            != external_id
            .strip()
            .lower()
        ):

            raise ValueError(
                "Reference-rate family contains "
                "multiple external IDs."
            )


    normalized_id = (
        external_id
        .strip()
        .lower()
    )


    observations = (
        fetch_latest_reference_rate(
            indicator_id=
                normalized_id,

            observation_count=
                observation_count,
        )
    )


    if not observations:

        raise RuntimeError(
            "NY Fed returned no observations "
            f"for {normalized_id.upper()}."
        )


    results: list[
        StoreResult
    ] = []


    for definition in definitions:

        values = (
            _extract_reference_rate_values(
                observations=
                    observations,

                definition=
                    definition,
            )
        )


        result = (
            store_values(
                indicator_symbol=
                    definition.symbol,

                values=
                    values,
            )
        )


        results.append(
            result
        )


    return tuple(
        results
    )


# =============================================================
# NY FED REFERENCE RATES — PROVIDER REFRESH
# =============================================================


def refresh_nyfed_reference_rates(
    observation_count: int = 100,
) -> ProviderRefreshResult:
    """
    Refresh every active NY Fed reference-rate series
    registered in the market-data catalog.

    The catalog determines:
        - which rate families exist
        - which internal series are stored
        - which response field each child series uses

    One NY Fed API request is made per underlying
    reference-rate family.
    """

    groups = (
        _reference_rate_groups()
    )


    if not groups:

        raise RuntimeError(
            "No active NY Fed reference-rate "
            "series are registered."
        )


    print()

    print(
        "New York Fed Reference Rates"
    )

    print(
        "=" * 72
    )


    results: list[
        StoreResult
    ] = []


    for external_id in sorted(
        groups
    ):

        definitions = (
            groups[
                external_id
            ]
        )


        print()

        print(
            external_id.upper()
        )

        print(
            "-" * 72
        )

        print(
            "Catalog series: "
            + ", ".join(
                definition.symbol

                for definition
                in definitions
            )
        )


        family_results = (
            refresh_nyfed_reference_rate_family(
                external_id=
                    external_id,

                definitions=
                    definitions,

                observation_count=
                    observation_count,
            )
        )


        results.extend(
            family_results
        )


        for result in family_results:

            _print_store_result(
                result
            )


    provider_result = (
        ProviderRefreshResult(
            provider=
                "nyfed_reference_rates",

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
        "NY Fed reference-rate refresh complete."
    )

    print(
        "Underlying rate families: "
        f"{len(groups)}"
    )

    print(
        "Stored catalog series: "
        f"{len(results)}"
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