from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from backend.assessments.engine import (
    build_liquidity_assessment,
)
from backend.assessments.models import (
    LiquidityAssessment,
)
from backend.factors.registry import (
    factor_definition,
)


# =============================================================
# INTERPRETATION CONTEXT
# =============================================================


def build_interpretation_context(
    assessment: LiquidityAssessment | None = None,
) -> dict[str, Any]:
    """
    Build the structured context packet supplied to the
    liquidity interpretation layer.

    The packet contains only deterministic framework output.

    It does not:
        - change factor verdicts
        - calculate new market metrics
        - override the overall verdict
        - fetch external information

    Its purpose is to give an interpretation agent enough
    economic context to explain how the registered factors
    interact.
    """

    if assessment is None:

        assessment = (
            build_liquidity_assessment()
        )

    factors: list[
        dict[str, Any]
    ] = []

    verdict_counts = {
        "Normal": 0,
        "Watch": 0,
        "Elevated": 0,
        "Stressed": 0,
    }

    confidence_counts = {
        "Low": 0,
        "Moderate": 0,
        "High": 0,
    }

    # ---------------------------------------------------------
    # REGISTERED FACTORS
    # ---------------------------------------------------------

    for factor in assessment.factors:

        definition = (
            factor_definition(
                factor.key
            )
        )

        factor_assessment = (
            factor.assessment
        )

        verdict = (
            factor_assessment.verdict
        )

        confidence = (
            factor_assessment.confidence
        )

        if verdict in verdict_counts:
            verdict_counts[
                verdict
            ] += 1

        if confidence in confidence_counts:
            confidence_counts[
                confidence
            ] += 1

        factors.append(
            {
                "key":
                    factor.key,

                "display_name":
                    factor.display_name,

                "category":
                    factor_assessment.category,

                "verdict":
                    verdict,

                "confidence":
                    confidence,

                "assessment":
                    factor_assessment.summary,

                "what_it_measures":
                    definition.what_matters_builder(),

                "current_watch_context":
                    definition.watch_builder(
                        verdict
                    ),
            }
        )

    # ---------------------------------------------------------
    # NON-NORMAL FACTORS
    # ---------------------------------------------------------

    non_normal_factors = [
        factor["key"]
        for factor in factors
        if factor["verdict"] != "Normal"
    ]

    stressed_factors = [
        factor["key"]
        for factor in factors
        if factor["verdict"] == "Stressed"
    ]

    elevated_factors = [
        factor["key"]
        for factor in factors
        if factor["verdict"] == "Elevated"
    ]

    watch_factors = [
        factor["key"]
        for factor in factors
        if factor["verdict"] == "Watch"
    ]

    normal_factors = [
        factor["key"]
        for factor in factors
        if factor["verdict"] == "Normal"
    ]

    # ---------------------------------------------------------
    # PACKET
    # ---------------------------------------------------------

    return {
        "generated_at":
            datetime.now(
                timezone.utc
            ).isoformat(),

        "framework": {

            "overall_verdict":
                assessment.overall_verdict,

            "overall_confidence": (
                "Low"
                if confidence_counts["Low"] > 0
                else
                "Moderate"
                if confidence_counts["Moderate"] > 0
                else
                "High"
            ),

            # Legacy deterministic summary.
            #
            # This remains useful as a fallback, but the
            # interpretation agent should rely primarily on
            # the complete factor packet because the legacy
            # summary predates the full eight-factor framework.
            "deterministic_summary":
                assessment.summary,

            "factor_count":
                len(factors),

            "verdict_counts":
                verdict_counts,

            "confidence_counts":
                confidence_counts,

            "non_normal_factors":
                non_normal_factors,

            "stressed_factors":
                stressed_factors,

            "elevated_factors":
                elevated_factors,

            "watch_factors":
                watch_factors,

            "normal_factors":
                normal_factors,
        },

        "factors":
            factors,
    }