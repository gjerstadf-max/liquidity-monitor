from __future__ import annotations

from fastapi import APIRouter, Query

from backend.services.daily_snapshot import build_daily_snapshot
from backend.services.funding_history import get_funding_history


router = APIRouter(
    prefix="/api",
    tags=["Liquidity Monitor API"],
)


@router.get("/snapshot")
def snapshot():
    current = build_daily_snapshot()

    return {
        "generated_at": current.generated_at.isoformat(),

        "assessment": {
            "score": current.assessment.overall_score,
            "condition": current.assessment.overall_condition,
            "confidence": current.assessment.confidence,

            "funding": {
                "score": current.assessment.funding.score,
                "condition": current.assessment.funding.condition,
                "confidence": current.assessment.funding.confidence,
                "summary": current.assessment.funding.summary,
            },
        },

        "funding": {
            "observation_date": (
                current.funding.observation_date.isoformat()
            ),

            "previous_observation_date": (
                current.funding
                .previous_observation_date
                .isoformat()
            ),

            "sofr": float(current.funding.sofr),

            "previous_sofr": float(
                current.funding.previous_sofr
            ),

            "sofr_change_bp": float(
                current.funding.sofr_change_bp
            ),

            "effr": float(current.funding.effr),

            "previous_effr": float(
                current.funding.previous_effr
            ),

            "effr_change_bp": float(
                current.funding.effr_change_bp
            ),

            "spread_bp": float(
                current.funding.spread_basis_points
            ),

            "previous_spread_bp": float(
                current.funding.previous_spread_basis_points
            ),

            "spread_change_bp": float(
                current.funding.spread_change_bp
            ),
        },

        "morning_brief": {
            "headline": current.morning_brief.headline,
            "summary": current.morning_brief.summary,
            "what_matters": current.morning_brief.what_matters,
            "what_to_watch": current.morning_brief.what_to_watch,
        },
    }


@router.get("/funding/history")
def funding_history(
    observations: int = Query(
        default=60,
        ge=1,
        le=1000,
    ),
):
    history = get_funding_history(
        observation_count=observations
    )

    return [
        {
            "date": point.observation_date.isoformat(),
            "sofr": float(point.sofr),
            "effr": float(point.effr),
            "spread_bp": float(
                point.spread_basis_points
            ),
        }
        for point in history
    ]