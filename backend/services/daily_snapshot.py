from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from datetime import datetime, time
from zoneinfo import ZoneInfo

from typing import Any

from backend.assessments.engine import (
    build_liquidity_assessment,
)

from backend.assessments.models import (
    LiquidityAssessment,
)

from backend.commentary.interpretation_storage import (
    load_latest_liquidity_interpretation,
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
    system_liquidity_data_freshness,
)

PACIFIC = ZoneInfo(
    "America/Los_Angeles"
)

MORNING_SNAPSHOT_TIME = time(
    hour=9,
    minute=0,
)

def _morning_freshness_reference() -> datetime:
    """
    Return the canonical morning reference time used to
    evaluate data freshness for the daily liquidity snapshot.

    The application is refreshed once each morning, so
    freshness should not change merely because the webpage
    is viewed later in the day.
    """

    today = datetime.now(
        PACIFIC
    ).date()

    return datetime.combine(
        today,
        MORNING_SNAPSHOT_TIME,
        tzinfo=PACIFIC,
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

    Stored AI interpretation is presentation commentary only.
    Building a DailySnapshot never calls OpenAI.
    """

    generated_at: datetime

    assessment: LiquidityAssessment

    funding: FundingSnapshot

    spread_statistics: FundingSpreadStatistics

    system_liquidity: SystemLiquidityMetrics

    system_liquidity_history: SystemLiquidityHistoryMetrics

    morning_brief: MorningBrief

    funding_freshness: DataFreshness

    system_liquidity_freshness: DataFreshness

    liquidity_interpretation: dict[str, Any]

    market_narrative: dict[str, Any]

    market_context: dict[str, Any]


# =============================================================
# EMPTY STORED INTERPRETATION
# =============================================================


def _empty_liquidity_interpretation(
    status: str = "No stored interpretation",
) -> dict[str, Any]:
    """
    Return a predictable empty interpretation object.

    This preserves a stable interface for the API and homepage
    when no successful AI interpretation has yet been stored.
    """

    return {
        "available": False,

        "status":
            status,

        "snapshot_date":
            None,

        "generated_at":
            None,

        "overall_verdict":
            None,

        "overall_confidence":
            None,

        "headline":
            None,

        "overall_comment":
            None,

        "primary_drivers":
            [],

        "counter_evidence":
            [],

        "what_to_watch":
            [],

        "model":
            None,

        "interpreter_version":
            None,

        "fallback_used":
            False,
    }


# =============================================================
# STORED LIQUIDITY INTERPRETATION
# =============================================================


def _load_liquidity_interpretation(
) -> dict[str, Any]:
    """
    Load the newest successfully stored liquidity
    interpretation.

    This performs no external API or model call.
    """

    try:

        interpretation = (
            load_latest_liquidity_interpretation()
        )

        if interpretation is None:

            return (
                _empty_liquidity_interpretation()
            )

        return interpretation

    except Exception as exc:

        print(
            "Stored liquidity interpretation unavailable: "
            f"{exc}"
        )

        return (
            _empty_liquidity_interpretation(
                status="Database unavailable"
            )
        )


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
        4. Deterministic Morning Brief
        5. Data freshness
        6. Stored AI liquidity interpretation
        7. Stored news narrative
        8. Simplified Market Context

    Neither the stored AI interpretation nor news can influence
    quantitative metrics, signals or assessments.

    No OpenAI or external news request occurs while building
    this snapshot.
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
    # DETERMINISTIC QUALITATIVE ASSESSMENT
    # =========================================================

    assessment = (
        build_liquidity_assessment()
    )

    # =========================================================
    # DETERMINISTIC MORNING BRIEF
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

    freshness_reference = (
    _morning_freshness_reference()
)

    funding_freshness = (
        funding_data_freshness(
            funding.observation_date,
            now=freshness_reference,
        )
    )

    system_liquidity_freshness = (
        system_liquidity_data_freshness(
            system_liquidity.observation_date,
            now=freshness_reference,
        )
)

    # =========================================================
    # STORED INTELLIGENT INTERPRETATION
    # =========================================================
    #
    # IMPORTANT:
    #
    # This only reads the newest successfully stored result.
    # No OpenAI call occurs here.
    #
    # Interpretation generation belongs to daily_refresh.py.
    # =========================================================

    liquidity_interpretation = (
        _load_liquidity_interpretation()
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

        liquidity_interpretation=
            liquidity_interpretation,

        market_narrative=
            market_narrative,

        market_context=
            market_context,

        system_liquidity_freshness=
            system_liquidity_freshness,
    )