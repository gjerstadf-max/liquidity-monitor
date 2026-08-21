from __future__ import annotations

from datetime import date

from backend.metrics.treasury_intermediation import (
    latest_treasury_intermediation_snapshot,
    treasury_intermediation_statistics,
)


TEST_DATES = [

    (
        "Normal 2019 baseline",
        date(2019, 6, 12),
    ),

    (
        "September 2019 repo event",
        date(2019, 9, 18),
    ),

    (
        "March 2020 early stress",
        date(2020, 3, 11),
    ),

    (
        "March 2020 peak stress",
        date(2020, 3, 18),
    ),

    (
        "March 2020 aftermath",
        date(2020, 3, 25),
    ),

    (
        "2022 Treasury volatility",
        date(2022, 10, 12),
    ),

    (
        "March 2023 banking stress",
        date(2023, 3, 15),
    ),

    (
        "October 2025 liquidity stress",
        date(2025, 10, 15),
    ),

    (
        "October 2025 continuation",
        date(2025, 10, 22),
    ),

    (
        "Current",
        date.today(),
    ),
]


def metric_line(
    name: str,
    metric,
) -> None:

    print(
        f"{name:<28}"
        f"{float(metric.current):>10,.1f}B  "
        f"4w={float(metric.change_4_week):>+9,.1f}B  "
        f"13w={float(metric.change_13_week):>+9,.1f}B  "
        f"z={metric.zscore_52_week:>+6.2f}  "
        f"pct={metric.percentile_52_week:>5.0f}"
    )


def run_test(
    label: str,
    requested_date: date,
) -> None:

    try:

        snapshot = (
            latest_treasury_intermediation_snapshot(
                as_of_date=requested_date
            )
        )

        stats = (
            treasury_intermediation_statistics(
                as_of_date=requested_date
            )
        )

    except RuntimeError as exc:

        print()
        print("=" * 100)

        print(label)

        print(
            f"Requested: {requested_date}"
        )

        print(
            f"UNAVAILABLE: {exc}"
        )

        return


    print()
    print("=" * 100)

    print(label)

    print(
        f"Requested date:   "
        f"{requested_date}"
    )

    print(
        f"Observation date: "
        f"{snapshot.observation_date}"
    )


    print()
    print("CORE INTERMEDIATION DIAGNOSTICS")
    print("-" * 100)


    metric_line(
        "Dealer Positions",
        stats.dealer_positions,
    )

    metric_line(
        "Treasury Transactions",
        stats.treasury_transactions,
    )

    metric_line(
        "Securities Borrowed",
        stats.securities_borrowed,
    )

    metric_line(
        "Fails to Receive",
        stats.fails_receive,
    )

    metric_line(
        "Fails to Deliver",
        stats.fails_deliver,
    )

    metric_line(
        "Total Treasury Fails",
        stats.total_fails,
    )


    print()
    print("SUPPORTING FINANCING")
    print("-" * 100)


    if snapshot.repo_billions is None:

        print(
            "Treasury repo:         "
            "suppressed / unavailable"
        )

    else:

        print(
            f"Treasury repo:         "
            f"${float(snapshot.repo_billions):,.1f}B"
        )


    if snapshot.reverse_repo_billions is None:

        print(
            "Treasury reverse repo: "
            "suppressed / unavailable"
        )

    else:

        print(
            f"Treasury reverse repo: "
            f"${float(snapshot.reverse_repo_billions):,.1f}B"
        )


def main() -> None:

    print()
    print(
        "Liquidity Monitor — "
        "Treasury Intermediation Historical Replay"
    )

    print("=" * 100)

    print(
        "All historical statistics use only "
        "observations available on or before "
        "each replay date."
    )


    for (
        label,
        test_date,
    ) in TEST_DATES:

        run_test(
            label,
            test_date,
        )


    print()
    print("=" * 100)

    print(
        "Historical Treasury intermediation "
        "replay complete."
    )

    print("=" * 100)


if __name__ == "__main__":
    main()