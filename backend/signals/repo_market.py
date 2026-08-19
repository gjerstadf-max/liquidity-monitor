from __future__ import annotations

from datetime import date

from backend.metrics.repo_market import (
    RepoMetricContext,
    RepoMarketStatistics,
    repo_market_statistics,
)
from backend.signals.models import Signal


# =============================================================
# ECONOMIC MAGNITUDE THRESHOLDS
# =============================================================
#
# Statistical abnormality alone can create a Watch.
#
# Warning / Critical require the observation to be both:
#
#   1. unusual relative to recent history
#   2. economically meaningful in absolute magnitude
#
# This prevents quiet-market z-scores from creating
# disproportionate Warning / Critical signals.
# =============================================================


ECONOMIC_THRESHOLDS = {

    "SOFR-OBFR": {
        "elevated": 10.0,
        "strong": 20.0,
    },

    "SOFR-TGCR": {
        "elevated": 3.0,
        "strong": 5.0,
    },

    "SOFR-BGCR": {
        "elevated": 3.0,
        "strong": 5.0,
    },

    "SOFR interquartile range": {
        "elevated": 10.0,
        "strong": 20.0,
    },

    "SOFR upper tail": {
        "elevated": 30.0,
        "strong": 100.0,
    },
}


# =============================================================
# STATISTICAL TESTS
# =============================================================


def _spread_statistically_elevated(
    metric: RepoMetricContext,
) -> bool:

    return (
        float(metric.current) > 0
        and (
            metric.zscore_60d >= 1.25
            or metric.percentile_60d >= 90
        )
    )


def _spread_statistically_strong(
    metric: RepoMetricContext,
) -> bool:

    return (
        float(metric.current) > 0
        and (
            metric.zscore_60d >= 2.0
            or metric.percentile_60d >= 97
        )
    )


def _dispersion_statistically_elevated(
    metric: RepoMetricContext,
) -> bool:

    return (
        metric.zscore_60d >= 1.25
        or metric.percentile_60d >= 90
    )


def _dispersion_statistically_strong(
    metric: RepoMetricContext,
) -> bool:

    return (
        metric.zscore_60d >= 2.0
        or metric.percentile_60d >= 97
    )


# =============================================================
# ECONOMIC MAGNITUDE TESTS
# =============================================================


def _economically_elevated(
    name: str,
    metric: RepoMetricContext,
) -> bool:

    threshold = (
        ECONOMIC_THRESHOLDS[
            name
        ][
            "elevated"
        ]
    )

    return (
        float(metric.current)
        >= threshold
    )


def _economically_strong(
    name: str,
    metric: RepoMetricContext,
) -> bool:

    threshold = (
        ECONOMIC_THRESHOLDS[
            name
        ][
            "strong"
        ]
    )

    return (
        float(metric.current)
        >= threshold
    )


# =============================================================
# COMBINED TESTS
# =============================================================


def _qualified_elevated(
    name: str,
    metric: RepoMetricContext,
    metric_type: str,
) -> bool:

    if metric_type == "spread":

        statistically_unusual = (
            _spread_statistically_elevated(
                metric
            )
        )

    else:

        statistically_unusual = (
            _dispersion_statistically_elevated(
                metric
            )
        )


    return (
        statistically_unusual
        and
        _economically_elevated(
            name,
            metric,
        )
    )


def _qualified_strong(
    name: str,
    metric: RepoMetricContext,
    metric_type: str,
) -> bool:

    if metric_type == "spread":

        statistically_strong = (
            _spread_statistically_strong(
                metric
            )
        )

    else:

        statistically_strong = (
            _dispersion_statistically_strong(
                metric
            )
        )


    return (
        statistically_strong
        and
        _economically_strong(
            name,
            metric,
        )
    )


def _statistically_elevated(
    metric: RepoMetricContext,
    metric_type: str,
) -> bool:

    if metric_type == "spread":

        return (
            _spread_statistically_elevated(
                metric
            )
        )


    return (
        _dispersion_statistically_elevated(
            metric
        )
    )


# =============================================================
# DISPLAY
# =============================================================


def _format_bp(
    value,
) -> str:

    return (
        f"{float(value):+.1f} bp"
    )


# =============================================================
# CORE SIGNAL LOGIC
# =============================================================


def evaluate_repo_market_statistics(
    stats: RepoMarketStatistics,
) -> Signal:
    """
    Repo Signal V2.

    Watch:
        Can be triggered by relative statistical
        abnormality.

    Warning / Critical:
        Require statistical abnormality AND
        economically meaningful absolute magnitude.

    Both live monitoring and historical replay use
    this exact function.
    """

    primary_metrics = {

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


    # =========================================================
    # CLASSIFY PRIMARY DIAGNOSTICS
    # =========================================================

    statistical_elevated: list[str] = []

    meaningful_elevated: list[str] = []

    meaningful_strong: list[str] = []


    for (
        name,
        (
            metric,
            metric_type,
        ),
    ) in primary_metrics.items():

        if _statistically_elevated(
            metric,
            metric_type,
        ):

            statistical_elevated.append(
                name
            )


        if _qualified_elevated(
            name,
            metric,
            metric_type,
        ):

            meaningful_elevated.append(
                name
            )


        if _qualified_strong(
            name,
            metric,
            metric_type,
        ):

            meaningful_strong.append(
                name
            )


    statistical_count = len(
        statistical_elevated
    )

    meaningful_count = len(
        meaningful_elevated
    )

    strong_count = len(
        meaningful_strong
    )


    # =========================================================
    # SUPPORTING DIAGNOSTICS
    # =========================================================
    #
    # SOFR-EFFR is useful confirmation but overlaps heavily
    # with SOFR-OBFR, so it remains supporting rather than
    # primary.
    #
    # Volume is also supporting only. High volume by itself
    # is not evidence of funding stress.
    # =========================================================


    sofr_effr_statistical = (
        _spread_statistically_elevated(
            stats.sofr_effr
        )
    )


    sofr_effr_meaningful = (
        sofr_effr_statistical
        and
        float(
            stats.sofr_effr.current
        ) >= 10.0
    )


    volume_unusual = (
        stats.sofr_volume.zscore_60d
        >= 1.5

        or

        stats.sofr_volume.percentile_60d
        >= 90
    )


    watch_support_count = (
        int(
            sofr_effr_statistical
        )
        +
        int(
            volume_unusual
        )
    )


    severity_support_count = (
        int(
            sofr_effr_meaningful
        )
        +
        int(
            volume_unusual
        )
    )


    # =========================================================
    # COMMON DIAGNOSTIC TEXT
    # =========================================================


    diagnostic_text = (
        f"SOFR-OBFR is "
        f"{_format_bp(stats.sofr_obfr.current)}, "
        f"SOFR-TGCR is "
        f"{_format_bp(stats.sofr_tgcr.current)}, "
        f"the SOFR interquartile range is "
        f"{float(stats.sofr_iqr.current):.1f} bp, "
        f"and the 99th-percentile premium is "
        f"{float(stats.sofr_upper_tail.current):.1f} bp."
    )


    # =========================================================
    # CRITICAL
    # =========================================================
    #
    # Critical requires several economically large,
    # statistically extreme diagnostics.
    #
    # This is intentionally difficult to reach.
    # =========================================================


    if (
        strong_count >= 3

        or

        (
            strong_count >= 2
            and
            meaningful_count >= 4
        )
    ):

        return Signal(

            category=
                "Repo Market",

            title=
                "Significant repo-market pressure",

            severity=
                "Critical",

            message=(
                f"{diagnostic_text} "
                f"{meaningful_count} of 5 primary "
                "repo diagnostics are both statistically "
                "unusual and economically meaningful, "
                f"including {strong_count} at severe "
                "levels. Broad secured-funding conditions "
                "show evidence of significant market "
                "pressure."
            ),
        )


    # =========================================================
    # WARNING
    # =========================================================
    #
    # Warning requires meaningful magnitude.
    #
    # Two severe diagnostics are sufficient.
    #
    # Otherwise we require broader confirmation.
    # =========================================================


    if (
        strong_count >= 2

        or

        meaningful_count >= 4

        or

        (
            meaningful_count >= 3
            and
            severity_support_count >= 1
        )
    ):

        return Signal(

            category=
                "Repo Market",

            title=
                "Repo-market pressure elevated",

            severity=
                "Warning",

            message=(
                f"{diagnostic_text} "
                f"{meaningful_count} of 5 primary "
                "repo diagnostics are both statistically "
                "unusual and economically meaningful, "
                f"including {strong_count} at severe "
                "levels. Pressure is confirmed across "
                "multiple secured-funding measures."
            ),
        )


    # =========================================================
    # WATCH
    # =========================================================
    #
    # Watch deliberately remains sensitive.
    #
    # Statistical abnormalities can trigger monitoring
    # even when absolute magnitude is not yet large enough
    # for Warning.
    # =========================================================


    if (
        statistical_count >= 2

        or

        (
            statistical_count >= 1
            and
            watch_support_count >= 1
        )
    ):

        return Signal(

            category=
                "Repo Market",

            title=
                "Repo internals warrant monitoring",

            severity=
                "Watch",

            message=(
                f"{diagnostic_text} "
                f"{statistical_count} of 5 primary "
                "repo diagnostics are unusual relative "
                "to recent history, but only "
                f"{meaningful_count} currently exceed "
                "the economic magnitude thresholds "
                "required for a higher-severity signal."
            ),
        )


    # =========================================================
    # ISOLATED ABNORMALITY
    # =========================================================


    if statistical_count == 1:

        return Signal(

            category=
                "Repo Market",

            title=
                "Isolated repo-market divergence",

            severity=
                "Normal",

            message=(
                f"{diagnostic_text} "
                "One repo diagnostic is statistically "
                "unusual, but the broader secured-funding "
                "market does not confirm meaningful "
                "market-wide pressure."
            ),
        )


    # =========================================================
    # NORMAL
    # =========================================================


    return Signal(

        category=
            "Repo Market",

        title=
            "Repo-market internals orderly",

        severity=
            "Normal",

        message=(
            f"{diagnostic_text} "
            "Secured-funding spreads, transaction "
            "dispersion, and upper-tail pricing do not "
            "show broad evidence of repo-market pressure."
        ),
    )


# =============================================================
# LIVE / HISTORICAL WRAPPER
# =============================================================


def evaluate_repo_market_signal(
    as_of_date: date | None = None,
) -> Signal:

    stats = (
        repo_market_statistics(
            lookback=60,
            as_of_date=
                as_of_date,
        )
    )


    return (
        evaluate_repo_market_statistics(
            stats
        )
    )


# =============================================================
# TERMINAL TEST
# =============================================================


if __name__ == "__main__":

    signal = (
        evaluate_repo_market_signal()
    )


    print()
    print(
        "Liquidity Monitor — "
        "Repo Market Signal"
    )

    print("=" * 72)

    print()

    print(
        f"Severity: "
        f"{signal.severity}"
    )

    print(
        f"Title:    "
        f"{signal.title}"
    )

    print()

    print(
        signal.message
    )