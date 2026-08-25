from __future__ import annotations

from decimal import Decimal

from backend.metrics.funding import (
    funding_spread_statistics,
    latest_funding_snapshot,
)
from backend.metrics.repo_market import (
    repo_market_statistics,
)
from backend.metrics.system_liquidity import (
    system_liquidity_history_metrics,
    system_liquidity_metrics,
)
from backend.metrics.treasury_intermediation import (
    treasury_intermediation_statistics,
)


# =============================================================
# FORMATTING
# =============================================================


def _format_billions(
    value: Decimal | float,
    decimals: int = 0,
) -> str:
    numeric = float(
        value
    )

    if numeric < 0:
        return (
            f"-${abs(numeric):,.{decimals}f}B"
        )

    return (
        f"${numeric:,.{decimals}f}B"
    )


def _format_bp(
    value: Decimal | float,
    decimals: int = 0,
) -> str:
    return (
        f"{float(value):+,.{decimals}f} bp"
    )


def _format_sigma(
    value: float,
) -> str:
    return (
        f"{value:+.2f}σ"
    )


# =============================================================
# FUNDING
# =============================================================


def funding_what_matters() -> str:
    snapshot = (
        latest_funding_snapshot()
    )

    stats = (
        funding_spread_statistics()
    )

    return (
        "Funding conditions: "
        f"SOFR is {float(snapshot.sofr):.2f}% "
        f"versus EFFR at {float(snapshot.effr):.2f}%, "
        f"leaving the SOFR-EFFR spread at "
        f"{_format_bp(stats.current_spread_bp)}. "
        f"The spread is at approximately the "
        f"{stats.percentile_60d:.0f}th percentile of its "
        f"recent distribution with a z-score of "
        f"{_format_sigma(stats.zscore_60d)}."
    )


def funding_watch(
    verdict: str,
) -> str:
    if verdict == "Normal":
        return (
            "Funding: overnight secured and unsecured rates "
            "remain well aligned. Watch for a persistent "
            "widening in SOFR relative to EFFR or other "
            "unsecured reference rates."
        )

    if verdict == "Watch":
        return (
            "Funding: conditions are less comfortable than "
            "normal. Watch whether recent spread pressure "
            "persists or begins appearing across multiple "
            "overnight funding benchmarks."
        )

    if verdict == "Elevated":
        return (
            "Funding: pricing pressure is materially elevated. "
            "Watch for persistence, broader secured/unsecured "
            "divergence, and evidence that funding pressure is "
            "spreading across venues."
        )

    return (
        "Funding: conditions are stressed. Watch the scale "
        "and persistence of rate dislocations and any signs "
        "that funding availability is becoming impaired."
    )


# =============================================================
# SYSTEM LIQUIDITY
# =============================================================


def system_liquidity_what_matters() -> str:
    current = (
        system_liquidity_metrics()
    )

    history = (
        system_liquidity_history_metrics()
    )

    return (
        "System liquidity: "
        f"the monitoring proxy "
        f"(reserve balances + ON RRP − TGA) stands at "
        f"{_format_billions(current.net_liquidity_proxy_billions)}. "
        f"It has changed "
        f"{_format_billions(history.four_week_change_billions)} "
        f"over four weeks and "
        f"{_format_billions(history.thirteen_week_change_billions)} "
        f"over thirteen weeks. "
        f"The current level is near the "
        f"{history.percentile_52_week:.0f}th percentile "
        f"of the trailing 52-week range."
    )


def system_liquidity_watch(
    verdict: str,
) -> str:
    metrics = (
        system_liquidity_metrics()
    )

    history = (
        system_liquidity_history_metrics()
    )

    contribution_text = (
        f"Reserve balances are "
        f"{_format_billions(metrics.reserve_balances_billions)}, "
        f"ON RRP is "
        f"{_format_billions(metrics.on_rrp_billions)}, "
        f"and the TGA is "
        f"{_format_billions(metrics.tga_billions)}."
    )

    if verdict == "Normal":
        return (
            "System liquidity: aggregate liquidity remains "
            "comfortable. "
            f"{contribution_text}"
        )

    if verdict == "Watch":
        return (
            "System liquidity: the liquidity buffer is "
            "becoming less comfortable. Watch whether reserve "
            "balances continue to decline, ON RRP remains "
            "largely exhausted, or TGA accumulation removes "
            "additional liquidity from the banking system. "
            f"{contribution_text} "
            f"The four-week change in the proxy is "
            f"{_format_billions(history.four_week_change_billions)}."
        )

    if verdict == "Elevated":
        return (
            "System liquidity: aggregate liquidity is under "
            "meaningful pressure. Watch the pace of reserve "
            "decline and whether Treasury cash accumulation "
            "continues to drain liquidity. "
            f"{contribution_text}"
        )

    return (
        "System liquidity: the available liquidity buffer is "
        "materially stressed. Reserve balances, Treasury cash "
        "flows and remaining ON RRP capacity require close "
        "monitoring. "
        f"{contribution_text}"
    )


# =============================================================
# REPO MARKET
# =============================================================


def repo_what_matters() -> str:
    stats = (
        repo_market_statistics(
            lookback=60
        )
    )

    return (
        "Repo market pressure: "
        f"SOFR-OBFR is "
        f"{_format_bp(stats.sofr_obfr.current)}, "
        f"SOFR-TGCR is "
        f"{_format_bp(stats.sofr_tgcr.current)}, "
        f"and SOFR-BGCR is "
        f"{_format_bp(stats.sofr_bgcr.current)}. "
        f"The SOFR interquartile range is "
        f"{_format_bp(stats.sofr_iqr.current)} "
        f"and the upper tail is "
        f"{_format_bp(stats.sofr_upper_tail.current)}."
    )


def repo_watch(
    verdict: str,
) -> str:
    if verdict == "Normal":
        return (
            "Repo market: secured funding remains orderly. "
            "Watch for widening differences between SOFR, "
            "TGCR and BGCR, or a sharp increase in SOFR "
            "dispersion and upper-tail pricing."
        )

    if verdict == "Watch":
        return (
            "Repo market: one or more repo diagnostics are "
            "unusually elevated, but evidence of broader "
            "dysfunction remains limited. Watch for "
            "confirmation across multiple repo measures."
        )

    if verdict == "Elevated":
        return (
            "Repo market: pressure is elevated across multiple "
            "secured-funding diagnostics. Watch whether "
            "dispersion, venue differences and upper-tail "
            "pricing continue to worsen."
        )

    return (
        "Repo market: secured funding is showing broad "
        "dysfunction. Watch the persistence of pricing "
        "dislocations and whether pressure spreads further "
        "across Treasury financing channels."
    )


# =============================================================
# TREASURY INTERMEDIATION
# =============================================================


def treasury_intermediation_what_matters() -> str:
    stats = (
        treasury_intermediation_statistics()
    )

    return (
        "Treasury intermediation: "
        f"dealer Treasury positions are "
        f"{_format_billions(stats.dealer_positions.current, 1)}, "
        f"weekly Treasury transaction activity is "
        f"{_format_billions(stats.treasury_transactions.current, 1)}, "
        f"and Treasury securities borrowed are "
        f"{_format_billions(stats.securities_borrowed.current, 1)}. "
        f"Total Treasury settlement fails are "
        f"{_format_billions(stats.total_fails.current, 1)}, "
        f"with a trailing 52-week z-score of "
        f"{_format_sigma(stats.total_fails.zscore_52_week)}."
    )


def treasury_intermediation_watch(
    verdict: str,
) -> str:
    if verdict == "Normal":
        return (
            "Treasury intermediation: dealer balance-sheet "
            "adjustment, intermediation demand and settlement "
            "friction remain orderly. Watch for unusual "
            "movement across more than one of these dimensions "
            "at the same time."
        )

    if verdict == "Watch":
        return (
            "Treasury intermediation: one dimension is "
            "unusually elevated, but the other dealer-market "
            "indicators do not confirm broad pressure. Watch "
            "for convergence across balance-sheet adjustment, "
            "trading/borrowing demand and settlement fails."
        )

    if verdict == "Elevated":
        return (
            "Treasury intermediation: pressure is evident "
            "across multiple dealer-market dimensions. Watch "
            "whether settlement friction intensifies and "
            "whether abnormal dealer balance-sheet adjustment "
            "and intermediation demand persist together."
        )

    return (
        "Treasury intermediation: dealer balance-sheet "
        "adjustment, intermediation demand and settlement "
        "friction are showing broad stress. Watch whether "
        "market functioning begins to normalize or whether "
        "the disruption persists across multiple weeks."
    )