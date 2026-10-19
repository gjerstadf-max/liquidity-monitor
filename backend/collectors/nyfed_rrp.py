from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any

import httpx


BASE_URL = "https://markets.newyorkfed.org/api"


@dataclass(frozen=True)
class ReverseRepoObservation:
    operation_date: date

    total_accepted_dollars: Decimal

    participating_counterparties: int

    accepted_counterparties: int

    offering_rate: Decimal | None

    award_rate: Decimal | None

    @property
    def total_accepted_billions(
        self,
    ) -> Decimal:
        return (
            self.total_accepted_dollars
            / Decimal("1000000000")
        )

def _parse_operation(
    operation: dict[str, Any],
) -> ReverseRepoObservation:
    details = operation.get("details") or []

    offering_rate = None
    award_rate = None

    if details:
        first_detail = details[0]

        if first_detail.get("percentOfferingRate") is not None:
            offering_rate = Decimal(
                str(
                    first_detail[
                        "percentOfferingRate"
                    ]
                )
            )

        if first_detail.get("percentAwardRate") is not None:
            award_rate = Decimal(
                str(
                    first_detail[
                        "percentAwardRate"
                    ]
                )
            )

    return ReverseRepoObservation(
        operation_date=date.fromisoformat(
            operation["operationDate"]
        ),

        total_accepted_dollars=Decimal(
            str(
                operation[
                    "totalAmtAccepted"
                ]
            )
        ),

        participating_counterparties=int(
            operation.get(
                "participatingCpty",
                0,
            )
        ),

        accepted_counterparties=int(
            operation.get(
                "acceptedCpty",
                0,
            )
        ),

        offering_rate=offering_rate,

        award_rate=award_rate,
    )


def fetch_latest_reverse_repo(
    count: int = 5,
) -> list[ReverseRepoObservation]:
    """
    Fetch recent overnight fixed-rate reverse repo
    operation results from the New York Fed.

    Small-value exercises are excluded.
    """

    if count < 1:
        raise ValueError(
            "count must be at least 1"
        )

    url = (
        f"{BASE_URL}"
        f"/rp/reverserepo/all/results/"
        f"last/{count}.json"
    )

    response = httpx.get(
        url,
        timeout=20.0,
    )

    response.raise_for_status()

    payload = response.json()

    operations = (
        payload
        .get("repo", {})
        .get("operations", [])
    )

    observations = []

    for operation in operations:

        note = (
            operation.get("note")
            or ""
        ).lower()

        if "small value exercise" in note:
            continue

        if (
            operation.get("operationType")
            != "Reverse Repo"
        ):
            continue

        if (
            operation.get("operationMethod")
            != "Fixed Rate"
        ):
            continue

        if (
            operation.get("term")
            != "Overnight"
        ):
            continue

        observations.append(
            _parse_operation(operation)
        )

    return observations


def print_latest_reverse_repo() -> None:
    observations = (
        fetch_latest_reverse_repo(5)
    )

    print()
    print("New York Fed ON RRP")
    print("================================")

    for observation in observations:

        billions = (
            observation.total_accepted_dollars
            / Decimal("1000000000")
        )

        print()
        print(
            f"Date:                 "
            f"{observation.operation_date}"
        )

        print(
            f"Accepted:             "
            f"${billions:,.3f} billion"
        )

        print(
            f"Counterparties:       "
            f"{observation.accepted_counterparties}"
        )

        if observation.award_rate is not None:
            print(
                f"Award Rate:           "
                f"{observation.award_rate:.2f}%"
            )


if __name__ == "__main__":
    print_latest_reverse_repo()


# =============================================================
# HISTORICAL REVERSE-REPO COLLECTOR
# =============================================================


def fetch_reverse_repo_history(
    start_date: date,
    end_date: date,
    timeout_seconds: float = 30.0,
) -> list[
    tuple[
        date,
        Decimal,
    ]
]:
    """
    Retrieve historical New York Fed reverse-repo
    operation results over an explicit date range.

    Returned values are:

        (
            operation_date,
            total_accepted_dollars,
        )

    The production daily-refresh path remains separate
    and continues to use fetch_latest_reverse_repo().
    """
    if start_date > end_date:
        raise ValueError(
            "start_date cannot be after end_date"
        )

    url = (
        "https://markets.newyorkfed.org/api/"
        "rp/reverserepo/propositions/search.json"
    )

    params = {
        "startDate":
            start_date.isoformat(),
        "endDate":
            end_date.isoformat(),
    }

    try:
        with httpx.Client(
            timeout=
                timeout_seconds,
            follow_redirects=True,
        ) as client:
            response = client.get(
                url,
                params=params,
                headers={
                    "Accept":
                        "application/json",
                    "User-Agent":
                        "LiquidityMonitor/0.1",
                },
            )

            response.raise_for_status()

    except httpx.HTTPError as exc:
        raise RuntimeError(
            "New York Fed historical "
            "reverse-repo request failed: "
            f"{exc}"
        ) from exc

    try:
        payload = response.json()

    except ValueError as exc:
        raise RuntimeError(
            "New York Fed historical "
            "reverse-repo response was "
            "not valid JSON."
        ) from exc

    repo = payload.get(
        "repo"
    )

    if not isinstance(
        repo,
        dict,
    ):
        raise RuntimeError(
            "New York Fed historical "
            "reverse-repo response did not "
            "contain a repo object."
        )

    operations = repo.get(
        "operations"
    )

    if not isinstance(
        operations,
        list,
    ):
        raise RuntimeError(
            "New York Fed historical "
            "reverse-repo response did not "
            "contain an operations list."
        )

    values: list[
        tuple[
            date,
            Decimal,
        ]
    ] = []

    for record in operations:

        if not isinstance(
            record,
            dict,
        ):
            continue

        if (
            record.get(
                "operationType"
            )
            != "Reverse Repo"
        ):
            continue

        try:
            operation_date = (
                date.fromisoformat(
                    record[
                        "operationDate"
                    ]
                )
            )

            amount = Decimal(
                str(
                    record[
                        "totalAmtAccepted"
                    ]
                )
            )

        except (
            KeyError,
            ValueError,
            TypeError,
        ) as exc:
            raise RuntimeError(
                "Invalid historical reverse-repo "
                f"record: {record!r}"
            ) from exc

        values.append(
            (
                operation_date,
                amount,
            )
        )

    if not values:
        raise RuntimeError(
            "New York Fed returned no historical "
            "reverse-repo observations between "
            f"{start_date} and {end_date}."
        )

    return sorted(
        values,
        key=lambda item:
            item[0],
    )

