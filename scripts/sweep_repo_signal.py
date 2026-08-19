from __future__ import annotations

import csv

from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

from backend.metrics.repo_market import (
    RepoMarketSnapshot,
    RepoMarketStatistics,
    _load_repo_history,
    _metric_context,
)
from backend.signals.repo_market import (
    evaluate_repo_market_statistics,
)


# =============================================================
# CONFIGURATION
# =============================================================

LOOKBACK = 60

OUTPUT_FILE = Path(
    "data/repo_signal_sweep.csv"
)


SEVERITY_ORDER = {
    "Normal": 0,
    "Watch": 1,
    "Warning": 2,
    "Critical": 3,
}


# =============================================================
# RESULT OBJECT
# =============================================================


@dataclass(frozen=True)
class SweepResult:

    snapshot: RepoMarketSnapshot

    statistics: RepoMarketStatistics

    severity: str

    title: str


# =============================================================
# BUILD STATISTICS FROM ONE 60-DAY WINDOW
# =============================================================


def build_statistics(
    window_descending: list[
        RepoMarketSnapshot
    ],
) -> RepoMarketStatistics:

    current = (
        window_descending[0]
    )


    return RepoMarketStatistics(

        observation_date=
            current.observation_date,

        observations_used=
            len(window_descending),


        sofr_effr=
            _metric_context(
                [
                    item.sofr_effr_spread_bp
                    for item
                    in window_descending
                ]
            ),


        sofr_obfr=
            _metric_context(
                [
                    item.sofr_obfr_spread_bp
                    for item
                    in window_descending
                ]
            ),


        sofr_tgcr=
            _metric_context(
                [
                    item.sofr_tgcr_spread_bp
                    for item
                    in window_descending
                ]
            ),


        sofr_bgcr=
            _metric_context(
                [
                    item.sofr_bgcr_spread_bp
                    for item
                    in window_descending
                ]
            ),


        sofr_iqr=
            _metric_context(
                [
                    item.sofr_iqr_bp
                    for item
                    in window_descending
                ]
            ),


        sofr_upper_tail=
            _metric_context(
                [
                    item.sofr_upper_tail_bp
                    for item
                    in window_descending
                ]
            ),


        sofr_volume=
            _metric_context(
                [
                    item.sofr_volume_billions
                    for item
                    in window_descending
                ]
            ),
    )


# =============================================================
# RUN FULL SWEEP
# =============================================================


def run_sweep() -> list[
    SweepResult
]:
    """
    Load the common repo history exactly once.

    Each historical date is evaluated using the
    preceding 60 common observations including
    the current date.

    Future observations are never used.
    """

    history_descending = (
        _load_repo_history()
    )


    history_ascending = list(
        reversed(
            history_descending
        )
    )


    if len(history_ascending) < LOOKBACK:

        raise RuntimeError(
            "Insufficient repo history "
            "for 60-observation sweep."
        )


    results: list[
        SweepResult
    ] = []


    for index in range(
        LOOKBACK - 1,
        len(history_ascending),
    ):

        window_ascending = (
            history_ascending[
                index
                - LOOKBACK
                + 1
                :
                index
                + 1
            ]
        )


        # Metrics expect current observation first.

        window_descending = list(
            reversed(
                window_ascending
            )
        )


        statistics = (
            build_statistics(
                window_descending
            )
        )


        signal = (
            evaluate_repo_market_statistics(
                statistics
            )
        )


        results.append(
            SweepResult(
                snapshot=
                    window_descending[0],

                statistics=
                    statistics,

                severity=
                    signal.severity,

                title=
                    signal.title,
            )
        )


    return results


# =============================================================
# CSV
# =============================================================


def write_csv(
    results: list[
        SweepResult
    ],
) -> None:

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )


    with OUTPUT_FILE.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.writer(
            file
        )


        writer.writerow(
            [
                "date",
                "severity",
                "title",

                "sofr",
                "effr",
                "obfr",
                "tgcr",
                "bgcr",

                "sofr_effr_bp",
                "sofr_effr_z",

                "sofr_obfr_bp",
                "sofr_obfr_z",

                "sofr_tgcr_bp",
                "sofr_tgcr_z",

                "sofr_bgcr_bp",
                "sofr_bgcr_z",

                "sofr_iqr_bp",
                "sofr_iqr_z",

                "sofr_upper_tail_bp",
                "sofr_upper_tail_z",

                "sofr_volume_billions",
                "sofr_volume_z",
            ]
        )


        for result in results:

            s = result.snapshot
            m = result.statistics


            writer.writerow(
                [
                    s.observation_date,
                    result.severity,
                    result.title,

                    s.sofr,
                    s.effr,
                    s.obfr,
                    s.tgcr,
                    s.bgcr,

                    m.sofr_effr.current,
                    round(
                        m.sofr_effr.zscore_60d,
                        4,
                    ),

                    m.sofr_obfr.current,
                    round(
                        m.sofr_obfr.zscore_60d,
                        4,
                    ),

                    m.sofr_tgcr.current,
                    round(
                        m.sofr_tgcr.zscore_60d,
                        4,
                    ),

                    m.sofr_bgcr.current,
                    round(
                        m.sofr_bgcr.zscore_60d,
                        4,
                    ),

                    m.sofr_iqr.current,
                    round(
                        m.sofr_iqr.zscore_60d,
                        4,
                    ),

                    m.sofr_upper_tail.current,
                    round(
                        m.sofr_upper_tail.zscore_60d,
                        4,
                    ),

                    m.sofr_volume.current,
                    round(
                        m.sofr_volume.zscore_60d,
                        4,
                    ),
                ]
            )


# =============================================================
# EPISODES
# =============================================================


def build_stress_episodes(
    results: list[
        SweepResult
    ],
) -> list[
    list[
        SweepResult
    ]
]:
    """
    Consecutive non-Normal observations form one
    stress episode.

    A return to Normal ends the episode.
    """

    episodes = []

    current_episode = []


    for result in results:

        if result.severity != "Normal":

            current_episode.append(
                result
            )

        else:

            if current_episode:

                episodes.append(
                    current_episode
                )

                current_episode = []


    if current_episode:

        episodes.append(
            current_episode
        )


    return episodes


def peak_severity(
    episode: list[
        SweepResult
    ],
) -> str:

    return max(
        (
            result.severity
            for result in episode
        ),
        key=lambda severity:
            SEVERITY_ORDER[
                severity
            ],
    )


# =============================================================
# SUMMARY
# =============================================================


def print_summary(
    results: list[
        SweepResult
    ],
) -> None:

    counts = Counter(
        result.severity
        for result in results
    )


    total = len(
        results
    )


    print()
    print(
        "Liquidity Monitor — "
        "Full Repo Signal Sweep"
    )

    print("=" * 80)


    print()
    print(
        f"First evaluated date: "
        f"{results[0].snapshot.observation_date}"
    )

    print(
        f"Last evaluated date:  "
        f"{results[-1].snapshot.observation_date}"
    )

    print(
        f"Observations:         "
        f"{total}"
    )


    print()
    print("Severity Distribution")
    print("-" * 80)


    for severity in [
        "Normal",
        "Watch",
        "Warning",
        "Critical",
    ]:

        count = counts[
            severity
        ]

        percentage = (
            count
            / total
            * 100
        )


        print(
            f"{severity:<10} "
            f"{count:>6} "
            f"{percentage:>7.2f}%"
        )


    non_normal = (
        total
        - counts["Normal"]
    )


    print()
    print(
        f"Non-Normal observations: "
        f"{non_normal} "
        f"({non_normal / total * 100:.2f}%)"
    )


# =============================================================
# YEAR-BY-YEAR
# =============================================================


def print_yearly_summary(
    results: list[
        SweepResult
    ],
) -> None:

    years = defaultdict(
        Counter
    )


    for result in results:

        year = (
            result
            .snapshot
            .observation_date
            .year
        )


        years[
            year
        ][
            result.severity
        ] += 1


    print()
    print("Year-by-Year")
    print("-" * 80)

    print(
        f"{'Year':<6}"
        f"{'Normal':>10}"
        f"{'Watch':>10}"
        f"{'Warning':>10}"
        f"{'Critical':>10}"
    )


    for year in sorted(
        years
    ):

        counts = years[
            year
        ]


        print(
            f"{year:<6}"
            f"{counts['Normal']:>10}"
            f"{counts['Watch']:>10}"
            f"{counts['Warning']:>10}"
            f"{counts['Critical']:>10}"
        )


# =============================================================
# STRESS EPISODES
# =============================================================


def print_stress_episodes(
    results: list[
        SweepResult
    ],
) -> None:

    episodes = (
        build_stress_episodes(
            results
        )
    )


    print()
    print("Non-Normal Episodes")
    print("-" * 80)


    if not episodes:

        print(
            "No non-Normal episodes."
        )

        return


    print(
        f"{'#':<4}"
        f"{'Start':<13}"
        f"{'End':<13}"
        f"{'Days':>6}"
        f"{'Peak':>12}"
    )


    for number, episode in enumerate(
        episodes,
        start=1,
    ):

        start = (
            episode[0]
            .snapshot
            .observation_date
        )

        end = (
            episode[-1]
            .snapshot
            .observation_date
        )

        peak = (
            peak_severity(
                episode
            )
        )


        print(
            f"{number:<4}"
            f"{str(start):<13}"
            f"{str(end):<13}"
            f"{len(episode):>6}"
            f"{peak:>12}"
        )


# =============================================================
# WARNING / CRITICAL DATES
# =============================================================


def print_major_dates(
    results: list[
        SweepResult
    ],
) -> None:

    major = [
        result
        for result in results
        if result.severity
        in {
            "Warning",
            "Critical",
        }
    ]


    print()
    print(
        "Warning / Critical Dates"
    )
    print("-" * 80)


    if not major:

        print(
            "None."
        )

        return


    for result in major:

        date_value = (
            result
            .snapshot
            .observation_date
        )

        stats = (
            result.statistics
        )


        print(
            f"{date_value}  "
            f"{result.severity:<8}  "
            f"SOFR-OBFR "
            f"{float(stats.sofr_obfr.current):>7.1f} bp  "
            f"IQR "
            f"{float(stats.sofr_iqr.current):>6.1f} bp  "
            f"Upper Tail "
            f"{float(stats.sofr_upper_tail.current):>7.1f} bp"
        )


# =============================================================
# MAIN
# =============================================================


def main() -> None:

    results = (
        run_sweep()
    )


    write_csv(
        results
    )


    print_summary(
        results
    )


    print_yearly_summary(
        results
    )


    print_stress_episodes(
        results
    )


    print_major_dates(
        results
    )


    print()
    print("=" * 80)

    print(
        f"Full daily results written to:"
    )

    print(
        OUTPUT_FILE
    )

    print("=" * 80)


if __name__ == "__main__":
    main()