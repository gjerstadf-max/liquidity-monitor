from backend.metrics.system_liquidity import (
    system_liquidity_history_metrics,
    system_liquidity_metrics,
)
from backend.signals.models import Signal


def evaluate_system_liquidity_signal() -> Signal:
    """
    Evaluate the preliminary system-liquidity proxy:

        Reserve Balances
        + ON RRP
        - TGA

    The signal considers both:

    1. Current level relative to the past 52 weeks.
    2. Direction over the past 4 and 13 weeks.

    Thresholds are deterministic and intentionally
    conservative.
    """

    history = system_liquidity_history_metrics()
    current = system_liquidity_metrics()

    percentile = history.percentile_52_week
    zscore = history.zscore_52_week

    change_4w = float(
        history.four_week_change_billions
    )

    change_13w = float(
        history.thirteen_week_change_billions
    )


    # =========================================================
    # CRITICAL
    # =========================================================

    if (
        zscore <= -2.5
        and change_4w < 0
        and change_13w < 0
    ):
        return Signal(
            category="System Liquidity",
            title="System liquidity materially constrained",
            severity="Critical",
            message=(
                f"The system-liquidity proxy is at the "
                f"{percentile:.0f}th percentile of its "
                f"52-week distribution with a z-score of "
                f"{zscore:+.2f}. "
                f"The proxy declined ${abs(change_4w):,.0f}B "
                f"over four weeks and "
                f"${abs(change_13w):,.0f}B over thirteen weeks. "
                "Liquidity is both historically low and "
                "continuing to contract."
            ),
        )


    # =========================================================
    # WARNING
    # =========================================================

    if (
        (
            percentile <= 10
            or zscore <= -2.0
        )
        and change_4w < 0
    ):
        return Signal(
            category="System Liquidity",
            title="System liquidity is unusually low",
            severity="Warning",
            message=(
                f"The system-liquidity proxy is at the "
                f"{percentile:.0f}th percentile of its "
                f"52-week distribution with a z-score of "
                f"{zscore:+.2f}. "
                f"The proxy changed {change_4w:+,.0f}B "
                f"over four weeks. "
                "The current level is unusually low relative "
                "to the past year and remains under pressure."
            ),
        )


    # =========================================================
    # WATCH
    # =========================================================

    if (
        (
            percentile <= 25
            and change_4w < 0
        )
        or (
            zscore <= -1.25
            and change_4w < 0
        )
        or (
            change_4w <= -150
            and change_13w < 0
        )
    ):
        return Signal(
            category="System Liquidity",
            title="System liquidity warrants monitoring",
            severity="Watch",
            message=(
                f"The system-liquidity proxy is at the "
                f"{percentile:.0f}th percentile of its "
                f"52-week distribution with a z-score of "
                f"{zscore:+.2f}. "
                f"The proxy changed {change_4w:+,.0f}B "
                f"over four weeks and "
                f"{change_13w:+,.0f}B over thirteen weeks. "
                "Liquidity remains functional, but the recent "
                "direction and historical position warrant "
                "monitoring."
            ),
        )


    # =========================================================
    # REBUILDING / IMPROVING
    # =========================================================

    if (
        change_4w > 0
        and change_13w > 0
    ):
        return Signal(
            category="System Liquidity",
            title="System liquidity is rebuilding",
            severity="Normal",
            message=(
                f"The system-liquidity proxy is at the "
                f"{percentile:.0f}th percentile of its "
                f"52-week distribution with a z-score of "
                f"{zscore:+.2f}. "
                f"The proxy increased {change_4w:+,.0f}B "
                f"over four weeks and "
                f"{change_13w:+,.0f}B over thirteen weeks. "
                "The recent direction indicates improving "
                "system liquidity."
            ),
        )


    # =========================================================
    # NORMAL
    # =========================================================

    return Signal(
        category="System Liquidity",
        title="System liquidity remains within normal range",
        severity="Normal",
        message=(
            f"The system-liquidity proxy is at the "
            f"{percentile:.0f}th percentile of its "
            f"52-week distribution with a z-score of "
            f"{zscore:+.2f}. "
            f"The proxy changed {change_4w:+,.0f}B "
            f"over four weeks and "
            f"{change_13w:+,.0f}B over thirteen weeks. "
            "Current conditions do not indicate unusual "
            "system-liquidity pressure."
        ),
    )