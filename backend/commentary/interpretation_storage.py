from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
import json
from typing import Any
from zoneinfo import ZoneInfo

from sqlalchemy import select

from backend.assessments.models import (
    LiquidityAssessment,
)
from backend.commentary.interpretation_context import (
    build_interpretation_context,
)
from backend.commentary.liquidity_interpreter import (
    LiquidityInterpretation,
)
from backend.database.connection import (
    get_session,
)
from backend.database.models import (
    LiquidityInterpretationSnapshot,
)


PACIFIC = ZoneInfo(
    "America/Los_Angeles"
)

INTERPRETER_VERSION = "v1"


# =============================================================
# SAVE
# =============================================================


def save_liquidity_interpretation(
    interpretation: LiquidityInterpretation,
    assessment: LiquidityAssessment,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    
    """
    Store today's liquidity interpretation.

    Re-running the interpretation on the same Pacific business
    day updates the existing row rather than creating a
    duplicate.

    The exact deterministic context packet supplied to the
    interpretation layer is retained for auditability.
    """

    generated_at = datetime.now(
        timezone.utc
    )

    snapshot_date = datetime.now(
        PACIFIC
    ).date()

    if context is None:
        context = (
            build_interpretation_context(
            assessment=assessment
            )
        )

    payload = asdict(
        interpretation
    )

    context_json = json.dumps(
        context,
        ensure_ascii=False,
        default=str,
    )

    payload_json = json.dumps(
        payload,
        ensure_ascii=False,
        default=str,
    )

    framework = context[
        "framework"
    ]

    overall_confidence = (
        framework.get(
            "overall_confidence"
        )
        or "Low"
    )

    with get_session() as session:

        existing = session.execute(
            select(
                LiquidityInterpretationSnapshot
            ).where(
                LiquidityInterpretationSnapshot.snapshot_date
                == snapshot_date
            )
        ).scalar_one_or_none()

        if existing is None:

            row = LiquidityInterpretationSnapshot(
                snapshot_date=
                    snapshot_date,

                generated_at=
                    generated_at,

                overall_verdict=
                    framework[
                        "overall_verdict"
                    ],

                overall_confidence=
                    overall_confidence,

                headline=
                    interpretation.headline,

                overall_comment=
                    interpretation.overall_comment,

                model=
                    interpretation.model,

                interpreter_version=
                    INTERPRETER_VERSION,

                fallback_used=
                    interpretation.fallback_used,

                context_json=
                    context_json,

                payload_json=
                    payload_json,
            )

            session.add(
                row
            )

        else:

            row = existing

            row.generated_at = (
                generated_at
            )

            row.overall_verdict = (
                framework[
                    "overall_verdict"
                ]
            )

            row.overall_confidence = (
                overall_confidence
            )

            row.headline = (
                interpretation.headline
            )

            row.overall_comment = (
                interpretation.overall_comment
            )

            row.model = (
                interpretation.model
            )

            row.interpreter_version = (
                INTERPRETER_VERSION
            )

            row.fallback_used = (
                interpretation.fallback_used
            )

            row.context_json = (
                context_json
            )

            row.payload_json = (
                payload_json
            )

            row.updated_at = (
                generated_at
            )

        session.commit()

    return {
        "snapshot_date":
            snapshot_date.isoformat(),

        "generated_at":
            generated_at.isoformat(),

        "overall_verdict":
            framework[
                "overall_verdict"
            ],

        "overall_confidence":
            overall_confidence,

        "model":
            interpretation.model,

        "fallback_used":
            interpretation.fallback_used,
    }


# =============================================================
# LOAD LATEST
# =============================================================


def load_latest_liquidity_interpretation(
) -> dict[str, Any] | None:
    """
    Load the newest stored liquidity interpretation.

    No model or external API call occurs here.
    """

    with get_session() as session:

        row = session.execute(
            select(
                LiquidityInterpretationSnapshot
            )
            .order_by(
                LiquidityInterpretationSnapshot
                .generated_at
                .desc()
            )
            .limit(1)
        ).scalar_one_or_none()

        if row is None:
            return None

        payload = json.loads(
            row.payload_json
        )

        return {
            "available":
                True,

            "status":
                "Stored",

            "snapshot_date":
                row.snapshot_date.isoformat(),

            "generated_at":
                row.generated_at.isoformat(),

            "overall_verdict":
                row.overall_verdict,

            "overall_confidence":
                row.overall_confidence,

            "model":
                row.model,

            "interpreter_version":
                row.interpreter_version,

            "fallback_used":
                row.fallback_used,

            **payload,
        }


# =============================================================
# LOAD LATEST CONTEXT
# =============================================================


def load_latest_interpretation_context(
) -> dict[str, Any] | None:
    """
    Load the deterministic context packet associated with the
    newest stored interpretation.

    Intended for diagnostics and historical comparison.
    """

    with get_session() as session:

        row = session.execute(
            select(
                LiquidityInterpretationSnapshot
            )
            .order_by(
                LiquidityInterpretationSnapshot
                .generated_at
                .desc()
            )
            .limit(1)
        ).scalar_one_or_none()

        if row is None:
            return None

        return json.loads(
            row.context_json
        )