from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from backend.collectors.nyfed_primary_dealers import (
    fetch_primary_dealer_timeseries,
)


# =============================================================
# CORE TREASURY INTERMEDIATION CONCEPTS
# =============================================================

CORE_SERIES = {

    "Treasury Dealer Positions":
        "PDPOSGST-TOT",

    "Treasury Transactions":
        "PDGSWOEXTTOT",

    "Treasury Repo Financing":
        "PDSORA-UTSETTOT",

    "Treasury Reverse Repo Financing":
        "PDSIRRA-UTSETTOT",

    "Treasury Securities Borrowed":
        "PDSIOSB-UTSETTOT",

    "Treasury Securities Lent":
        "PDSOOS-UTSETTOT",

    "Treasury Fails to Receive":
        "PDFTR-USTET",

    "Treasury Fails to Deliver":
        "PDFTD-USTET",
}


# =============================================================
# OFFICIAL NY FED REPORTING REGIMES
# =============================================================
#
# These are intentionally explicit.
#
# We are not pretending the definitions are continuous
# across these boundaries.
# =============================================================


@dataclass(frozen=True)
class ReportingRegime:
    name: str
    start_date: date
    end_date: date | None


REGIMES = [

    ReportingRegime(
        name="1998-2001",
        start_date=date(
            1998,
            1,
            28,
        ),
        end_date=date(
            2001,
            6,
            30,
        ),
    ),

    ReportingRegime(
        name="2001-2013",
        start_date=date(
            2001,
            7,
            1,
        ),
        end_date=date(
            2013,
            3,
            31,
        ),
    ),

    ReportingRegime(
        name="2013-2014",
        start_date=date(
            2013,
            4,
            1,
        ),
        end_date=date(
            2014,
            12,
            31,
        ),
    ),

    ReportingRegime(
        name="2015-2021",
        start_date=date(
            2015,
            1,
            1,
        ),
        end_date=date(
            2022,
            1,
            4,
        ),
    ),

    ReportingRegime(
        name="2022-2024",
        start_date=date(
            2022,
            1,
            5,
        ),
        end_date=date(
            2024,
            7,
            2,
        ),
    ),

    ReportingRegime(
        name="2024-current",
        start_date=date(
            2024,
            7,
            3,
        ),
        end_date=None,
    ),
]


# =============================================================
# OBSERVATION OBJECT
# =============================================================


@dataclass(frozen=True)
class DealerObservation:
    observation_date: date
    key_id: str
    value: Decimal


# =============================================================
# PARSE NY FED RESPONSE
# =============================================================


def parse_timeseries_payload(
    payload: dict,
) -> list[
    DealerObservation
]:

    pd_payload = (
        payload.get(
            "pd"
        )
    )


    if not isinstance(
        pd_payload,
        dict,
    ):

        raise RuntimeError(
            "Response did not contain "
            "a pd object."
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

        raise RuntimeError(
            "Response did not contain "
            "a pd.timeseries list."
        )


    observations = []


    for record in records:

        if not isinstance(
            record,
            dict,
        ):
            continue


        raw_date = (
            record.get(
                "asofdate"
            )
        )

        key_id = (
            record.get(
                "keyid"
            )
        )

        raw_value = (
            record.get(
                "value"
            )
        )


        if (
            raw_date is None
            or
            key_id is None
            or
            raw_value is None
        ):

            continue


        try:

            observation_date = (
                date.fromisoformat(
                    str(
                        raw_date
                    )
                )
            )


            value = Decimal(
                str(
                    raw_value
                )
            )


        except Exception:

            continue


        observations.append(
            DealerObservation(
                observation_date=
                    observation_date,

                key_id=
                    str(
                        key_id
                    ),

                value=
                    value,
            )
        )


    return sorted(
        observations,
        key=lambda observation:
            observation.observation_date,
    )


# =============================================================
# REGIME LOOKUP
# =============================================================


def regime_for_date(
    observation_date: date,
) -> ReportingRegime | None:

    for regime in REGIMES:

        if (
            observation_date
            < regime.start_date
        ):

            continue


        if (
            regime.end_date
            is not None
            and
            observation_date
            > regime.end_date
        ):

            continue


        return regime


    return None


# =============================================================
# INSPECT ONE SERIES
# =============================================================


def inspect_series(
    label: str,
    key_id: str,
) -> None:

    print()
    print("=" * 110)

    print(
        label
    )

    print(
        f"Current key: {key_id}"
    )

    print("-" * 110)


    # IMPORTANT:
    #
    # No series_break supplied.
    #
    # According to the NY Fed API this requests
    # the time-series ID across all reporting
    # regimes in which that ID exists.

    payload = (
        fetch_primary_dealer_timeseries(
            key_id=
                key_id,

            series_break=
                None,
        )
    )


    observations = (
        parse_timeseries_payload(
            payload
        )
    )


    if not observations:

        print(
            "NO OBSERVATIONS RETURNED"
        )

        return


    print(
        f"Observations: "
        f"{len(observations)}"
    )

    print(
        f"Earliest:     "
        f"{observations[0].observation_date}"
    )

    print(
        f"Latest:       "
        f"{observations[-1].observation_date}"
    )


    # =========================================================
    # GROUP BY OFFICIAL REPORTING REGIME
    # =========================================================


    grouped: dict[
        str,
        list[
            DealerObservation
        ],
    ] = {
        regime.name: []
        for regime
        in REGIMES
    }


    unmapped = []


    for observation in observations:

        regime = (
            regime_for_date(
                observation.observation_date
            )
        )


        if regime is None:

            unmapped.append(
                observation
            )

            continue


        grouped[
            regime.name
        ].append(
            observation
        )


    print()
    print(
        f"{'Reporting Regime':<22}"
        f"{'Count':>8}"
        f"{'First':>15}"
        f"{'Last':>15}"
    )

    print("-" * 110)


    regimes_present = 0


    for regime in REGIMES:

        records = (
            grouped[
                regime.name
            ]
        )


        if not records:

            print(
                f"{regime.name:<22}"
                f"{0:>8}"
                f"{'-':>15}"
                f"{'-':>15}"
            )

            continue


        regimes_present += 1


        print(
            f"{regime.name:<22}"
            f"{len(records):>8}"
            f"{str(records[0].observation_date):>15}"
            f"{str(records[-1].observation_date):>15}"
        )


    print()


    if regimes_present == len(
        REGIMES
    ):

        print(
            "RESULT: CURRENT KEY EXISTS "
            "ACROSS ALL SIX REGIMES."
        )


    elif regimes_present > 1:

        print(
            f"RESULT: CURRENT KEY EXISTS "
            f"IN {regimes_present} OF "
            f"{len(REGIMES)} REGIMES."
        )

        print(
            "Historical predecessor mapping "
            "is required for the missing periods."
        )


    else:

        print(
            "RESULT: CURRENT KEY IS LIMITED "
            "TO ONE REPORTING REGIME."
        )

        print(
            "Historical predecessor mapping "
            "is required."
        )


    if unmapped:

        print()

        print(
            f"WARNING: "
            f"{len(unmapped)} observations "
            "fell outside the documented "
            "reporting periods."
        )


# =============================================================
# MAIN
# =============================================================


def main() -> None:

    print()
    print(
        "Liquidity Monitor — "
        "Primary Dealer Historical Mapping"
    )

    print("=" * 110)

    print()
    print(
        "Testing current Treasury intermediation "
        "series IDs across all official NY Fed "
        "reporting regimes."
    )


    for (
        label,
        key_id,
    ) in CORE_SERIES.items():

        try:

            inspect_series(
                label=
                    label,

                key_id=
                    key_id,
            )


        except Exception as exc:

            print()
            print("=" * 110)

            print(
                label
            )

            print(
                f"ERROR: "
                f"{type(exc).__name__}: "
                f"{exc}"
            )


    print()
    print("=" * 110)

    print(
        "Historical mapping inspection complete."
    )

    print("=" * 110)


if __name__ == "__main__":
    main()