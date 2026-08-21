from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation

from backend.collectors.nyfed_primary_dealers import (
    fetch_primary_dealer_timeseries,
)


# =============================================================
# CORE FACTOR #4 SERIES
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
# CANONICAL FACTOR HISTORY
# =============================================================
#
# April 2013 is intentional.
#
# Before April 2013, primary dealers did not report
# Treasury-specific repo/reverse-repo collateral in the
# same form, so we do not manufacture continuity.
# =============================================================


@dataclass(frozen=True)
class Regime:
    name: str
    start_date: date
    end_date: date | None


REGIMES = [

    Regime(
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

    Regime(
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

    Regime(
        name="2022-Jun2024",
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

    Regime(
        name="Jul2024-current",
        start_date=date(
            2024,
            7,
            3,
        ),
        end_date=None,
    ),
]


# =============================================================
# RAW RECORD
# =============================================================


@dataclass(frozen=True)
class RawRecord:
    observation_date: date
    raw_value: str
    numeric_value: Decimal | None


# =============================================================
# PARSE
# =============================================================


def parse_raw_records(
    payload: dict,
) -> list[RawRecord]:

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
            "Primary Dealer payload "
            "did not contain a pd object."
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
            "Primary Dealer payload "
            "did not contain a timeseries list."
        )


    parsed: list[
        RawRecord
    ] = []


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

        raw_value = (
            record.get(
                "value"
            )
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


        value_text = (
            ""
            if raw_value is None
            else str(
                raw_value
            ).strip()
        )


        numeric_value = None


        if value_text not in {
            "",
            "*",
            "NA",
            "N/A",
            "null",
            "None",
        }:

            try:

                numeric_value = (
                    Decimal(
                        value_text
                    )
                )

            except (
                InvalidOperation,
                ValueError,
            ):

                numeric_value = None


        parsed.append(
            RawRecord(
                observation_date=
                    observation_date,

                raw_value=
                    value_text,

                numeric_value=
                    numeric_value,
            )
        )


    return sorted(
        parsed,
        key=lambda item:
            item.observation_date,
    )


# =============================================================
# REGIME
# =============================================================


def regime_for_date(
    observation_date: date,
) -> Regime | None:

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
# AUDIT ONE SERIES
# =============================================================


def audit_series(
    label: str,
    key_id: str,
) -> None:

    print()
    print("=" * 110)

    print(
        label
    )

    print(
        f"Key: {key_id}"
    )

    print("-" * 110)


    payload = (
        fetch_primary_dealer_timeseries(
            key_id=
                key_id,

            series_break=
                None,
        )
    )


    records = (
        parse_raw_records(
            payload
        )
    )


    if not records:

        print(
            "NO RECORDS"
        )

        return


    print(
        f"Raw records: "
        f"{len(records)}"
    )

    print(
        f"Earliest:    "
        f"{records[0].observation_date}"
    )

    print(
        f"Latest:      "
        f"{records[-1].observation_date}"
    )


    print()
    print(
        f"{'Regime':<20}"
        f"{'Raw':>8}"
        f"{'Numeric':>10}"
        f"{'Missing':>10}"
        f"{'Coverage':>12}"
        f"{'First Numeric':>16}"
        f"{'Last Numeric':>16}"
    )

    print("-" * 110)


    all_missing: list[
        RawRecord
    ] = []


    for regime in REGIMES:

        regime_records = [
            record
            for record
            in records

            if regime_for_date(
                record.observation_date
            ) == regime
        ]


        numeric_records = [
            record
            for record
            in regime_records

            if record.numeric_value
            is not None
        ]


        missing_records = [
            record
            for record
            in regime_records

            if record.numeric_value
            is None
        ]


        all_missing.extend(
            missing_records
        )


        raw_count = len(
            regime_records
        )

        numeric_count = len(
            numeric_records
        )

        missing_count = len(
            missing_records
        )


        coverage = (
            numeric_count
            / raw_count
            * 100
            if raw_count
            else 0.0
        )


        first_numeric = (
            str(
                numeric_records[
                    0
                ].observation_date
            )
            if numeric_records
            else "-"
        )


        last_numeric = (
            str(
                numeric_records[
                    -1
                ].observation_date
            )
            if numeric_records
            else "-"
        )


        print(
            f"{regime.name:<20}"
            f"{raw_count:>8}"
            f"{numeric_count:>10}"
            f"{missing_count:>10}"
            f"{coverage:>11.1f}%"
            f"{first_numeric:>16}"
            f"{last_numeric:>16}"
        )


    # =========================================================
    # MISSING / SUPPRESSED VALUES
    # =========================================================


    if all_missing:

        print()
        print(
            "NON-NUMERIC / SUPPRESSED RECORDS"
        )

        print("-" * 110)


        for record in (
            all_missing[:20]
        ):

            print(
                f"{record.observation_date}   "
                f"value={record.raw_value!r}"
            )


        if len(
            all_missing
        ) > 20:

            print(
                f"... plus "
                f"{len(all_missing) - 20} "
                "additional records"
            )


    else:

        print()
        print(
            "No non-numeric observations."
        )


# =============================================================
# MAIN
# =============================================================


def main() -> None:

    print()
    print(
        "Liquidity Monitor — "
        "Primary Dealer Coverage Audit"
    )

    print("=" * 110)

    print()
    print(
        "Canonical Factor #4 history begins "
        "April 2013."
    )

    print(
        "Missing NY Fed observations are treated "
        "as unavailable — never as zero."
    )


    for (
        label,
        key_id,
    ) in CORE_SERIES.items():

        try:

            audit_series(
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
        "Primary Dealer coverage audit complete."
    )

    print("=" * 110)


if __name__ == "__main__":
    main()