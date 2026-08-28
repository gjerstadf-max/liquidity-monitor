from __future__ import annotations

from datetime import date

from backend.metrics.global_dollar_funding import (
    GlobalDollarFundingStatistics,
    global_dollar_funding_statistics,
)
from backend.signals.models import Signal


# =============================================================
# THRESHOLDS
# =============================================================

SWAP_WATCH_BILLIONS = 10.0
SWAP_WARNING_BILLIONS = 50.0
SWAP_CRITICAL_BILLIONS = 250.0

FIMA_WATCH_BILLIONS = 5.0
FIMA_STRONG_BILLIONS = 25.0


# =============================================================
# CORE SIGNAL
# =============================================================


def evaluate_global_dollar_funding_statistics(
    stats: GlobalDollarFundingStatistics,
) -> Signal:
    """
    Global Dollar Funding Stress signal.

    Central-bank dollar liquidity swaps are the core
    systemic offshore-dollar funding diagnostic.

    FIMA repo usage is supporting only. It can create
    a Watch when unusually large, but cannot by itself
    create Warning or Critical.
    """

    swaps = float(
        stats.swap_usage_billions
    )

    fima = float(
        stats.fima_repo_billions
    )

    # =========================================================
    # SUPPORTING FIMA DIAGNOSTIC
    # =========================================================

    fima_watch = (
        fima >= FIMA_WATCH_BILLIONS
    )

    fima_strong = (
        fima >= FIMA_STRONG_BILLIONS
    )

    diagnostic_text = (
        f"Federal Reserve central-bank dollar liquidity "
        f"swaps are ${swaps:,.1f}B, while FIMA repo "
        f"usage is ${fima:,.1f}B."
    )

    # =========================================================
    # CRITICAL
    # =========================================================

    if swaps >= SWAP_CRITICAL_BILLIONS:

        return Signal(
            category=
                "Global Dollar Funding",

            title=
                "Global dollar funding severely stressed",

            severity=
                "Critical",

            message=(
                f"{diagnostic_text} "
                "Central-bank swap usage is at a crisis-level "
                "magnitude, indicating severe demand for "
                "Federal Reserve dollar liquidity outside "
                "the domestic banking system."
            ),
        )

    # =========================================================
    # WARNING
    # =========================================================

    if swaps >= SWAP_WARNING_BILLIONS:

        return Signal(
            category=
                "Global Dollar Funding",

            title=
                "Global dollar funding pressure elevated",

            severity=
                "Warning",

            message=(
                f"{diagnostic_text} "
                "Central-bank swap usage is economically "
                "large and indicates meaningful offshore "
                "dollar-funding pressure."
            ),
        )

    # =========================================================
    # WATCH
    # =========================================================

    if (
        swaps >= SWAP_WATCH_BILLIONS
        or fima_watch
    ):

        if fima_strong and swaps < SWAP_WATCH_BILLIONS:

            message = (
                f"{diagnostic_text} "
                "Swap-line usage remains limited, but FIMA "
                "repo usage is unusually large and warrants "
                "monitoring of foreign-official dollar "
                "liquidity demand."
            )

        else:

            message = (
                f"{diagnostic_text} "
                "Dollar-liquidity backstop usage is elevated "
                "enough to warrant monitoring, but remains "
                "below levels historically associated with "
                "severe global dollar-funding stress."
            )

        return Signal(
            category=
                "Global Dollar Funding",

            title=
                "Global dollar funding warrants monitoring",

            severity=
                "Watch",

            message=
                message,
        )

    # =========================================================
    # NORMAL
    # =========================================================

    return Signal(
        category=
            "Global Dollar Funding",

        title=
            "Global dollar funding orderly",

        severity=
            "Normal",

        message=(
            f"{diagnostic_text} "
            "Federal Reserve dollar-liquidity backstop usage "
            "does not indicate unusual global dollar-funding "
            "stress."
        ),
    )


# =============================================================
# LIVE / HISTORICAL WRAPPER
# =============================================================


def evaluate_global_dollar_funding_signal(
    as_of_date: date | None = None,
) -> Signal:

    stats = (
        global_dollar_funding_statistics(
            as_of_date=
                as_of_date,
        )
    )

    return (
        evaluate_global_dollar_funding_statistics(
            stats
        )
    )


# =============================================================
# TERMINAL TEST
# =============================================================


if __name__ == "__main__":

    signal = (
        evaluate_global_dollar_funding_signal()
    )

    print()

    print(
        "Liquidity Monitor — "
        "Global Dollar Funding Signal"
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