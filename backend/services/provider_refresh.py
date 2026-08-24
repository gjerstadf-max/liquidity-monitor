from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from decimal import (
    Decimal,
    InvalidOperation,
)

from backend.collectors.nyfed_primary_dealers import (
    fetch_primary_dealer_timeseries,
)


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
from backend.collectors.nyfed_rrp import (
    fetch_latest_reverse_repo,
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

# =============================================================
# NY FED ON RRP — PROVIDER REFRESH
# =============================================================


def refresh_nyfed_reverse_repo(
    observation_count: int = 400,
) -> ProviderRefreshResult:
    """
    Refresh all active New York Fed reverse-repo series
    registered in the market-data catalog.

    At present the catalog contains one series:

        on_rrp

    Values arrive from the New York Fed in dollars and are
    normalized according to the catalog transform.
    """

    definitions = (
        series_for_provider(
            "nyfed_reverse_repo"
        )
    )


    if not definitions:

        raise RuntimeError(
            "No active NY Fed reverse-repo "
            "series are registered."
        )


    print()

    print(
        "New York Fed ON RRP"
    )

    print(
        "=" * 72
    )


    # ---------------------------------------------------------
    # FETCH ONCE
    # ---------------------------------------------------------

    observations = (
        fetch_latest_reverse_repo(
            observation_count
        )
    )


    if not observations:

        raise RuntimeError(
            "New York Fed returned no "
            "ON RRP observations."
        )


    results: list[
        StoreResult
    ] = []


    # ---------------------------------------------------------
    # PROCESS CATALOG SERIES
    # ---------------------------------------------------------

    for definition in definitions:

        print()

        print(
            definition.symbol.upper()
        )

        print(
            f"Stored units: "
            f"{definition.units}"
        )


        # ON RRP currently maps to total accepted dollars.
        #
        # The conversion to billions comes from the catalog
        # transform rather than being hardcoded in the loader.

        values = [

            (
                observation.operation_date,

                normalize_value(
                    value=
                        observation.total_accepted_dollars,

                    transform=
                        definition.transform,
                ),
            )

            for observation
            in observations
        ]


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
                f"Latest:   "
                f"{result.latest_date}"
            )


        if (
            result.latest_value
            is not None
        ):

            print(
                "Value:    "
                f"${result.latest_value:,.3f}B"
            )


    provider_result = (
        ProviderRefreshResult(
            provider=
                "nyfed_reverse_repo",

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
        "NY Fed ON RRP refresh complete."
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
# NY FED PRIMARY DEALERS — PROVIDER REFRESH
# =============================================================


PRIMARY_DEALER_CANONICAL_START_DATE = date(
    2013,
    4,
    3,
)


def _extract_primary_dealer_values(
    payload: dict,
    definition: SeriesDefinition,
) -> tuple[
    list[
        tuple[
            date,
            Decimal,
        ]
    ],
    int,
]:
    """
    Convert one NY Fed Primary Dealer response into
    normalized Liquidity Monitor date/value observations.

    Primary Dealer source values may contain suppressed
    observations. Suppressed or missing values remain
    missing and are never converted to zero.

    Canonical Treasury-intermediation history begins
    April 3, 2013.

    Unit normalization is controlled by the market-data
    catalog through definition.transform.
    """

    pd_payload = payload.get(
        "pd"
    )

    if not isinstance(
        pd_payload,
        dict,
    ):
        raise RuntimeError(
            "Primary Dealer response did not "
            "contain a pd object."
        )

    records = pd_payload.get(
        "timeseries"
    )

    if not isinstance(
        records,
        list,
    ):
        raise RuntimeError(
            "Primary Dealer response did not "
            "contain a timeseries list."
        )

    values: list[
        tuple[
            date,
            Decimal,
        ]
    ] = []

    suppressed = 0

    for record in records:

        if not isinstance(
            record,
            dict,
        ):
            continue

        raw_date = record.get(
            "asofdate"
        )

        raw_value = record.get(
            "value"
        )

        if raw_date is None:
            continue

        try:
            observation_date = (
                date.fromisoformat(
                    str(
                        raw_date
                    )
                )
            )

        except ValueError:
            continue

        if (
            observation_date
            < PRIMARY_DEALER_CANONICAL_START_DATE
        ):
            continue

        value_text = (
            ""
            if raw_value is None
            else str(
                raw_value
            ).strip()
        )

        # -----------------------------------------------------
        # SUPPRESSED / MISSING
        # -----------------------------------------------------

        if value_text in {
            "",
            "*",
            "NA",
            "N/A",
            "null",
            "None",
        }:
            suppressed += 1
            continue

        # -----------------------------------------------------
        # NUMERIC
        # -----------------------------------------------------

        try:
            source_value = Decimal(
                value_text
            )

        except (
            InvalidOperation,
            ValueError,
        ):
            suppressed += 1
            continue

        normalized_value = (
            normalize_value(
                value=
                    source_value,

                transform=
                    definition.transform,
            )
        )

        values.append(
            (
                observation_date,
                normalized_value,
            )
        )

    return (
        sorted(
            values,
            key=lambda item:
                item[0],
        ),
        suppressed,
    )


def refresh_nyfed_primary_dealer_series(
    definition: SeriesDefinition,
) -> StoreResult:
    """
    Refresh one catalog-defined NY Fed Primary Dealer
    series.
    """

    if (
        definition.provider
        != "nyfed_primary_dealers"
    ):
        raise ValueError(
            "Series is not configured for "
            "NY Fed Primary Dealers: "
            f"{definition.symbol}"
        )

    if not definition.external_id:
        raise ValueError(
            "Primary Dealer series has no "
            "external ID: "
            f"{definition.symbol}"
        )

    payload = (
        fetch_primary_dealer_timeseries(
            key_id=
                definition.external_id,

            series_break=
                None,
        )
    )

    (
        values,
        suppressed,
    ) = (
        _extract_primary_dealer_values(
            payload=
                payload,

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

    print(
        f"Suppressed/missing: "
        f"{suppressed}"
    )

    return result


def refresh_nyfed_primary_dealers(
) -> ProviderRefreshResult:
    """
    Refresh every active NY Fed Primary Dealer series
    registered in the market-data catalog.

    The catalog determines:
        - internal symbol
        - NY Fed external key
        - stored units
        - normalization transform
        - factor role

    Primary-Dealer-specific parsing and reporting-regime
    handling remain explicit in this provider layer.
    """

    definitions = (
        series_for_provider(
            "nyfed_primary_dealers"
        )
    )

    if not definitions:
        raise RuntimeError(
            "No active NY Fed Primary Dealer "
            "series are registered."
        )

    print()

    print(
        "New York Fed Primary Dealers"
    )

    print(
        "=" * 72
    )

    print(
        "Canonical history begins "
        f"{PRIMARY_DEALER_CANONICAL_START_DATE}."
    )

    results: list[
        StoreResult
    ] = []

    for definition in definitions:

        print()

        print(
            definition.symbol.upper()
        )

        print(
            "-" * 72
        )

        print(
            "NY Fed key: "
            f"{definition.external_id}"
        )

        print(
            "Stored units: "
            f"{definition.units}"
        )

        print(
            "Factor role: "
            f"{definition.role}"
        )

        result = (
            refresh_nyfed_primary_dealer_series(
                definition=
                    definition,
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
                "nyfed_primary_dealers",

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
        "NY Fed Primary Dealer "
        "provider refresh complete."
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