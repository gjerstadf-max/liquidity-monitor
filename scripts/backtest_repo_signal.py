from __future__ import annotations

from datetime import date

from backend.metrics.repo_market import (
    latest_repo_market_snapshot,
    repo_market_statistics,
)
from backend.signals.repo_market import (
    evaluate_repo_market_signal,
)


# =============================================================
# TEST DATES
# =============================================================


TEST_DATES = [

    (
        "Normal 2019 baseline",
        date(2019, 6, 14),
    ),

    (
        "Before September 2019 event",
        date(2019, 9, 13),
    ),

    (
        "September 2019 — Day 1",
        date(2019, 9, 16),
    ),

    (
        "September 2019 — Day 2",
        date(2019, 9, 17),
    ),

    (
        "September 2019 — Day 3",
        date(2019, 9, 18),
    ),

    (
        "2019 year-end",
        date(2019, 12, 31),
    ),

    (
        "March 2020 — early stress",
        date(2020, 3, 12),
    ),

    (
        "March 2020 — escalation",
        date(2020, 3, 16),
    ),

    (
        "March 2020 — Fed response period",
        date(2020, 3, 23),
    ),

    (
        "March 2023 banking stress",
        date(2023, 3, 13),
    ),

    (
        "Current",
        date.today(),
    ),
]


# =============================================================
# FORMAT
# =============================================================


def metric_line(
    name: str,
    metric,
    units: str = "bp",
) -> None:

    print(
        f"{name:<24} "
        f"{float(metric.current):>8.1f} {units:<3} "
        f"z={metric.zscore_60d:>+6.2f} "
        f"pct={metric.percentile_60d:>5.0f}"
    )


# =============================================================
# ONE HISTORICAL REPLAY
# =============================================================


def run_test(
    label: str,
    requested_date: date,
) -> None:

    try:

        snapshot = (
            latest_repo_market_snapshot(
                as_of_date=
                    requested_date
            )
        )

        statistics = (
            repo_market_statistics(
                lookback=60,
                as_of_date=
                    requested_date,
            )
        )

        signal = (
            evaluate_repo_market_signal(
                as_of_date=
                    requested_date
            )
        )


    except RuntimeError as exc:

        print()
        print("=" * 80)

        print(
            f"{label}"
        )

        print(
            f"Requested: {requested_date}"
        )

        print(
            f"UNAVAILABLE: {exc}"
        )

        return


    print()
    print("=" * 80)

    print(
        label
    )

    print(
        f"Requested date:   "
        f"{requested_date}"
    )

    print(
        f"Observation date: "
        f"{snapshot.observation_date}"
    )

    print()

    print(
        f"SIGNAL: "
        f"{signal.severity.upper()}"
    )

    print(
        signal.title
    )


    print()
    print("Reference Rates")
    print("-" * 80)

    print(
        f"SOFR  {snapshot.sofr:.2f}%"
    )

    print(
        f"TGCR  {snapshot.tgcr:.2f}%"
    )

    print(
        f"BGCR  {snapshot.bgcr:.2f}%"
    )

    print(
        f"EFFR  {snapshot.effr:.2f}%"
    )

    print(
        f"OBFR  {snapshot.obfr:.2f}%"
    )


    print()
    print("Repo Diagnostics")
    print("-" * 80)

    metric_line(
        "SOFR - EFFR",
        statistics.sofr_effr,
    )

    metric_line(
        "SOFR - OBFR",
        statistics.sofr_obfr,
    )

    metric_line(
        "SOFR - TGCR",
        statistics.sofr_tgcr,
    )

    metric_line(
        "SOFR - BGCR",
        statistics.sofr_bgcr,
    )

    metric_line(
        "SOFR IQR",
        statistics.sofr_iqr,
    )

    metric_line(
        "SOFR 99th - median",
        statistics.sofr_upper_tail,
    )

    metric_line(
        "SOFR volume",
        statistics.sofr_volume,
        units="$B",
    )


    print()
    print("Interpretation")
    print("-" * 80)

    print(
        signal.message
    )


# =============================================================
# MAIN
# =============================================================


def main() -> None:

    print()
    print(
        "Liquidity Monitor — "
        "Historical Repo Signal Replay"
    )

    print("=" * 80)

    print(
        "Historical statistics use only "
        "information available on or before "
        "each test date."
    )


    for (
        label,
        test_date,
    ) in TEST_DATES:

        run_test(
            label=label,
            requested_date=
                test_date,
        )


    print()
    print("=" * 80)

    print(
        "Historical repo replay complete."
    )

    print("=" * 80)


if __name__ == "__main__":
    main()