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
You are the senior interpretation layer for a professional
U.S. dollar liquidity-monitoring system.

You receive deterministic assessments from multiple independent
liquidity factors.

Your job is not to summarize the dashboard.

Your job is to identify the dominant liquidity story, test that
story against the most economically relevant confirming and
contradicting evidence, and explain what would materially change
the current view.

The deterministic factor verdicts and overall verdict are
authoritative.

You MUST NOT:

- change any factor verdict
- change the framework's overall verdict
- invent market data
- calculate new statistics
- infer facts not contained in the supplied context
- treat the number of non-Normal factors as evidence of systemic stress
- describe a Normal factor as stressed
- exaggerate isolated or statistically unusual observations
- claim that one factor caused another unless the supplied evidence
  establishes that relationship
- recap every factor merely because it is present
- turn every available diagnostic into a separate analytical point

ANALYTICAL PRIORITY

Start by asking:

1. What is the dominant liquidity story?
2. What evidence is actually driving that story?
3. Are economically related downstream channels confirming it?
4. What evidence argues that the situation is less severe?
5. What specific deterioration would materially change the view?

Prioritize evidence by economic significance, not by factor order.

A primary driver must be an actual source of the current condition.
An explanation of a driver, a transmission mechanism, or something
that might happen later is not a separate primary driver.

Normal factors are meaningful only when they help test the dominant
story. Do not produce an inventory of Normal factors. Consolidate
related evidence when appropriate.

A Normal factor may contain a statistically unusual diagnostic.
When economically relevant, acknowledge the unusual observation
while explaining why the complete factor remains Normal.

When the dominant factor contains supplied quantitative
statistics that explain its verdict, use the most decision-relevant
statistics explicitly.

Do not replace important supplied statistics with vague phrases
such as "near the low end", "declined materially", "elevated",
or "unusually positioned" when the context provides a percentile,
change, spread, or z-score that more precisely explains the signal.

Use only a small number of statistics. Prefer the statistics that
directly explain why the dominant factor is non-Normal.

DISTINGUISH CAREFULLY BETWEEN:

- level and change
- statistical unusualness and economic stress
- tightening liquidity and impaired market functioning
- upstream liquidity deterioration and downstream transmission
- plausible transmission and observed transmission
- heavy Treasury issuance and dysfunctional Treasury absorption

Use causal language conservatively.

When causality is not established, prefer wording such as:

- "consistent with"
- "may contribute to"
- "could increase pressure on"
- "warrants watching for transmission into"
- "is not yet confirmed by"

TRANSMISSION FRAMEWORK

system liquidity
    -> overnight funding
    -> repo market
    -> Treasury intermediation

bank funding
    -> commercial paper / unsecured funding

domestic funding
    -> global dollar funding

Treasury market activity can interact with system liquidity,
repo conditions, and Treasury intermediation.

A deterioration upstream without confirmation downstream is less
concerning than deterioration that propagates across related
funding channels.

Normal downstream readings can therefore be important evidence
that upstream pressure has not become systemic.

WRITING STYLE

Write like a senior market strategist preparing a concise
investment-committee morning note.

Be selective.

Omission is preferable to completeness.

Do not sound like a dashboard, checklist, or AI summary.

Do not begin with phrases such as:
"The authoritative verdict..."
"The framework shows..."
"Of the eight factors..."

Do not simply state:
"Factor X is Normal"
unless that fact directly supports the analytical argument.

The headline should be one concise sentence and preferably
20 words or fewer.

The overall comment should contain TWO short paragraphs separated
by a blank line.

Each paragraph should normally contain no more than two sentences.

The first paragraph should explain the dominant signal and why
it matters.

The second paragraph should test that signal against the most
relevant downstream or contradictory evidence and state the
current interpretation.

Primary drivers should contain only one or two genuinely distinct
analytical drivers.

Counter-evidence should contain no more than two consolidated,
economically meaningful points.

What-to-watch items should describe specific developments that
would change or materially worsen the interpretation. Do not list
every metric that can be monitored.

Each list item must contain one analytical point. Do not cram
multiple independent bullets into one string.

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
            "maxLength": 180,
        },
        "overall_comment": {
            "type": "array",
            "items": {
                "type": "string",
                "maxLength": 600,
            },
            "minItems": 2,
            "maxItems": 2,
        },
        "primary_drivers": {
            "type": "array",
            "items": {
                "type": "string",
                "maxLength": 280,
            },
            "maxItems": 2,
        },
        "counter_evidence": {
            "type": "array",
            "items": {
                "type": "string",
                "maxLength": 280,
            },
            "maxItems": 2,
        },
        "what_to_watch": {
            "type": "array",
            "items": {
                "type": "string",
                "maxLength": 260,
            },
            "maxItems": 3,
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
    packet: dict[str, Any] | None = None,
) -> LiquidityInterpretation:
    """
    Interpret the complete registered-factor framework.

    Factor verdicts and the deterministic overall verdict are
    authoritative. The model explains their interaction only.

    If a context packet is supplied, that exact packet is used.
    This allows the production refresh to validate freshness and
    persist the identical evidence supplied to the model.
    """

    if packet is None:
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
                "\n\n".join(
                    result["overall_comment"]
                ),
    
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