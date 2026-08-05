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
    """Raised when the API request fails."""


class NewYorkFedDataError(NewYorkFedError):
    """Raised when the API returns missing or invalid data."""


@dataclass(frozen=True)
class ReferenceRateObservation:
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


def _parse_sofr_record(record: dict[str, Any]) -> ReferenceRateObservation:
    """Validate and convert one New York Fed SOFR record."""

    try:
        observation_date = date.fromisoformat(record["effectiveDate"])
        rate = Decimal(str(record["percentRate"]))
    except KeyError as exc:
        raise NewYorkFedDataError(
            f"Required SOFR field is missing: {exc.args[0]}"
        ) from exc
    except (ValueError, InvalidOperation, TypeError) as exc:
        raise NewYorkFedDataError(
            f"Invalid SOFR record: {record!r}"
        ) from exc

    if rate < Decimal("0") or rate > Decimal("25"):
        raise NewYorkFedDataError(
            f"SOFR value is outside the validation range: {rate}"
        )

    return ReferenceRateObservation(
        indicator_id="sofr",
        observation_date=observation_date,
        rate=rate,
        volume_billions=_optional_decimal(record.get("volumeInBillions")),
        percentile_1=_optional_decimal(record.get("percentPercentile1")),
        percentile_25=_optional_decimal(record.get("percentPercentile25")),
        percentile_75=_optional_decimal(record.get("percentPercentile75")),
        percentile_99=_optional_decimal(record.get("percentPercentile99")),
    )


def fetch_latest_sofr(
    observation_count: int = 5,
    timeout_seconds: float = 15.0,
) -> list[ReferenceRateObservation]:
    """
    Retrieve recent SOFR observations from the New York Fed.

    The function retrieves data only. It does not write to a database,
    calculate metrics, or generate commentary.
    """

    if observation_count < 1 or observation_count > 100:
        raise ValueError("observation_count must be between 1 and 100")

    url = (
        f"{NY_FED_API_BASE_URL}/rates/secured/sofr/"
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
            f"New York Fed request failed: {exc}"
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
            "New York Fed response did not contain a refRates list"
        )

    if not records:
        raise NewYorkFedDataError(
            "New York Fed returned no SOFR observations"
        )

    observations = [_parse_sofr_record(record) for record in records]

    return sorted(
        observations,
        key=lambda observation: observation.observation_date,
        reverse=True,
    )


if __name__ == "__main__":
    try:
        sofr_observations = fetch_latest_sofr(5)

        print("\nLatest SOFR observations\n")

        for observation in sofr_observations:
            volume = (
                f"${observation.volume_billions} billion"
                if observation.volume_billions is not None
                else "Not available"
            )

            print(
                f"{observation.observation_date}: "
                f"{observation.rate}% | Volume: {volume}"
            )

    except NewYorkFedError as exc:
        print(f"Collector failed: {exc}")
        raise SystemExit(1) from exc