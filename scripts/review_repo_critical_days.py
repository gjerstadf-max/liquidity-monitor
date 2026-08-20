from __future__ import annotations

import csv

from pathlib import Path

from backend.signals.repo_market import (
    ECONOMIC_THRESHOLDS,
    _dispersion_statistically_elevated,
    _dispersion_statistically_strong,
    _economically_elevated,
    _economically_strong,
    _spread_statistically_elevated,
    _spread_statistically_strong,
)
from scripts.sweep_repo_signal import (
    SweepResult,
    run_sweep,
)


OUTPUT_FILE = Path(
    "data/repo_critical_day_review.csv"
)


# =============================================================
# PRIMARY DIAGNOSTICS
# =============================================================


def diagnostic_map(
    result: SweepResult,
):
    stats = result.statistics

    return {
        "SOFR-OBFR": (
            stats.sofr_obfr,
            "spread",
        ),

        "SOFR-TGCR": (
            stats.sofr_tgcr,
            "spread",
        ),

        "SOFR-BGCR": (
            stats.sofr_bgcr,
            "spread",
        ),

        "SOFR interquartile range": (
            stats.sofr_iqr,
            "dispersion",
        ),

        "SOFR upper tail": (
            stats.sofr_upper_tail,
            "dispersion",
        ),
    }


# =============================================================
# CLASSIFICATION
# =============================================================


def classify_diagnostic(
    name: str,
    metric,
    metric_type: str,
) -> dict:

    if metric_type == "spread":

        statistical_elevated = (
            _spread_statistically_elevated(
                metric
            )
        )

        statistical_strong = (
            _spread_statistically_strong(
                metric
            )
        )

    else:

        statistical_elevated = (
            _dispersion_statistically_elevated(
                metric
            )
        )

        statistical_strong = (
            _dispersion_statistically_strong(
                metric
            )
        )


    meaningful_elevated = (
        statistical_elevated
        and
        _economically_elevated(
            name,
            metric,
        )
    )


    meaningful_strong = (
        statistical_strong
        and
        _economically_strong(
            name,
            metric,
        )
    )


    return {
        "name":
            name,

        "current":
            float(
                metric.current
            ),

        "zscore":
            metric.zscore_60d,

        "percentile":
            metric.percentile_60d,

        "statistical_elevated":
            statistical_elevated,

        "statistical_strong":
            statistical_strong,

        "meaningful_elevated":
            meaningful_elevated,

        "meaningful_strong":
            meaningful_strong,

        "elevated_floor":
            ECONOMIC_THRESHOLDS[
                name
            ][
                "elevated"
            ],

        "strong_floor":
            ECONOMIC_THRESHOLDS[
                name
            ][
                "strong"
            ],
    }


# =============================================================
# CALENDAR CONTEXT
# =============================================================


def calendar_context(
    index: int,
    results: list[
        SweepResult
    ],
) -> str:
    """
    Classify repo observations around month-end,
    quarter-end, and year-end turns.

    Recognizes:
        Pre month-end
        Month-end
        Post month-end

        Pre quarter-end
        Quarter-end
        Post quarter-end

        Pre year-end
        Year-end
        Post year-end

    Uses the sequence of actual repo observation
    dates, so weekends and holidays are handled
    naturally.
    """

    current_date = (
        results[
            index
        ]
        .snapshot
        .observation_date
    )


    previous_date = None

    if index > 0:

        previous_date = (
            results[
                index - 1
            ]
            .snapshot
            .observation_date
        )


    next_date = None

    if index + 1 < len(
        results
    ):

        next_date = (
            results[
                index + 1
            ]
            .snapshot
            .observation_date
        )


    next_next_date = None

    if index + 2 < len(
        results
    ):

        next_next_date = (
            results[
                index + 2
            ]
            .snapshot
            .observation_date
        )


    # =========================================================
    # HELPER
    # =========================================================

    def turn_label(
        month: int,
        position: str,
    ) -> str:

        if month == 12:

            turn = "year-end"

        elif month in {
            3,
            6,
            9,
        }:

            turn = "quarter-end"

        else:

            turn = "month-end"


        if position == "exact":

            return (
                turn.capitalize()
            )


        return (
            f"{position.capitalize()} "
            f"{turn}"
        )


    # =========================================================
    # EXACT TURN
    # =========================================================
    #
    # Current observation is the final repo observation
    # of the month.
    # =========================================================

    if (
        next_date is None
        or
        next_date.month
        != current_date.month
        or
        next_date.year
        != current_date.year
    ):

        return turn_label(
            month=
                current_date.month,

            position=
                "exact",
        )


    # =========================================================
    # POST TURN
    # =========================================================
    #
    # Current observation is the first repo observation
    # of a new month.
    # =========================================================

    if previous_date is not None:

        crossed_month = (
            previous_date.month
            != current_date.month
            or
            previous_date.year
            != current_date.year
        )


        if crossed_month:

            return turn_label(
                month=
                    previous_date.month,

                position=
                    "post",
            )


    # =========================================================
    # PRE TURN
    # =========================================================
    #
    # Next observation is the final repo observation
    # of its month.
    #
    # Example:
    #
    #   2023-12-28  -> Pre year-end
    #   2023-12-29  -> Year-end
    #   2024-01-02  -> Post year-end
    #
    # =========================================================

    if (
        next_date is not None
        and
        (
            next_next_date is None
            or
            next_next_date.month
            != next_date.month
            or
            next_next_date.year
            != next_date.year
        )
    ):

        return turn_label(
            month=
                next_date.month,

            position=
                "pre",
        )


    # =========================================================
    # ORDINARY DATE
    # =========================================================

    return (
        "Ordinary date"
    )

# =============================================================
# ATTRIBUTION
# =============================================================


def build_attribution(
    result: SweepResult,
) -> dict:

    classifications = []


    for (
        name,
        (
            metric,
            metric_type,
        ),
    ) in diagnostic_map(
        result
    ).items():

        classifications.append(
            classify_diagnostic(
                name=
                    name,

                metric=
                    metric,

                metric_type=
                    metric_type,
            )
        )


    meaningful_elevated = [
        item["name"]
        for item
        in classifications
        if item[
            "meaningful_elevated"
        ]
    ]


    meaningful_strong = [
        item["name"]
        for item
        in classifications
        if item[
            "meaningful_strong"
        ]
    ]


    statistical_only = [
        item["name"]
        for item
        in classifications
        if (
            item[
                "statistical_elevated"
            ]
            and
            not item[
                "meaningful_elevated"
            ]
        )
    ]


    return {
        "classifications":
            classifications,

        "meaningful_elevated":
            meaningful_elevated,

        "meaningful_strong":
            meaningful_strong,

        "statistical_only":
            statistical_only,
    }


# =============================================================
# PRINT ONE CRITICAL DAY
# =============================================================


def print_critical_day(
    number: int,
    index: int,
    results: list[
        SweepResult
    ],
) -> None:

    result = results[
        index
    ]

    snapshot = (
        result.snapshot
    )

    stats = (
        result.statistics
    )

    attribution = (
        build_attribution(
            result
        )
    )


    context = (
        calendar_context(
            index,
            results,
        )
    )


    print()
    print("=" * 100)

    print(
        f"{number:>2}. "
        f"{snapshot.observation_date}  "
        f"[{context}]"
    )

    print("-" * 100)


    print(
        f"SOFR={float(snapshot.sofr):.2f}%  "
        f"OBFR={float(snapshot.obfr):.2f}%  "
        f"TGCR={float(snapshot.tgcr):.2f}%  "
        f"BGCR={float(snapshot.bgcr):.2f}%"
    )


    print(
        f"SOFR-OBFR="
        f"{float(stats.sofr_obfr.current):+.1f} bp   "
        f"IQR="
        f"{float(stats.sofr_iqr.current):.1f} bp   "
        f"Upper Tail="
        f"{float(stats.sofr_upper_tail.current):.1f} bp   "
        f"Volume="
        f"${float(stats.sofr_volume.current):,.0f}B"
    )


    print()

    print(
        "Meaningful elevated: "
        + (
            ", ".join(
                attribution[
                    "meaningful_elevated"
                ]
            )
            or
            "None"
        )
    )


    print(
        "Meaningful strong:   "
        + (
            ", ".join(
                attribution[
                    "meaningful_strong"
                ]
            )
            or
            "None"
        )
    )


    if attribution[
        "statistical_only"
    ]:

        print(
            "Statistical only:   "
            + ", ".join(
                attribution[
                    "statistical_only"
                ]
            )
        )


    print()
    print(
        f"{'Diagnostic':<30}"
        f"{'Value':>9}"
        f"{'Z':>8}"
        f"{'Pct':>7}"
        f"{'Elev':>8}"
        f"{'Strong':>9}"
    )

    print("-" * 100)


    for item in attribution[
        "classifications"
    ]:

        print(
            f"{item['name']:<30}"
            f"{item['current']:>9.1f}"
            f"{item['zscore']:>+8.2f}"
            f"{item['percentile']:>7.0f}"
            f"{'YES' if item['meaningful_elevated'] else '-':>8}"
            f"{'YES' if item['meaningful_strong'] else '-':>9}"
        )


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


    critical_indices = [
        index
        for index, result
        in enumerate(
            results
        )
        if result.severity
        == "Critical"
    ]


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
                "calendar_context",

                "sofr",
                "obfr",
                "tgcr",
                "bgcr",

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

                "meaningful_elevated",
                "meaningful_strong",
                "statistical_only",

                "market_context",
                "review_classification",
                "review_notes",
            ]
        )


        for index in critical_indices:

            result = results[
                index
            ]

            snapshot = (
                result.snapshot
            )

            stats = (
                result.statistics
            )

            attribution = (
                build_attribution(
                    result
                )
            )


            writer.writerow(
                [
                    snapshot.observation_date,

                    calendar_context(
                        index,
                        results,
                    ),

                    snapshot.sofr,
                    snapshot.obfr,
                    snapshot.tgcr,
                    snapshot.bgcr,

                    stats.sofr_obfr.current,
                    round(
                        stats.sofr_obfr.zscore_60d,
                        4,
                    ),

                    stats.sofr_tgcr.current,
                    round(
                        stats.sofr_tgcr.zscore_60d,
                        4,
                    ),

                    stats.sofr_bgcr.current,
                    round(
                        stats.sofr_bgcr.zscore_60d,
                        4,
                    ),

                    stats.sofr_iqr.current,
                    round(
                        stats.sofr_iqr.zscore_60d,
                        4,
                    ),

                    stats.sofr_upper_tail.current,
                    round(
                        stats.sofr_upper_tail.zscore_60d,
                        4,
                    ),

                    stats.sofr_volume.current,
                    round(
                        stats.sofr_volume.zscore_60d,
                        4,
                    ),

                    "; ".join(
                        attribution[
                            "meaningful_elevated"
                        ]
                    ),

                    "; ".join(
                        attribution[
                            "meaningful_strong"
                        ]
                    ),

                    "; ".join(
                        attribution[
                            "statistical_only"
                        ]
                    ),

                    # Intentionally blank.
                    # These become our human validation
                    # fields for the 17-event review.

                    "",
                    "",
                    "",
                ]
            )


# =============================================================
# MAIN
# =============================================================


def main() -> None:

    results = (
        run_sweep()
    )


    critical_indices = [
        index
        for index, result
        in enumerate(
            results
        )
        if result.severity
        == "Critical"
    ]


    print()
    print(
        "Liquidity Monitor — "
        "Critical Repo Event Review"
    )

    print("=" * 100)

    print(
        f"Critical observations: "
        f"{len(critical_indices)}"
    )


    for number, index in enumerate(
        critical_indices,
        start=1,
    ):

        print_critical_day(
            number=
                number,

            index=
                index,

            results=
                results,
        )


    write_csv(
        results
    )


    print()
    print("=" * 100)

    print(
        "Critical-event review written to:"
    )

    print(
        OUTPUT_FILE
    )

    print("=" * 100)


if __name__ == "__main__":
    main()