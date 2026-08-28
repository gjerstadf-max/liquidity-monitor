from __future__ import annotations

from datetime import date

from backend.metrics.commercial_paper import (
    CommercialPaperStatistics,
    commercial_paper_statistics,
)
from backend.signals.models import Signal


# =============================================================
# THRESHOLDS
# =============================================================

WATCH_SPREAD_BP = 75.0
WARNING_SPREAD_BP = 100.0
CRITICAL_SPREAD_BP = 200.0

STATISTICAL_WATCH_FLOOR_BP = 50.0
STATISTICAL_WATCH_Z = 1.50
STATISTICAL_WATCH_PERCENTILE = 90.0


# =============================================================
# CORE SIGNAL LOGIC
# =============================================================


def evaluate_commercial_paper_statistics(
    stats: CommercialPaperStatistics,
) -> Signal:
    """
    Commercial Paper Funding signal.

    The primary diagnostic is the spread between:

        30-day A2/P2 nonfinancial CP
        and
        30-day AA nonfinancial CP.

    Warning and Critical require economically meaningful
    absolute spread levels.

    Watch can also occur below 75 bp when the spread is at
    least 50 bp and unusually elevated relative to its
    recent 60-day history.
    """

    spread = float(
        stats.current_spread_bp
    )

    statistical_watch = (
        spread >= STATISTICAL_WATCH_FLOOR_BP
        and (
            stats.zscore_60d >= STATISTICAL_WATCH_Z
            or
            stats.percentile_60d
            >= STATISTICAL_WATCH_PERCENTILE
        )
    )

    diagnostic_text = (
        f"The 30-day A2/P2 minus AA nonfinancial "
        f"commercial-paper spread is {spread:.1f} bp, "
        f"versus a 20-day average of "
        f"{float(stats.average_20d_bp):.1f} bp and a "
        f"60-day average of "
        f"{float(stats.average_60d_bp):.1f} bp."
    )

    # =========================================================
    # CRITICAL
    # =========================================================

    if spread >= CRITICAL_SPREAD_BP:

        return Signal(
            category=
                "Commercial Paper",

            title=
                "Commercial-paper funding severely stressed",

            severity=
                "Critical",

            message=(
                f"{diagnostic_text} "
                "The lower-quality commercial-paper premium "
                "is at a crisis-level magnitude, indicating "
                "severe stress in unsecured short-term "
                "corporate funding."
            ),
        )

    # =========================================================
    # WARNING
    # =========================================================

    if spread >= WARNING_SPREAD_BP:

        return Signal(
            category=
                "Commercial Paper",

            title=
                "Commercial-paper funding pressure elevated",

            severity=
                "Warning",

            message=(
                f"{diagnostic_text} "
                "The lower-quality commercial-paper premium "
                "is economically large and indicates "
                "meaningful stress in unsecured short-term "
                "corporate funding."
            ),
        )

    # =========================================================
    # WATCH
    # =========================================================

    if (
        spread >= WATCH_SPREAD_BP
        or statistical_watch
    ):

        return Signal(
            category=
                "Commercial Paper",

            title=
                "Commercial-paper funding warrants monitoring",

            severity=
                "Watch",

            message=(
                f"{diagnostic_text} "
                "The lower-quality commercial-paper premium "
                "is elevated enough to warrant monitoring, "
                "but remains below levels historically "
                "associated with more severe funding stress."
            ),
        )

    # =========================================================
    # NORMAL
    # =========================================================

    return Signal(
        category=
            "Commercial Paper",

        title=
            "Commercial-paper funding orderly",

        severity=
            "Normal",

        message=(
            f"{diagnostic_text} "
            "The lower-quality commercial-paper premium "
            "does not indicate unusual stress in unsecured "
            "short-term corporate funding."
        ),
    )


# =============================================================
# LIVE / HISTORICAL WRAPPER
# =============================================================


def evaluate_commercial_paper_signal(
    as_of_date: date | None = None,
) -> Signal:

    stats = (
        commercial_paper_statistics(
            lookback=60,
            as_of_date=
                as_of_date,
        )
    )

    return (
        evaluate_commercial_paper_statistics(
            stats
        )
    )


# =============================================================
# TERMINAL TEST
# =============================================================


if __name__ == "__main__":

    signal = (
        evaluate_commercial_paper_signal()
    )

    print()

    print(
        "Liquidity Monitor — "
        "Commercial Paper Signal"
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