from __future__ import annotations

from dataclasses import dataclass
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
from backend.news.storage import (
    load_latest_market_narrative,
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
    status: str = "No stored snapshot",
) -> dict[str, Any]:

    return {
        "available": False,

        "status": status,

        "market_attention":
            "Unavailable",

        "directional_confirmation":
            "Unavailable",

        "summary": (
            "No stored market-news snapshot "
            "is currently available."
        ),

        "stories": [],
    }


def _load_news_overlay(
) -> dict[str, Any]:
    """
    Load the latest stored news assessment.

    This function deliberately makes no external
    network calls. News collection happens only
    inside the scheduled news-refresh job.
    """

    try:

        narrative = (
            load_latest_market_narrative()
        )


        if narrative is None:

            return (
                _empty_news_overlay()
            )


        return narrative


    except Exception as exc:

        print(
            "Stored news overlay unavailable: "
            f"{exc}"
        )


        return _empty_news_overlay(
            status="Database unavailable"
        )


# =============================================================
# SNAPSHOT BUILDER
# =============================================================


def build_daily_snapshot(
    include_news: bool = False,
) -> DailySnapshot:

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
    # STORED MARKET NEWS
    # ---------------------------------------------------------

    if include_news:

        market_narrative = (
            _load_news_overlay()
        )

    else:

        market_narrative = (
            _empty_news_overlay(
                status="Not requested"
            )
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