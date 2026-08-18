from dataclasses import dataclass
from datetime import datetime, timezone

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
from backend.services.freshness import (
    DataFreshness,
    funding_data_freshness,
)


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
    

def build_daily_snapshot() -> DailySnapshot:
    """
    Build the canonical Liquidity Monitor snapshot.

    This object is shared by the frontend and API.
    """

    funding = (
        latest_funding_snapshot()
    )

    spread_statistics = (
        funding_spread_statistics()
    )

    system_liquidity = (
        system_liquidity_metrics()
    )

    system_liquidity_history = (
        system_liquidity_history_metrics()
    )

    assessment = (
        build_liquidity_assessment()
    )

    morning_brief = (
        generate_morning_brief(
            assessment=assessment
        )
    )

    funding_freshness = (
        funding_data_freshness(
            funding.observation_date
        )
    )

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
    )
