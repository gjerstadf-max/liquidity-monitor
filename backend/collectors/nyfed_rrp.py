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