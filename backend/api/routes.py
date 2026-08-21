from fastapi import APIRouter, Query

from backend.services.daily_snapshot import (
    build_daily_snapshot,
)
from backend.services.funding_history import (
    get_funding_history,
)


router = APIRouter(
    prefix="/api",
    tags=["Liquidity Monitor"],
)


# =============================================================
# DAILY SNAPSHOT
# =============================================================


@router.get("/snapshot")
def get_snapshot():

    snapshot = build_daily_snapshot(
        include_news=True
    )

    system_assessment = (
        snapshot.assessment.system_liquidity
    )

    if system_assessment is None:
        raise RuntimeError(
            "System Liquidity assessment is missing."
        )

    return {
        # -----------------------------------------------------
        # GENERATED
        # -----------------------------------------------------

        "generated_at":
            snapshot.generated_at.isoformat(),

        # -----------------------------------------------------
        # QUALITATIVE ASSESSMENT
        # -----------------------------------------------------

        "assessment": {
            "overall_verdict":
                snapshot.assessment.overall_verdict,

            "confidence":
                snapshot.assessment.confidence,

            "summary":
                snapshot.assessment.summary,

            # -------------------------------------------------
            # FUNDING
            # -------------------------------------------------

            "funding": {
                "verdict":
                    snapshot.assessment
                    .funding
                    .verdict,

                "confidence":
                    snapshot.assessment
                    .funding
                    .confidence,

                "summary":
                    snapshot.assessment
                    .funding
                    .summary,
            },

            # -------------------------------------------------
            # SYSTEM LIQUIDITY
            # -------------------------------------------------

            "system_liquidity": {
                "verdict":
                    snapshot.assessment
                    .system_liquidity
                    .verdict,

                "confidence":
                    snapshot.assessment
                    .system_liquidity
                    .confidence,

                "summary":
                    snapshot.assessment
                    .system_liquidity
                    .summary,
            },

            # -------------------------------------------------
            # REPO MARKET PRESSURE
            # -------------------------------------------------

            "repo_market": {
                "verdict":
                    snapshot.assessment
                    .repo_market
                    .verdict,

                "confidence":
                    snapshot.assessment
                    .repo_market
                    .confidence,

                "summary":
                    snapshot.assessment
                    .repo_market
                    .summary,
            },

            # -------------------------------------------------
            # TREASURY INTERMEDIATION
            # -------------------------------------------------

            "treasury_intermediation": {
                "verdict":
                    snapshot.assessment
                    .treasury_intermediation
                    .verdict,

                "confidence":
                    snapshot.assessment
                    .treasury_intermediation
                    .confidence,

                "summary":
                    snapshot.assessment
                    .treasury_intermediation
                    .summary,
            },
        },

        # -----------------------------------------------------
        # FUNDING SNAPSHOT
        # -----------------------------------------------------

        "funding": {
            "observation_date":
                snapshot.funding
                .observation_date
                .isoformat(),

            "previous_observation_date":
                snapshot.funding
                .previous_observation_date
                .isoformat(),

            "sofr":
                float(
                    snapshot.funding.sofr
                ),

            "previous_sofr":
                float(
                    snapshot.funding.previous_sofr
                ),

            "sofr_change_bp":
                float(
                    snapshot.funding.sofr_change_bp
                ),

            "effr":
                float(
                    snapshot.funding.effr
                ),

            "previous_effr":
                float(
                    snapshot.funding.previous_effr
                ),

            "effr_change_bp":
                float(
                    snapshot.funding.effr_change_bp
                ),

            "spread_basis_points":
                float(
                    snapshot.funding
                    .spread_basis_points
                ),

            "previous_spread_basis_points":
                float(
                    snapshot.funding
                    .previous_spread_basis_points
                ),

            "spread_change_bp":
                float(
                    snapshot.funding
                    .spread_change_bp
                ),
        },

        # -----------------------------------------------------
        # FUNDING HISTORICAL STATISTICS
        # -----------------------------------------------------

        "spread_statistics": {
            "observations_used":
                snapshot.spread_statistics
                .observations_used,

            "current_spread_bp":
                float(
                    snapshot.spread_statistics
                    .current_spread_bp
                ),

            "average_30d_bp":
                float(
                    snapshot.spread_statistics
                    .average_30d_bp
                ),

            "average_60d_bp":
                float(
                    snapshot.spread_statistics
                    .average_60d_bp
                ),

            "minimum_60d_bp":
                float(
                    snapshot.spread_statistics
                    .minimum_60d_bp
                ),

            "maximum_60d_bp":
                float(
                    snapshot.spread_statistics
                    .maximum_60d_bp
                ),

            "percentile_60d":
                snapshot.spread_statistics
                .percentile_60d,

            "zscore_60d":
                snapshot.spread_statistics
                .zscore_60d,
        },

        # -----------------------------------------------------
        # SYSTEM LIQUIDITY SNAPSHOT
        # -----------------------------------------------------

        "system_liquidity": {
            "observation_date":
                snapshot.system_liquidity
                .observation_date
                .isoformat(),

            "reserve_balances_billions":
                float(
                    snapshot.system_liquidity
                    .reserve_balances_billions
                ),

            "on_rrp_billions":
                float(
                    snapshot.system_liquidity
                    .on_rrp_billions
                ),

            "tga_billions":
                float(
                    snapshot.system_liquidity
                    .tga_billions
                ),

            "net_liquidity_proxy_billions":
                float(
                    snapshot.system_liquidity
                    .net_liquidity_proxy_billions
                ),

            "weekly_change_billions":
                float(
                    snapshot.system_liquidity
                    .weekly_change_billions
                ),

            "four_week_change_billions":
                float(
                    snapshot.system_liquidity
                    .four_week_change_billions
                ),

            "reserve_4_week_contribution_billions":
                float(
                    snapshot.system_liquidity
                    .reserve_4_week_contribution_billions
                ),

            "rrp_4_week_contribution_billions":
                float(
                    snapshot.system_liquidity
                    .rrp_4_week_contribution_billions
                ),

            "tga_4_week_contribution_billions":
                float(
                    snapshot.system_liquidity
                    .tga_4_week_contribution_billions
                ),
        },

        # -----------------------------------------------------
        # SYSTEM LIQUIDITY HISTORY
        # -----------------------------------------------------

        "system_liquidity_history": {
            "observations_used":
                snapshot.system_liquidity_history
                .observations_used,

            "current_proxy_billions":
                float(
                    snapshot.system_liquidity_history
                    .current_proxy_billions
                ),

            "four_week_change_billions":
                float(
                    snapshot.system_liquidity_history
                    .four_week_change_billions
                ),

            "thirteen_week_change_billions":
                float(
                    snapshot.system_liquidity_history
                    .thirteen_week_change_billions
                ),

            "average_13_week_billions":
                float(
                    snapshot.system_liquidity_history
                    .average_13_week_billions
                ),

            "average_52_week_billions":
                float(
                    snapshot.system_liquidity_history
                    .average_52_week_billions
                ),

            "minimum_52_week_billions":
                float(
                    snapshot.system_liquidity_history
                    .minimum_52_week_billions
                ),

            "maximum_52_week_billions":
                float(
                    snapshot.system_liquidity_history
                    .maximum_52_week_billions
                ),

            "percentile_52_week":
                snapshot.system_liquidity_history
                .percentile_52_week,

            "zscore_52_week":
                snapshot.system_liquidity_history
                .zscore_52_week,
        },

        # -----------------------------------------------------
        # MORNING BRIEF
        # -----------------------------------------------------

        "morning_brief": {
            "headline":
                snapshot.morning_brief.headline,

            "summary":
                snapshot.morning_brief.summary,

            "what_matters":
                snapshot.morning_brief.what_matters,

            "what_to_watch":
                snapshot.morning_brief.what_to_watch,
        },

        # -----------------------------------------------------
        # MARKET NEWS / NARRATIVE
        # -----------------------------------------------------

        "market_narrative":
            snapshot.market_narrative,
    }


# =============================================================
# FUNDING HISTORY
# =============================================================


@router.get("/funding/history")
def funding_history(
    observations: int = Query(
        default=60,
        ge=2,
        le=500,
    )
):

    history = get_funding_history(
        observation_count=observations
    )

    return [
        {
            "date":
                point.observation_date
                .isoformat(),

            "sofr":
                float(
                    point.sofr
                ),

            "effr":
                float(
                    point.effr
                ),

            "spread_bp":
                float(
                    point.spread_basis_points
                ),
        }

        for point in history
    ]