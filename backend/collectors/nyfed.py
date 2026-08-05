from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any

import httpx


NY_FED_API_BASE_URL = "https://markets.newyorkfed.org/api"


class NewYorkFedError(Exception):
    """Base exception for New York Fed collector errors."""


class NewYorkFedRequestError(NewYorkFedError):
    """Raised when a New York Fed API request fails."""


class NewYorkFedDataError(NewYorkFedError):
    """Raised when the New York Fed returns missing or invalid data."""


@dataclass(frozen=True)
class ReferenceRateObservation:
    """One reference-rate observation from the New York Fed."""

    indicator_id: str
    observation_date: date
    rate: Decimal
    volume_billions: Decimal | None
    percentile_1: Decimal | None
    percentile_25: Decimal | None
    percentile_75: Decimal | None
    percentile_99: Decimal | None
    source: str = "Federal Reserve Bank of New York"


def _optional_decimal(value: Any) -> Decimal | None:
    """Convert an optional API value to Decimal."""

    if value in (None, "", "N/A"):
        return None

    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise NewYorkFedDataError(
            f"Could not convert value to Decimal: {value!r}"
        ) from exc


def _parse_reference_rate_record(
    record: dict[str, Any],
    indicator_id: str,
) -> ReferenceRateObservation:
    """Validate and convert one New York Fed reference-rate record."""

    try:
        observation_date = date.fromisoformat(record["effectiveDate"])
        rate = Decimal(str(record["percentRate"]))
    except KeyError as exc:
        raise NewYorkFedDataError(
            f"Required {indicator_id.upper()} field is missing: {exc.args[0]}"
        ) from exc
    except (ValueError, InvalidOperation, TypeError) as exc:
        raise NewYorkFedDataError(
            f"Invalid {indicator_id.upper()} record: {record!r}"
        ) from exc

    if rate < Decimal("0") or rate > Decimal("25"):
        raise NewYorkFedDataError(
            f"{indicator_id.upper()} value is outside "
            f"the validation range: {rate}"
        )

    return ReferenceRateObservation(
        indicator_id=indicator_id,
        observation_date=observation_date,
        rate=rate,
        volume_billions=_optional_decimal(
            record.get("volumeInBillions")
        ),
        percentile_1=_optional_decimal(
            record.get("percentPercentile1")
        ),
        percentile_25=_optional_decimal(
            record.get("percentPercentile25")
        ),
        percentile_75=_optional_decimal(
            record.get("percentPercentile75")
        ),
        percentile_99=_optional_decimal(
            record.get("percentPercentile99")
        ),
    )


def fetch_latest_reference_rate(
    indicator_id: str,
    observation_count: int = 5,
    timeout_seconds: float = 15.0,
) -> list[ReferenceRateObservation]:
    """
    Retrieve recent SOFR or EFFR observations from the New York Fed.

    This function retrieves and validates data only. It does not write
    to a database, calculate metrics, or generate commentary.
    """

    normalized_id = indicator_id.lower().strip()

    rate_configuration = {
        "sofr": "secured",
        "effr": "unsecured",
    }

    if normalized_id not in rate_configuration:
        supported = ", ".join(sorted(rate_configuration))

        raise ValueError(
            f"Unsupported reference rate: {indicator_id}. "
            f"Supported rates: {supported}"
        )

    if observation_count < 1 or observation_count > 100:
        raise ValueError(
            "observation_count must be between 1 and 100"
        )

    market_type = rate_configuration[normalized_id]

    url = (
        f"{NY_FED_API_BASE_URL}/rates/"
        f"{market_type}/{normalized_id}/"
        f"last/{observation_count}.json"
    )

    try:
        with httpx.Client(
            timeout=timeout_seconds,
            follow_redirects=True,
        ) as client:
            response = client.get(
                url,
                headers={
                    "Accept": "application/json",
                    "User-Agent": "LiquidityMonitor/0.1",
                },
            )

            response.raise_for_status()

    except httpx.HTTPError as exc:
        raise NewYorkFedRequestError(
            f"New York Fed {normalized_id.upper()} "
            f"request failed: {exc}"
        ) from exc

    try:
        payload = response.json()
    except ValueError as exc:
        raise NewYorkFedDataError(
            "New York Fed response was not valid JSON"
        ) from exc

    records = payload.get("refRates")

    if not isinstance(records, list):
        raise NewYorkFedDataError(
            "New York Fed response did not contain "
            "a refRates list"
        )

    if not records:
        raise NewYorkFedDataError(
            f"New York Fed returned no "
            f"{normalized_id.upper()} observations"
        )

    observations = [
        _parse_reference_rate_record(
            record=record,
            indicator_id=normalized_id,
        )
        for record in records
    ]

    return sorted(
        observations,
        key=lambda observation: observation.observation_date,
        reverse=True,
    )


def fetch_latest_sofr(
    observation_count: int = 5,
    timeout_seconds: float = 15.0,
) -> list[ReferenceRateObservation]:
    """Retrieve recent SOFR observations."""

    return fetch_latest_reference_rate(
        indicator_id="sofr",
        observation_count=observation_count,
        timeout_seconds=timeout_seconds,
    )


def fetch_latest_effr(
    observation_count: int = 5,
    timeout_seconds: float = 15.0,
) -> list[ReferenceRateObservation]:
    """Retrieve recent EFFR observations."""

    return fetch_latest_reference_rate(
        indicator_id="effr",
        observation_count=observation_count,
        timeout_seconds=timeout_seconds,
    )


def _print_observations(
    indicator_name: str,
    observations: list[ReferenceRateObservation],
) -> None:
    """Print observations for local testing."""

    print(f"\nLatest {indicator_name} observations\n")

    for observation in observations:
        volume = (
            f"${observation.volume_billions} billion"
            if observation.volume_billions is not None
            else "Not available"
        )

        print(
            f"{observation.observation_date}: "
            f"{observation.rate}% | "
            f"Volume: {volume}"
        )


if __name__ == "__main__":
    try:
        _print_observations(
            indicator_name="SOFR",
            observations=fetch_latest_sofr(5),
        )

        _print_observations(
            indicator_name="EFFR",
            observations=fetch_latest_effr(5),
        )

    except NewYorkFedError as exc:
        print(f"Collector failed: {exc}")
        raise SystemExit(1) from exc