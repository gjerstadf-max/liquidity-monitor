from __future__ import annotations

from dataclasses import dataclass

import httpx


NY_FED_MARKETS_BASE_URL = (
    "https://markets.newyorkfed.org"
)


# =============================================================
# EXCEPTIONS
# =============================================================


class PrimaryDealerRequestError(
    RuntimeError
):
    pass


class PrimaryDealerDataError(
    RuntimeError
):
    pass


# =============================================================
# DATA OBJECTS
# =============================================================


@dataclass(frozen=True)
class PrimaryDealerSeries:
    series_break: str
    key_id: str
    description: str


@dataclass(frozen=True)
class PrimaryDealerSeriesBreak:
    series_break: str
    label: str
    start_date: str
    end_date: str | None


# =============================================================
# HTTP
# =============================================================


def _get_json(
    path: str,
    timeout_seconds: float = 30.0,
) -> dict:

    url = (
        f"{NY_FED_MARKETS_BASE_URL}"
        f"{path}"
    )


    try:

        with httpx.Client(
            timeout=timeout_seconds,
            follow_redirects=True,
        ) as client:

            response = client.get(
                url,
                headers={
                    "Accept":
                        "application/json",

                    "User-Agent":
                        "LiquidityMonitor/0.1",
                },
            )


            response.raise_for_status()


    except httpx.HTTPError as exc:

        raise PrimaryDealerRequestError(
            "New York Fed Primary Dealer "
            f"request failed for {url}: "
            f"{exc}"
        ) from exc


    try:

        payload = (
            response.json()
        )


    except ValueError as exc:

        raise PrimaryDealerDataError(
            "New York Fed Primary Dealer "
            "response was not valid JSON."
        ) from exc


    if not isinstance(
        payload,
        dict,
    ):

        raise PrimaryDealerDataError(
            "New York Fed Primary Dealer "
            "response was not a JSON object."
        )


    return payload


# =============================================================
# SERIES BREAKS
# =============================================================


def fetch_primary_dealer_series_breaks(
) -> list[PrimaryDealerSeriesBreak]:
    """
    Retrieve all Primary Dealer reporting regimes.

    The NY Fed splits Primary Dealer history into
    separate series breaks when reporting definitions
    or structures change.
    """

    payload = (
        _get_json(
            "/api/pd/list/seriesbreaks.json"
        )
    )


    pd_payload = (
        payload.get(
            "pd"
        )
    )


    if not isinstance(
        pd_payload,
        dict,
    ):

        raise PrimaryDealerDataError(
            "Primary Dealer series-break response "
            "did not contain a pd object."
        )


    records = (
        pd_payload.get(
            "seriesbreaks"
        )
    )


    if not isinstance(
        records,
        list,
    ):

        raise PrimaryDealerDataError(
            "Primary Dealer response did not "
            "contain a seriesbreaks list."
        )


    results: list[
        PrimaryDealerSeriesBreak
    ] = []


    for record in records:

        if not isinstance(
            record,
            dict,
        ):
            continue


        series_break = (
            record.get(
                "seriesbreak"
            )
            or
            record.get(
                "seriesbreakid"
            )
        )


        label = (
            record.get(
                "label"
            )
            or
            ""
        )


        start_date = (
            record.get(
                "startdate"
            )
            or
            record.get(
                "startDate"
            )
            or
            ""
        )


        end_date = (
            record.get(
                "enddate"
            )
            or
            record.get(
                "endDate"
            )
        )


        if not series_break:

            continue


        results.append(
            PrimaryDealerSeriesBreak(
                series_break=
                    str(
                        series_break
                    ),

                label=
                    str(
                        label
                    ),

                start_date=
                    str(
                        start_date
                    ),

                end_date=(
                    str(
                        end_date
                    )
                    if end_date
                    else None
                ),
            )
        )


    if not results:

        raise PrimaryDealerDataError(
            "No Primary Dealer series breaks "
            "were returned."
        )


    return results


# =============================================================
# SERIES CATALOG
# =============================================================


def fetch_primary_dealer_series_catalog(
) -> list[PrimaryDealerSeries]:

    payload = (
        _get_json(
            "/api/pd/list/timeseries.json"
        )
    )


    pd_payload = (
        payload.get(
            "pd"
        )
    )


    if not isinstance(
        pd_payload,
        dict,
    ):

        raise PrimaryDealerDataError(
            "Primary Dealer response did not "
            "contain a pd object."
        )


    records = (
        pd_payload.get(
            "timeseries"
        )
    )


    if not isinstance(
        records,
        list,
    ):

        raise PrimaryDealerDataError(
            "Primary Dealer response did not "
            "contain a timeseries list."
        )


    series: list[
        PrimaryDealerSeries
    ] = []


    for record in records:

        if not isinstance(
            record,
            dict,
        ):
            continue


        series_break = (
            record.get(
                "seriesbreak"
            )
        )

        key_id = (
            record.get(
                "keyid"
            )
        )

        description = (
            record.get(
                "description"
            )
        )


        if not all(
            [
                series_break,
                key_id,
                description,
            ]
        ):
            continue


        series.append(
            PrimaryDealerSeries(
                series_break=
                    str(
                        series_break
                    ),

                key_id=
                    str(
                        key_id
                    ),

                description=
                    " ".join(
                        str(
                            description
                        ).split()
                    ),
            )
        )


    if not series:

        raise PrimaryDealerDataError(
            "No Primary Dealer time-series "
            "definitions were returned."
        )


    return series


# =============================================================
# SERIES FETCH
# =============================================================


def fetch_primary_dealer_timeseries(
    key_id: str,
    series_break: str | None = None,
) -> dict:

    normalized_key = (
        key_id.strip()
    )


    if not normalized_key:

        raise ValueError(
            "key_id cannot be empty."
        )


    if series_break:

        path = (
            f"/api/pd/get/"
            f"{series_break}/"
            f"timeseries/"
            f"{normalized_key}.json"
        )

    else:

        path = (
            f"/api/pd/get/"
            f"{normalized_key}.json"
        )


    return (
        _get_json(
            path
        )
    )