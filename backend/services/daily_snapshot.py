from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any

from backend.assessments.engine import (
    build_liquidity_assessment,
)
from backend.assessments.models import (
    LiquidityAssessment,
)
from backend.commentary.morning_brief import (
    MorningBrief,
    generate_morning_brief,
)
from backend.metrics.funding import (
    FundingSnapshot,
    FundingSpreadStatistics,
    funding_spread_statistics,
    latest_funding_snapshot,
)
from backend.metrics.system_liquidity import (
    SystemLiquidityHistoryMetrics,
    SystemLiquidityMetrics,
    system_liquidity_history_metrics,
    system_liquidity_metrics,
)
from backend.news.narrative import (
    build_market_narrative,
)
from backend.services.freshness import (
    DataFreshness,
    funding_data_freshness,
)


# =============================================================
# DAILY SNAPSHOT
# =============================================================


@dataclass(frozen=True)
class DailySnapshot:
    generated_at: datetime

    assessment: LiquidityAssessment

    funding: FundingSnapshot

    spread_statistics: FundingSpreadStatistics

    system_liquidity: SystemLiquidityMetrics

    system_liquidity_history: SystemLiquidityHistoryMetrics

    morning_brief: MorningBrief

    funding_freshness: DataFreshness

    market_narrative: dict[str, Any]


# =============================================================
# NEWS OVERLAY
# =============================================================


def _empty_news_overlay(
    status: str = "Not requested",
) -> dict[str, Any]:
    """
    Return a predictable empty news-overlay structure.

    The core liquidity snapshot must remain available
    regardless of whether the external news feed is
    requested or available.
    """

    return {
        "available": False,
        "status": status,
        "market_attention": "Unavailable",
        "directional_confirmation": "Unavailable",
        "summary": (
            "Market-news overlay is not available "
            "for this snapshot."
        ),
        "stories": [],
    }


def _build_news_overlay() -> dict[str, Any]:
    """
    Build the market-news overlay.

    News is intentionally treated as a secondary
    contextual layer. Failure of the external news
    source must never break the quantitative
    Liquidity Monitor snapshot.
    """

    try:
        narrative = build_market_narrative(
            final_limit=6
        )

        return {
            "available": True,
            "status": "Available",
            **asdict(narrative),
        }

    except Exception as exc:
        print(
            "News overlay unavailable: "
            f"{exc}"
        )

        return _empty_news_overlay(
            status="Feed unavailable"
        )


# =============================================================
# SNAPSHOT BUILDER
# =============================================================


def build_daily_snapshot(
    include_news: bool = False,
) -> DailySnapshot:
    """
    Build the canonical Liquidity Monitor snapshot.

    This object is shared by the frontend and API.

    News is optional because it depends on an external
    source. The quantitative liquidity system remains
    fully operational if the news feed is unavailable.
    """

    # ---------------------------------------------------------
    # FUNDING
    # ---------------------------------------------------------

    funding = (
        latest_funding_snapshot()
    )

    spread_statistics = (
        funding_spread_statistics()
    )


    # ---------------------------------------------------------
    # SYSTEM LIQUIDITY
    # ---------------------------------------------------------

    system_liquidity = (
        system_liquidity_metrics()
    )

    system_liquidity_history = (
        system_liquidity_history_metrics()
    )


    # ---------------------------------------------------------
    # ASSESSMENT
    # ---------------------------------------------------------

    assessment = (
        build_liquidity_assessment()
    )


    # ---------------------------------------------------------
    # MORNING BRIEF
    # ---------------------------------------------------------

    morning_brief = (
        generate_morning_brief(
            assessment=assessment
        )
    )


    # ---------------------------------------------------------
    # DATA FRESHNESS
    # ---------------------------------------------------------

    funding_freshness = (
        funding_data_freshness(
            funding.observation_date
        )
    )


    # ---------------------------------------------------------
    # MARKET NEWS OVERLAY
    # ---------------------------------------------------------

    if include_news:
        market_narrative = (
            _build_news_overlay()
        )

    else:
        market_narrative = (
            _empty_news_overlay()
        )


    # ---------------------------------------------------------
    # FINAL SNAPSHOT
    # ---------------------------------------------------------

    return DailySnapshot(
        generated_at=
            datetime.now(timezone.utc),

        assessment=
            assessment,

        funding=
            funding,

        spread_statistics=
            spread_statistics,

        system_liquidity=
            system_liquidity,

        system_liquidity_history=
            system_liquidity_history,

        morning_brief=
            morning_brief,

        funding_freshness=
            funding_freshness,

        market_narrative=
            market_narrative,
    )