from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any

import httpx


NY_FED_API_BASE_URL = "https://markets.newyorkfed.org/api"


# =============================================================
# EXCEPTIONS
# =============================================================


class NewYorkFedError(Exception):
    """Base exception for New York Fed collector errors."""


class NewYorkFedRequestError(NewYorkFedError):
    """Raised when a New York Fed API request fails."""


class NewYorkFedDataError(NewYorkFedError):
    """Raised when New York Fed data is missing or invalid."""


# =============================================================
# DATA OBJECT
# =============================================================


@dataclass(frozen=True)
class ReferenceRateObservation:
    """
    One reference-rate observation from the
    Federal Reserve Bank of New York.
    """

    indicator_id: str

    observation_date: date

    rate: Decimal

    volume_billions: Decimal | None

    percentile_1: Decimal | None
    percentile_25: Decimal | None
    percentile_75: Decimal | None
    percentile_99: Decimal | None

    source: str = "Federal Reserve Bank of New York"


# =============================================================
# HELPERS
# =============================================================


def _optional_decimal(
    value: Any,
) -> Decimal | None:
    """
    Convert an optional API field to Decimal.
    """

    if value in (
        None,
        "",
        "N/A",
    ):
        return None

    try:

        return Decimal(
            str(value)
        )

    except (
        InvalidOperation,
        TypeError,
        ValueError,
    ) as exc:

        raise NewYorkFedDataError(
            "Could not convert value "
            f"to Decimal: {value!r}"
        ) from exc


def _parse_reference_rate_record(
    record: dict[str, Any],
    indicator_id: str,
) -> ReferenceRateObservation:
    """
    Convert one New York Fed API record
    into our normalized observation object.
    """

    try:

        observation_date = (
            date.fromisoformat(
                record[
                    "effectiveDate"
                ]
            )
        )


        rate = Decimal(
            str(
                record[
                    "percentRate"
                ]
            )
        )


    except KeyError as exc:

        raise NewYorkFedDataError(
            f"Required "
            f"{indicator_id.upper()} "
            f"field is missing: "
            f"{exc.args[0]}"
        ) from exc


    except (
        ValueError,
        InvalidOperation,
        TypeError,
    ) as exc:

        raise NewYorkFedDataError(
            f"Invalid "
            f"{indicator_id.upper()} "
            f"record: {record!r}"
        ) from exc


    # ---------------------------------------------------------
    # BASIC VALIDATION
    # ---------------------------------------------------------

    if (
        rate < Decimal("0")
        or rate > Decimal("25")
    ):

        raise NewYorkFedDataError(
            f"{indicator_id.upper()} "
            "value is outside "
            f"the validation range: "
            f"{rate}"
        )


    return ReferenceRateObservation(

        indicator_id=
            indicator_id,

        observation_date=
            observation_date,

        rate=
            rate,

        volume_billions=
            _optional_decimal(
                record.get(
                    "volumeInBillions"
                )
            ),

        percentile_1=
            _optional_decimal(
                record.get(
                    "percentPercentile1"
                )
            ),

        percentile_25=
            _optional_decimal(
                record.get(
                    "percentPercentile25"
                )
            ),

        percentile_75=
            _optional_decimal(
                record.get(
                    "percentPercentile75"
                )
            ),

        percentile_99=
            _optional_decimal(
                record.get(
                    "percentPercentile99"
                )
            ),
    )


# =============================================================
# GENERIC REFERENCE-RATE COLLECTOR
# =============================================================


def fetch_latest_reference_rate(
    indicator_id: str,
    observation_count: int = 5,
    timeout_seconds: float = 15.0,
) -> list[ReferenceRateObservation]:
    """
    Retrieve recent New York Fed reference-rate observations.

    Supported rates:

        Secured:
            SOFR
            TGCR
            BGCR

        Unsecured:
            EFFR
            OBFR
    """

    normalized_id = (
        indicator_id
        .lower()
        .strip()
    )


    rate_configuration = {

        # Secured Treasury repo
        "sofr": "secured",
        "tgcr": "secured",
        "bgcr": "secured",

        # Unsecured bank funding
        "effr": "unsecured",
        "obfr": "unsecured",
    }


    if (
        normalized_id
        not in rate_configuration
    ):

        supported = ", ".join(
            sorted(
                rate_configuration
            )
        )

        raise ValueError(
            "Unsupported reference rate: "
            f"{indicator_id}. "
            f"Supported rates: {supported}"
        )


    if (
        observation_count < 1
        or observation_count > 100
    ):

        raise ValueError(
            "observation_count must "
            "be between 1 and 100"
        )


    market_type = (
        rate_configuration[
            normalized_id
        ]
    )


    url = (
        f"{NY_FED_API_BASE_URL}"
        f"/rates/"
        f"{market_type}/"
        f"{normalized_id}/"
        f"last/{observation_count}.json"
    )


    # ---------------------------------------------------------
    # REQUEST
    # ---------------------------------------------------------

    try:

        with httpx.Client(
            timeout=
                timeout_seconds,

            follow_redirects=True,
        ) as client:

            response = (
                client.get(
                    url,

                    headers={
                        "Accept":
                            "application/json",

                        "User-Agent":
                            "LiquidityMonitor/0.1",
                    },
                )
            )


            response.raise_for_status()


    except httpx.HTTPError as exc:

        raise NewYorkFedRequestError(
            "New York Fed "
            f"{normalized_id.upper()} "
            f"request failed: {exc}"
        ) from exc


    # ---------------------------------------------------------
    # JSON
    # ---------------------------------------------------------

    try:

        payload = (
            response.json()
        )


    except ValueError as exc:

        raise NewYorkFedDataError(
            "New York Fed response "
            "was not valid JSON"
        ) from exc


    records = (
        payload.get(
            "refRates"
        )
    )


    if not isinstance(
        records,
        list,
    ):

        raise NewYorkFedDataError(
            "New York Fed response "
            "did not contain a "
            "refRates list"
        )


    if not records:

        raise NewYorkFedDataError(
            "New York Fed returned "
            f"no {normalized_id.upper()} "
            "observations"
        )


    # ---------------------------------------------------------
    # PARSE
    # ---------------------------------------------------------

    observations = [

        _parse_reference_rate_record(
            record=record,

            indicator_id=
                normalized_id,
        )

        for record in records
    ]


    return sorted(
        observations,

        key=lambda observation:
            observation.observation_date,

        reverse=True,
    )


def fetch_reference_rate_history(
    indicator_id: str,
    start_date: date,
    end_date: date,
    timeout_seconds: float = 30.0,
) -> list[ReferenceRateObservation]:
    """
    Retrieve historical New York Fed reference-rate data
    for a specified date range.

    Supported:
        SOFR
        TGCR
        BGCR
        EFFR
        OBFR
    """

    normalized_id = (
        indicator_id
        .lower()
        .strip()
    )


    rate_configuration = {
        "sofr": "secured",
        "tgcr": "secured",
        "bgcr": "secured",
        "effr": "unsecured",
        "obfr": "unsecured",
    }


    if normalized_id not in rate_configuration:

        supported = ", ".join(
            sorted(
                rate_configuration
            )
        )

        raise ValueError(
            "Unsupported reference rate: "
            f"{indicator_id}. "
            f"Supported rates: {supported}"
        )


    if end_date < start_date:

        raise ValueError(
            "end_date must be on or after "
            "start_date"
        )


    market_type = (
        rate_configuration[
            normalized_id
        ]
    )


    url = (
        f"{NY_FED_API_BASE_URL}"
        f"/rates/"
        f"{market_type}/"
        f"{normalized_id}/"
        f"search.json"
    )


    try:

        with httpx.Client(
            timeout=
                timeout_seconds,

            follow_redirects=True,
        ) as client:

            response = client.get(
                url,

                params={
                    "startDate":
                        start_date.isoformat(),

                    "endDate":
                        end_date.isoformat(),

                    "type":
                        "rate",
                },

                headers={
                    "Accept":
                        "application/json",

                    "User-Agent":
                        "LiquidityMonitor/0.1",
                },
            )


            response.raise_for_status()


    except httpx.HTTPError as exc:

        raise NewYorkFedRequestError(
            "Historical New York Fed "
            f"{normalized_id.upper()} "
            f"request failed: {exc}"
        ) from exc


    try:

        payload = (
            response.json()
        )


    except ValueError as exc:

        raise NewYorkFedDataError(
            "Historical New York Fed "
            "response was not valid JSON"
        ) from exc


    records = (
        payload.get(
            "refRates"
        )
    )


    if not isinstance(
        records,
        list,
    ):

        raise NewYorkFedDataError(
            "Historical New York Fed "
            "response did not contain "
            "a refRates list"
        )


    observations = [

        _parse_reference_rate_record(
            record=record,

            indicator_id=
                normalized_id,
        )

        for record in records
    ]


    return sorted(
        observations,

        key=lambda observation:
            observation.observation_date,

        reverse=True,
    )

# =============================================================
# CONVENIENCE WRAPPERS
# =============================================================


def fetch_latest_sofr(
    observation_count: int = 5,
    timeout_seconds: float = 15.0,
) -> list[ReferenceRateObservation]:

    return fetch_latest_reference_rate(
        indicator_id="sofr",

        observation_count=
            observation_count,

        timeout_seconds=
            timeout_seconds,
    )


def fetch_latest_tgcr(
    observation_count: int = 5,
    timeout_seconds: float = 15.0,
) -> list[ReferenceRateObservation]:

    return fetch_latest_reference_rate(
        indicator_id="tgcr",

        observation_count=
            observation_count,

        timeout_seconds=
            timeout_seconds,
    )


def fetch_latest_bgcr(
    observation_count: int = 5,
    timeout_seconds: float = 15.0,
) -> list[ReferenceRateObservation]:

    return fetch_latest_reference_rate(
        indicator_id="bgcr",

        observation_count=
            observation_count,

        timeout_seconds=
            timeout_seconds,
    )


def fetch_latest_effr(
    observation_count: int = 5,
    timeout_seconds: float = 15.0,
) -> list[ReferenceRateObservation]:

    return fetch_latest_reference_rate(
        indicator_id="effr",

        observation_count=
            observation_count,

        timeout_seconds=
            timeout_seconds,
    )


def fetch_latest_obfr(
    observation_count: int = 5,
    timeout_seconds: float = 15.0,
) -> list[ReferenceRateObservation]:

    return fetch_latest_reference_rate(
        indicator_id="obfr",

        observation_count=
            observation_count,

        timeout_seconds=
            timeout_seconds,
    )


# =============================================================
# LOCAL TEST OUTPUT
# =============================================================


def _display(
    value: Decimal | None,
) -> str:

    if value is None:
        return "-"

    return str(
        value
    )


def _print_observations(
    indicator_name: str,

    observations: list[
        ReferenceRateObservation
    ],
) -> None:

    print()
    print(
        indicator_name
    )
    print("=" * 72)


    for observation in observations:

        print()

        print(
            f"{observation.observation_date}"
        )

        print(
            f"Rate:      "
            f"{observation.rate}%"
        )

        print(
            f"Volume:    "
            f"${_display(observation.volume_billions)}B"
        )

        print(
            f"1st pct:   "
            f"{_display(observation.percentile_1)}%"
        )

        print(
            f"25th pct:  "
            f"{_display(observation.percentile_25)}%"
        )

        print(
            f"75th pct:  "
            f"{_display(observation.percentile_75)}%"
        )

        print(
            f"99th pct:  "
            f"{_display(observation.percentile_99)}%"
        )


# =============================================================
# COMMAND-LINE TEST
# =============================================================


if __name__ == "__main__":

    try:

        _print_observations(
            indicator_name="SOFR",

            observations=
                fetch_latest_sofr(
                    3
                ),
        )


        _print_observations(
            indicator_name="TGCR",

            observations=
                fetch_latest_tgcr(
                    3
                ),
        )


        _print_observations(
            indicator_name="BGCR",

            observations=
                fetch_latest_bgcr(
                    3
                ),
        )


        _print_observations(
            indicator_name="EFFR",

            observations=
                fetch_latest_effr(
                    3
                ),
        )


        _print_observations(
            indicator_name="OBFR",

            observations=
                fetch_latest_obfr(
                    3
                ),
        )


    except NewYorkFedError as exc:

        print(
            f"Collector failed: "
            f"{exc}"
        )

        raise SystemExit(
            1
        ) from exc