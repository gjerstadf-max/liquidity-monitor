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
from backend.news.context import (
    build_market_context,
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
    """
    Complete application snapshot used by the API
    and homepage.

    Business logic remains in the underlying metrics,
    signals, assessments and commentary modules.
    """

    generated_at: datetime

    assessment: LiquidityAssessment

    funding: FundingSnapshot
    spread_statistics: FundingSpreadStatistics

    system_liquidity: SystemLiquidityMetrics
    system_liquidity_history: SystemLiquidityHistoryMetrics

    morning_brief: MorningBrief

    funding_freshness: DataFreshness

    market_narrative: dict[str, Any]
    market_context: dict[str, Any]


# =============================================================
# EMPTY STORED NEWS STATE
# =============================================================


def _empty_news_overlay(
    status: str = "No stored snapshot",
) -> dict[str, Any]:
    """
    Return a predictable empty news object.

    This preserves the existing market_narrative interface
    used by the API while allowing the simplified homepage
    Market Context to remain independent of the old visual
    news overlay.
    """

    return {
        "available": False,

        "status":
            status,

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


# =============================================================
# STORED NEWS
# =============================================================


def _load_news_overlay(
) -> dict[str, Any]:
    """
    Load the latest stored market-news narrative.

    No network request occurs here.

    External news collection remains the responsibility
    of the scheduled news-refresh process.
    """

    try:

        narrative = (
            load_latest_market_narrative()
        )

        if narrative is None:

            return _empty_news_overlay()

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
    """
    Build the complete Liquidity Monitor snapshot.

    Sequence:

        1. Funding metrics
        2. System-liquidity metrics
        3. Registered-factor liquidity assessment
        4. Morning Brief
        5. Data freshness
        6. Stored news narrative
        7. Simplified Market Context

    News remains contextual only and does not influence
    quantitative metrics, signals or assessments.
    """

    # =========================================================
    # FUNDING
    # =========================================================

    funding = (
        latest_funding_snapshot()
    )

    spread_statistics = (
        funding_spread_statistics()
    )


    # =========================================================
    # SYSTEM LIQUIDITY
    # =========================================================

    system_liquidity = (
        system_liquidity_metrics()
    )

    system_liquidity_history = (
        system_liquidity_history_metrics()
    )


    # =========================================================
    # QUALITATIVE ASSESSMENT
    # =========================================================
    #
    # The assessment engine now contains:
    #
    #   1. Funding Conditions
    #   2. System Liquidity
    #   3. Repo Market Pressure
    #   4. Treasury Intermediation
    #   5. Treasury Market Activity
    #
    # No composite numeric score is used.
    # =========================================================

    assessment = (
        build_liquidity_assessment()
    )


    # =========================================================
    # MORNING BRIEF
    # =========================================================
    #
    # Reuse the assessment we just calculated rather than
    # rebuilding it inside the commentary layer.
    # =========================================================

    morning_brief = (
        generate_morning_brief(
            assessment=
                assessment
        )
    )


    # =========================================================
    # DATA FRESHNESS
    # =========================================================

    funding_freshness = (
        funding_data_freshness(
            funding.observation_date
        )
    )


    # =========================================================
    # STORED MARKET NEWS
    # =========================================================
    #
    # The application does not fetch external news here.
    #
    # include_news=True simply means:
    #
    #   Load the most recent narrative already stored
    #   by the scheduled news-refresh process.
    # =========================================================

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


    # =========================================================
    # SIMPLIFIED MARKET CONTEXT
    # =========================================================
    #
    # The detailed narrative remains available to the API,
    # but the homepage receives only the deliberately small
    # Market Context representation.
    # =========================================================

    market_context = (
        build_market_context(
            market_narrative
        )
    )


    # =========================================================
    # FINAL SNAPSHOT
    # =========================================================

    return DailySnapshot(
        generated_at=
            datetime.now(
                timezone.utc
            ),

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

        market_context=
            market_context,
    )