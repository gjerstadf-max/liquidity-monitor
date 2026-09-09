from __future__ import annotations

from dataclasses import dataclass
import json
import os
from typing import Any

from openai import OpenAI

from backend.assessments.models import (
    LiquidityAssessment,
)
from backend.commentary.interpretation_context import (
    build_interpretation_context,
)


MODEL = os.getenv(
    "LIQUIDITY_INTERPRETER_MODEL",
    "gpt-5.6-terra",
)


# =============================================================
# RESULT OBJECT
# =============================================================


@dataclass(frozen=True)
class LiquidityInterpretation:
    headline: str
    overall_comment: str
    primary_drivers: list[str]
    counter_evidence: list[str]
    what_to_watch: list[str]
    model: str
    fallback_used: bool


# =============================================================
# SYSTEM INSTRUCTIONS
# =============================================================


INTERPRETER_INSTRUCTIONS = """
You are the interpretation layer for a professional U.S. dollar
liquidity-monitoring system.

You receive deterministic assessments from multiple independent
liquidity factors.

Your job is to interpret the factors together.

You MUST NOT:
- change any factor verdict
- change the framework's overall verdict
- invent market data
- calculate new statistics
- infer facts not contained in the supplied context
- treat the number of Watch factors as sufficient evidence of
  systemic stress
- describe a Normal factor as stressed
- exaggerate isolated or statistically unusual observations

You SHOULD:
- identify which non-Normal factors are driving the current condition
- identify corroboration between economically related factors
- identify contradictions or lack of confirmation
- use Normal factors as meaningful counter-evidence when appropriate
- distinguish localized pressure from broad or systemic stress
- distinguish heavy-but-orderly Treasury issuance from genuine
  market dysfunction when the supplied evidence supports that
  distinction
- recognize whether pressure is transmitting across funding channels
- explain what would need to deteriorate for the interpretation to
  become materially worse
- write in concise institutional investment-committee language

Think in terms of transmission channels:

system liquidity
    -> overnight funding
    -> repo market
    -> Treasury intermediation

and

bank funding
    -> commercial paper / unsecured funding

and

domestic funding
    -> global dollar funding

Treasury market activity can interact with system liquidity, repo,
and Treasury intermediation.

A Watch in one area without confirmation elsewhere is less concerning
than corroborating deterioration across related channels.

Normal readings in downstream stress channels can be important
evidence that upstream pressure has not become systemic.

The framework's supplied overall_verdict is authoritative.

Return only the requested structured JSON.
"""


# =============================================================
# STRUCTURED OUTPUT SCHEMA
# =============================================================


OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {

        "headline": {
            "type": "string",
        },

        "overall_comment": {
            "type": "string",
        },

        "primary_drivers": {
            "type": "array",
            "items": {
                "type": "string",
            },
            "maxItems": 4,
        },

        "counter_evidence": {
            "type": "array",
            "items": {
                "type": "string",
            },
            "maxItems": 4,
        },

        "what_to_watch": {
            "type": "array",
            "items": {
                "type": "string",
            },
            "maxItems": 4,
        },
    },

    "required": [
        "headline",
        "overall_comment",
        "primary_drivers",
        "counter_evidence",
        "what_to_watch",
    ],

    "additionalProperties": False,
}


# =============================================================
# FALLBACK
# =============================================================


def _fallback_interpretation(
    packet: dict[str, Any],
) -> LiquidityInterpretation:
    """
    Deterministic fallback.

    The application remains usable if the model call fails.
    """

    framework = packet[
        "framework"
    ]

    verdict = framework[
        "overall_verdict"
    ]

    summary = framework[
        "deterministic_summary"
    ]

    watch_factors = framework.get(
        "watch_factors",
        [],
    )

    elevated_factors = framework.get(
        "elevated_factors",
        [],
    )

    stressed_factors = framework.get(
        "stressed_factors",
        [],
    )

    normal_factors = framework.get(
        "normal_factors",
        [],
    )

    primary_drivers = (
        stressed_factors
        + elevated_factors
        + watch_factors
    )[:4]

    return LiquidityInterpretation(
        headline=
            f"Overall liquidity conditions: {verdict}.",

        overall_comment=
            summary,

        primary_drivers=
            primary_drivers,

        counter_evidence=
            normal_factors[:4],

        what_to_watch=
            watch_factors[:4],

        model=
            "deterministic-fallback",

        fallback_used=
            True,
    )


# =============================================================
# MODEL INTERPRETATION
# =============================================================


def interpret_liquidity(
    assessment: LiquidityAssessment | None = None,
) -> LiquidityInterpretation:
    """
    Interpret the complete registered-factor framework.

    Factor verdicts and the deterministic overall verdict are
    authoritative. The model explains their interaction only.
    """

    packet = (
        build_interpretation_context(
            assessment=
                assessment
        )
    )

    try:

        client = OpenAI()

        response = (
            client.responses.create(
                model=
                    MODEL,

                instructions=
                    INTERPRETER_INSTRUCTIONS,

                input=(
                    "Interpret the following liquidity framework.\n\n"
                    + json.dumps(
                        packet,
                        indent=2,
                        default=str,
                    )
                ),

                reasoning={
                    "effort": "medium",
                },

                text={
                    "format": {
                        "type": "json_schema",
                        "name": "liquidity_interpretation",
                        "strict": True,
                        "schema": OUTPUT_SCHEMA,
                    }
                },
            )
        )

        result = json.loads(
            response.output_text
        )

        return LiquidityInterpretation(
            headline=
                result["headline"],

            overall_comment=
                result["overall_comment"],

            primary_drivers=
                result["primary_drivers"],

            counter_evidence=
                result["counter_evidence"],

            what_to_watch=
                result["what_to_watch"],

            model=
                MODEL,

            fallback_used=
                False,
        )

    except Exception as exc:

        print(
            "Liquidity interpretation unavailable: "
            f"{exc}"
        )

        return (
            _fallback_interpretation(
                packet
            )
        )


# =============================================================
# TERMINAL DISPLAY
# =============================================================


def print_liquidity_interpretation(
    interpretation: LiquidityInterpretation,
) -> None:

    print()

    print(
        "LIQUIDITY MONITOR — "
        "INTELLIGENT INTERPRETATION"
    )

    print("=" * 80)

    print()

    print(
        interpretation.headline
    )

    print()

    print(
        interpretation.overall_comment
    )

    print()

    print("PRIMARY DRIVERS")

    print("-" * 80)

    for item in (
        interpretation.primary_drivers
    ):

        print(
            f"• {item}"
        )

    print()

    print("COUNTER-EVIDENCE")

    print("-" * 80)

    for item in (
        interpretation.counter_evidence
    ):

        print(
            f"• {item}"
        )

    print()

    print("WHAT TO WATCH")

    print("-" * 80)

    for item in (
        interpretation.what_to_watch
    ):

        print(
            f"• {item}"
        )

    print()

    print(
        f"Model: "
        f"{interpretation.model}"
    )

    print(
        f"Fallback used: "
        f"{interpretation.fallback_used}"
    )


# =============================================================
# DIRECT EXECUTION
# =============================================================


if __name__ == "__main__":

    interpretation = (
        interpret_liquidity()
    )

    print_liquidity_interpretation(
        interpretation
    )