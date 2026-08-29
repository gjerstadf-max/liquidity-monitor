from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


# =============================================================
# TYPES
# =============================================================


Provider = Literal[
    "nyfed_reference_rates",
    "nyfed_reverse_repo",
    "fred",
    "nyfed_primary_dealers",
]


SeriesRole = Literal[
    "core",
    "supporting",
    "research",
]


# =============================================================
# SERIES DEFINITION
# =============================================================


@dataclass(frozen=True)
class SeriesDefinition:
    """
    Canonical definition of one stored market-data series.

    The catalog describes data.

    It does NOT:
        - fetch data
        - write observations
        - calculate metrics
        - generate signals
        - determine assessments

    Those responsibilities remain elsewhere.
    """

    symbol: str
    name: str

    category: str
    frequency: str
    units: str

    provider: Provider

    # Provider-specific external identifier.
    #
    # Examples:
    #   SOFR
    #   WRESBAL
    #   PDPOSGST-TOT
    #
    external_id: str

    # For a series extracted from a richer parent observation,
    # such as SOFR volume or SOFR percentile data.
    parent_symbol: str | None = None
    source_field: str | None = None

    # Units received from the provider before normalization.
    source_units: str | None = None

    # Descriptive transform name only.
    #
    # Actual transformation logic remains in the loader.
    transform: str | None = None

    role: SeriesRole = "core"

    active: bool = True


# =============================================================
# FUNDING REFERENCE RATES
# =============================================================


FUNDING_SERIES = (

    SeriesDefinition(
        symbol="sofr",
        name="Secured Overnight Financing Rate",
        category="Funding",
        frequency="Daily",
        units="Percent",
        provider="nyfed_reference_rates",
        external_id="sofr",
        source_units="Percent",
        role="core",
    ),

    SeriesDefinition(
        symbol="effr",
        name="Effective Federal Funds Rate",
        category="Funding",
        frequency="Daily",
        units="Percent",
        provider="nyfed_reference_rates",
        external_id="effr",
        source_units="Percent",
        role="core",
    ),

    SeriesDefinition(
        symbol="obfr",
        name="Overnight Bank Funding Rate",
        category="Funding",
        frequency="Daily",
        units="Percent",
        provider="nyfed_reference_rates",
        external_id="obfr",
        source_units="Percent",
        role="core",
    ),

    SeriesDefinition(
        symbol="tgcr",
        name="Tri-Party General Collateral Rate",
        category="Repo Market",
        frequency="Daily",
        units="Percent",
        provider="nyfed_reference_rates",
        external_id="tgcr",
        source_units="Percent",
        role="core",
    ),

    SeriesDefinition(
        symbol="bgcr",
        name="Broad General Collateral Rate",
        category="Repo Market",
        frequency="Daily",
        units="Percent",
        provider="nyfed_reference_rates",
        external_id="bgcr",
        source_units="Percent",
        role="core",
    ),
)


# =============================================================
# REFERENCE-RATE INTERNALS
# =============================================================


def _reference_rate_internals(
    symbol: str,
    display_name: str,
) -> tuple[SeriesDefinition, ...]:

    return (

        SeriesDefinition(
            symbol=f"{symbol}_volume",
            name=f"{display_name} Transaction Volume",
            category="Repo Market",
            frequency="Daily",
            units="USD Billions",
            provider="nyfed_reference_rates",
            external_id=symbol,
            parent_symbol=symbol,
            source_field="volume_billions",
            source_units="USD Billions",
            role="supporting",
        ),

        SeriesDefinition(
            symbol=f"{symbol}_p1",
            name=f"{display_name} 1st Percentile",
            category="Repo Market",
            frequency="Daily",
            units="Percent",
            provider="nyfed_reference_rates",
            external_id=symbol,
            parent_symbol=symbol,
            source_field="percentile_1",
            source_units="Percent",
            role="supporting",
        ),

        SeriesDefinition(
            symbol=f"{symbol}_p25",
            name=f"{display_name} 25th Percentile",
            category="Repo Market",
            frequency="Daily",
            units="Percent",
            provider="nyfed_reference_rates",
            external_id=symbol,
            parent_symbol=symbol,
            source_field="percentile_25",
            source_units="Percent",
            role="supporting",
        ),

        SeriesDefinition(
            symbol=f"{symbol}_p75",
            name=f"{display_name} 75th Percentile",
            category="Repo Market",
            frequency="Daily",
            units="Percent",
            provider="nyfed_reference_rates",
            external_id=symbol,
            parent_symbol=symbol,
            source_field="percentile_75",
            source_units="Percent",
            role="supporting",
        ),

        SeriesDefinition(
            symbol=f"{symbol}_p99",
            name=f"{display_name} 99th Percentile",
            category="Repo Market",
            frequency="Daily",
            units="Percent",
            provider="nyfed_reference_rates",
            external_id=symbol,
            parent_symbol=symbol,
            source_field="percentile_99",
            source_units="Percent",
            role="supporting",
        ),
    )


REPO_INTERNAL_SERIES = (

    *_reference_rate_internals(
        symbol="sofr",
        display_name="SOFR",
    ),

    *_reference_rate_internals(
        symbol="tgcr",
        display_name="TGCR",
    ),

    *_reference_rate_internals(
        symbol="bgcr",
        display_name="BGCR",
    ),
)


# =============================================================
# SYSTEM LIQUIDITY
# =============================================================


SYSTEM_LIQUIDITY_SERIES = (

    SeriesDefinition(
        symbol="reserve_balances",
        name=(
            "Reserve Balances with "
            "Federal Reserve Banks"
        ),
        category="Funding",
        frequency="Weekly",
        units="USD Billions",
        provider="fred",
        external_id="WRESBAL",
        source_units="USD Millions",
        transform="millions_to_billions",
        role="core",
    ),

    SeriesDefinition(
        symbol="tga",
        name="U.S. Treasury General Account",
        category="Funding",
        frequency="Weekly",
        units="USD Billions",
        provider="fred",
        external_id="WDTGAL",
        source_units="USD Millions",
        transform="millions_to_billions",
        role="core",
    ),

    SeriesDefinition(
        symbol="on_rrp",
        name=(
            "Overnight Reverse "
            "Repo Agreements"
        ),
        category="Funding",
        frequency="Daily",
        units="USD Billions",
        provider="nyfed_reverse_repo",
        external_id="overnight_fixed_rate_reverse_repo",
        source_units="USD",
        transform="dollars_to_billions",
        role="core",
    ),

)


# =============================================================
# TREASURY INTERMEDIATION
# =============================================================


TREASURY_INTERMEDIATION_SERIES = (

    SeriesDefinition(
        symbol="pd_treasury_positions",
        name="Primary Dealer Treasury Positions",
        category="Treasury Intermediation",
        frequency="Weekly",
        units="USD Billions",
        provider="nyfed_primary_dealers",
        external_id="PDPOSGST-TOT",
        source_units="USD Millions",
        transform="millions_to_billions",
        role="core",
    ),

    SeriesDefinition(
        symbol="pd_treasury_transactions",
        name="Primary Dealer Treasury Transactions",
        category="Treasury Intermediation",
        frequency="Weekly",
        units="USD Billions",
        provider="nyfed_primary_dealers",
        external_id="PDGSWOEXTTOT",
        source_units="USD Millions",
        transform="millions_to_billions",
        role="core",
    ),

    SeriesDefinition(
        symbol="pd_treasury_repo",
        name="Primary Dealer Treasury Repo Financing",
        category="Treasury Intermediation",
        frequency="Weekly",
        units="USD Billions",
        provider="nyfed_primary_dealers",
        external_id="PDSORA-UTSETTOT",
        source_units="USD Millions",
        transform="millions_to_billions",
        role="supporting",
    ),

    SeriesDefinition(
        symbol="pd_treasury_reverse_repo",
        name=(
            "Primary Dealer Treasury "
            "Reverse Repo Financing"
        ),
        category="Treasury Intermediation",
        frequency="Weekly",
        units="USD Billions",
        provider="nyfed_primary_dealers",
        external_id="PDSIRRA-UTSETTOT",
        source_units="USD Millions",
        transform="millions_to_billions",
        role="supporting",
    ),

    SeriesDefinition(
        symbol="pd_treasury_borrowed",
        name=(
            "Primary Dealer Treasury "
            "Securities Borrowed"
        ),
        category="Treasury Intermediation",
        frequency="Weekly",
        units="USD Billions",
        provider="nyfed_primary_dealers",
        external_id="PDSIOSB-UTSETTOT",
        source_units="USD Millions",
        transform="millions_to_billions",
        role="core",
    ),

    SeriesDefinition(
        symbol="pd_treasury_lent",
        name=(
            "Primary Dealer Treasury "
            "Securities Lent"
        ),
        category="Treasury Intermediation",
        frequency="Weekly",
        units="USD Billions",
        provider="nyfed_primary_dealers",
        external_id="PDSOOS-UTSETTOT",
        source_units="USD Millions",
        transform="millions_to_billions",
        role="research",
    ),

    SeriesDefinition(
        symbol="pd_treasury_fails_receive",
        name=(
            "Primary Dealer Treasury "
            "Fails to Receive"
        ),
        category="Treasury Intermediation",
        frequency="Weekly",
        units="USD Billions",
        provider="nyfed_primary_dealers",
        external_id="PDFTR-USTET",
        source_units="USD Millions",
        transform="millions_to_billions",
        role="core",
    ),

    SeriesDefinition(
        symbol="pd_treasury_fails_deliver",
        name=(
            "Primary Dealer Treasury "
            "Fails to Deliver"
        ),
        category="Treasury Intermediation",
        frequency="Weekly",
        units="USD Billions",
        provider="nyfed_primary_dealers",
        external_id="PDFTD-USTET",
        source_units="USD Millions",
        transform="millions_to_billions",
        role="core",
    ),
)

# =============================================================
# TREASURY MARKET ACTIVITY
# =============================================================


TREASURY_MARKET_ACTIVITY_SERIES = (

    SeriesDefinition(
        symbol="iorb",
        name=(
            "Interest Rate on Reserve "
            "Balances"
        ),
        category="Treasury Market Activity",
        frequency="Daily",
        units="Percent",
        provider="fred",
        external_id="IORB",
        source_units="Percent",
        role="core",
    ),

    SeriesDefinition(
        symbol="treasury_3m",
        name=(
            "3-Month Treasury "
            "Constant Maturity Rate"
        ),
        category="Treasury Market Activity",
        frequency="Daily",
        units="Percent",
        provider="fred",
        external_id="DGS3MO",
        source_units="Percent",
        role="core",
    ),

    SeriesDefinition(
        symbol="fed_repo_operations",
        name="Federal Reserve Repo Operations Accepted",
        category="repo_market",
        frequency="Daily",
        units="Billions of U.S. Dollars",
        provider="fred",
        external_id="RPTTLD",
        source_units="Billions of U.S. Dollars",
        role="supporting",
    ),

)


COMMERCIAL_PAPER_SERIES = (

    SeriesDefinition(
        symbol="cp_aa_nonfinancial_30d",
        name="30-Day AA Nonfinancial Commercial Paper Rate",
        category="commercial_paper",
        frequency="Daily",
        units="Percent",
        provider="fred",
        external_id="RIFSPPNAAD30NB",
        source_units="Percent",
        role="core",
    ),

    SeriesDefinition(
        symbol="cp_a2p2_nonfinancial_30d",
        name="30-Day A2/P2 Nonfinancial Commercial Paper Rate",
        category="commercial_paper",
        frequency="Daily",
        units="Percent",
        provider="fred",
        external_id="RIFSPPNA2P2D30NB",
        source_units="Percent",
        role="core",
    ),

    SeriesDefinition(
        symbol="cp_aa_financial_30d",
        name="30-Day AA Financial Commercial Paper Rate",
        category="commercial_paper",
        frequency="Daily",
        units="Percent",
        provider="fred",
        external_id="RIFSPPFAAD30NB",
        source_units="Percent",
        role="supporting",
    ),

    SeriesDefinition(
        symbol="cp_financial_outstanding",
        name="Financial Commercial Paper Outstanding",
        category="commercial_paper",
        frequency="Weekly",
        units="Billions of Dollars",
        provider="fred",
        external_id="FINCP",
        source_units="Billions of Dollars",
        role="supporting",
    ),

    SeriesDefinition(
        symbol="cp_nonfinancial_outstanding",
        name="Nonfinancial Commercial Paper Outstanding",
        category="commercial_paper",
        frequency="Weekly",
        units="Billions of Dollars",
        provider="fred",
        external_id="NFINCP",
        source_units="Billions of Dollars",
        role="supporting",
    ),

)

BANK_FUNDING_SERIES = (

    SeriesDefinition(
        symbol="fed_primary_credit",
        name="Federal Reserve Primary Credit",
        category="bank_funding",
        frequency="Weekly",
        units="Billions of U.S. Dollars",
        provider="fred",
        external_id="WLCFLPCL",
        source_units="Millions of U.S. Dollars",
        transform="millions_to_billions",
        role="core",
    ),

    SeriesDefinition(
        symbol="bank_deposits_small",
        name="Deposits at Small Domestically Chartered Commercial Banks",
        category="bank_funding",
        frequency="Weekly",
        units="Billions of U.S. Dollars",
        provider="fred",
        external_id="DPSSCBW027SBOG",
        source_units="Billions of U.S. Dollars",
        role="core",
    ),

    SeriesDefinition(
        symbol="bank_deposits_large",
        name="Deposits at Large Domestically Chartered Commercial Banks",
        category="bank_funding",
        frequency="Weekly",
        units="Billions of U.S. Dollars",
        provider="fred",
        external_id="DPSLCBW027SBOG",
        source_units="Billions of U.S. Dollars",
        role="supporting",
    ),

    SeriesDefinition(
        symbol="bank_large_time_deposits_small",
        name="Large Time Deposits at Small Domestically Chartered Commercial Banks",
        category="bank_funding",
        frequency="Weekly",
        units="Billions of U.S. Dollars",
        provider="fred",
        external_id="LTDSCBW027SBOG",
        source_units="Billions of U.S. Dollars",
        role="supporting",
    ),

)
GLOBAL_DOLLAR_FUNDING_SERIES = (

    SeriesDefinition(
        symbol="central_bank_liquidity_swaps",
        name="Federal Reserve Central Bank Liquidity Swaps",
        category="global_dollar_funding",
        frequency="Weekly",
        units="Billions of U.S. Dollars",
        provider="fred",
        external_id="SWPT",
        source_units="Millions of U.S. Dollars",
        transform="millions_to_billions",
        role="core",
    ),

    SeriesDefinition(
        symbol="fima_repo",
        name="FIMA Repo Facility",
        category="global_dollar_funding",
        frequency="Weekly",
        units="Billions of U.S. Dollars",
        provider="fred",
        external_id="H41RESPPALGTRFNWW",
        source_units="Millions of U.S. Dollars",
        transform="millions_to_billions",
        role="supporting",
    ),

)

# =============================================================
# COMPLETE CATALOG
# =============================================================


SERIES_CATALOG: tuple[
    SeriesDefinition,
    ...
] = (

    *FUNDING_SERIES,

    *REPO_INTERNAL_SERIES,

    *SYSTEM_LIQUIDITY_SERIES,

    *TREASURY_INTERMEDIATION_SERIES,

    *TREASURY_MARKET_ACTIVITY_SERIES,

    *COMMERCIAL_PAPER_SERIES,

    *BANK_FUNDING_SERIES,

    *GLOBAL_DOLLAR_FUNDING_SERIES,
)


SERIES_BY_SYMBOL: dict[
    str,
    SeriesDefinition,
] = {
    series.symbol:
        series

    for series in SERIES_CATALOG
}


# =============================================================
# LOOKUP HELPERS
# =============================================================


def get_series(
    symbol: str,
) -> SeriesDefinition:
    """
    Retrieve one series definition by internal symbol.
    """

    normalized_symbol = (
        symbol
        .strip()
        .lower()
    )

    try:

        return SERIES_BY_SYMBOL[
            normalized_symbol
        ]

    except KeyError as exc:

        raise KeyError(
            "Unknown market-data series: "
            f"{symbol}"
        ) from exc


def series_for_provider(
    provider: Provider,
) -> tuple[
    SeriesDefinition,
    ...
]:
    """
    Return active series belonging to one provider.
    """

    return tuple(
        series

        for series in SERIES_CATALOG

        if (
            series.provider == provider
            and series.active
        )
    )


def series_for_category(
    category: str,
) -> tuple[
    SeriesDefinition,
    ...
]:
    """
    Return active series belonging to one category.
    """

    normalized_category = (
        category
        .strip()
        .lower()
    )

    return tuple(
        series

        for series in SERIES_CATALOG

        if (
            series.category.lower()
            == normalized_category

            and series.active
        )
    )


# =============================================================
# VALIDATION
# =============================================================


def validate_series_catalog() -> None:
    """
    Validate structural integrity of the catalog.

    Raises ValueError if the registry contains an
    internally inconsistent definition.
    """

    if not SERIES_CATALOG:

        raise ValueError(
            "Series catalog is empty."
        )


    # ---------------------------------------------------------
    # UNIQUE SYMBOLS
    # ---------------------------------------------------------

    symbols = [
        series.symbol
        for series in SERIES_CATALOG
    ]

    duplicates = sorted(
        {
            symbol

            for symbol in symbols

            if symbols.count(symbol) > 1
        }
    )

    if duplicates:

        raise ValueError(
            "Duplicate series symbols: "
            + ", ".join(duplicates)
        )


    # ---------------------------------------------------------
    # REQUIRED FIELDS
    # ---------------------------------------------------------

    for series in SERIES_CATALOG:

        if not series.symbol.strip():

            raise ValueError(
                "Series contains an empty symbol."
            )

        if (
            series.symbol
            != series.symbol.lower()
        ):

            raise ValueError(
                "Series symbols must be lowercase: "
                f"{series.symbol}"
            )

        if not series.name.strip():

            raise ValueError(
                "Series contains an empty name: "
                f"{series.symbol}"
            )

        if not series.external_id.strip():

            raise ValueError(
                "Series contains an empty "
                "external_id: "
                f"{series.symbol}"
            )


    # ---------------------------------------------------------
    # PARENT REFERENCES
    # ---------------------------------------------------------

    for series in SERIES_CATALOG:

        if series.parent_symbol is None:
            continue

        if (
            series.parent_symbol
            not in SERIES_BY_SYMBOL
        ):

            raise ValueError(
                "Unknown parent series "
                f"{series.parent_symbol!r} "
                f"for {series.symbol!r}."
            )

        parent = SERIES_BY_SYMBOL[
            series.parent_symbol
        ]

        if (
            parent.provider
            != series.provider
        ):

            raise ValueError(
                "Parent/provider mismatch for "
                f"{series.symbol}."
            )

        if (
            parent.external_id
            != series.external_id
        ):

            raise ValueError(
                "Parent/external_id mismatch for "
                f"{series.symbol}."
            )


    # ---------------------------------------------------------
    # DERIVED SOURCE FIELDS
    # ---------------------------------------------------------

    for series in SERIES_CATALOG:

        if (
            series.parent_symbol is not None
            and series.source_field is None
        ):

            raise ValueError(
                "Child series requires source_field: "
                f"{series.symbol}"
            )


# Validate immediately when imported.
validate_series_catalog()