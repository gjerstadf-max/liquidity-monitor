from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from urllib import response
from dotenv import load_dotenv


import httpx

load_dotenv()

FRED_API_URL = (
    "https://api.stlouisfed.org/fred/series/observations"
)


@dataclass(frozen=True)
class FredObservation:
    series_id: str
    observation_date: date
    value: Decimal

class FredResponseError(RuntimeError):
    """FRED returned a successful HTTP response with invalid content."""

def fetch_fred_series(
    series_id: str,
    count: int = 20,
    vintage_date: date | None = None,
) -> list[FredObservation]:
    api_key = os.getenv("FRED_API_KEY")

    if not api_key:
        raise RuntimeError(
            "FRED_API_KEY environment variable is not set."
        )

    params = {
        "series_id": series_id,
        "api_key": api_key,
        "file_type": "json",
        "limit": count,
        "sort_order": "desc",
    }

    if vintage_date is not None:
        params["realtime_start"] = (
            vintage_date.isoformat()
        )
        params["realtime_end"] = (
            vintage_date.isoformat()
        )

    response = httpx.get(
        FRED_API_URL,
        params=params,
        timeout=20.0,
    )

    response.raise_for_status()

    try:
        payload = response.json()
    except ValueError as exc:
        content_type = response.headers.get(
            "content-type",
            "unknown",
        )

        raise FredResponseError(
            "FRED returned a non-JSON response "
            f"(status={response.status_code}, "
            f"content-type={content_type})."
        ) from exc

    observations = []

    for row in payload.get(
        "observations",
        []
    ):

        value = row.get("value")

        if (
            value is None
            or value == "."
        ):
            continue

        observations.append(
            FredObservation(
                series_id=series_id,

                observation_date=
                    date.fromisoformat(
                        row["date"]
                    ),

                value=Decimal(value),
            )
        )

    return observations


def fetch_reserve_balances(
    count: int = 20,
) -> list[FredObservation]:

    return fetch_fred_series(
        series_id="WRESBAL",
        count=count,
    )

def fetch_tga(
    count: int = 20,
) -> list[FredObservation]:
    """
    U.S. Treasury General Account.

    FRED series:
        WDTGAL

    Units:
        Millions of U.S. dollars

    Frequency:
        Weekly, Wednesday level
    """

    return fetch_fred_series(
        series_id="WDTGAL",
        count=count,
    )

def print_tga() -> None:

    observations = fetch_tga(10)

    print()
    print("Treasury General Account")
    print("================================")

    for observation in observations:

        billions = (
            observation.value
            / Decimal("1000")
        )

        print(
            f"{observation.observation_date}   "
            f"${billions:,.3f}B"
        )

def print_reserve_balances() -> None:

    observations = (
        fetch_reserve_balances(10)
    )

    print()
    print("Federal Reserve Balances")
    print("================================")

    for observation in observations:

        billions = (
            observation.value
            / Decimal("1000")
        )

        print(
            f"{observation.observation_date}   "
            f"${billions:,.3f}B"
        )


if __name__ == "__main__":
    print_tga()

    