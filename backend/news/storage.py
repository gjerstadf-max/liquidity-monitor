from __future__ import annotations

import json

from dataclasses import asdict
from datetime import date, datetime, timezone
from typing import Any
from zoneinfo import ZoneInfo

from sqlalchemy import select

from backend.database.connection import (
    get_session,
)
from backend.database.models import (
    NewsSnapshot,
)
from backend.news.narrative import (
    MarketNarrative,
)


PACIFIC = ZoneInfo(
    "America/Los_Angeles"
)


# =============================================================
# JSON SERIALIZATION
# =============================================================


def _json_default(
    value: Any,
) -> str:

    if isinstance(
        value,
        (datetime, date),
    ):
        return value.isoformat()

    raise TypeError(
        f"Object of type "
        f"{type(value).__name__} "
        "is not JSON serializable"
    )


# =============================================================
# SAVE
# =============================================================


def save_market_narrative(
    narrative: MarketNarrative,
) -> dict[str, Any]:
    """
    Save today's Market Narrative.

    Re-running the news refresh on the same day
    updates the existing row instead of creating
    duplicates.
    """

    generated_at = datetime.now(
        timezone.utc
    )

    snapshot_date = datetime.now(
        PACIFIC
    ).date()


    payload = asdict(
        narrative
    )

    payload_json = json.dumps(
        payload,
        default=_json_default,
        ensure_ascii=False,
    )


    with get_session() as session:

        existing = session.execute(
            select(
                NewsSnapshot
            ).where(
                NewsSnapshot.snapshot_date
                == snapshot_date
            )
        ).scalar_one_or_none()


        if existing is None:

            row = NewsSnapshot(
                snapshot_date=
                    snapshot_date,

                generated_at=
                    generated_at,

                market_attention=
                    narrative.market_attention,

                directional_confirmation=
                    narrative.directional_confirmation,

                funding_severity=
                    narrative.funding_severity,

                system_liquidity_severity=
                    narrative.system_liquidity_severity,

                summary=
                    narrative.summary,

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

            row.market_attention = (
                narrative.market_attention
            )

            row.directional_confirmation = (
                narrative
                .directional_confirmation
            )

            row.funding_severity = (
                narrative.funding_severity
            )

            row.system_liquidity_severity = (
                narrative
                .system_liquidity_severity
            )

            row.summary = (
                narrative.summary
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

            "market_attention":
                narrative.market_attention,

            "directional_confirmation":
                narrative.directional_confirmation,

            "story_count":
                len(narrative.stories),
        }


# =============================================================
# LOAD
# =============================================================


def load_latest_market_narrative(
) -> dict[str, Any] | None:
    """
    Load the newest stored Market Narrative.

    This function performs no external HTTP calls.
    """

    with get_session() as session:

        row = session.execute(
            select(
                NewsSnapshot
            )
            .order_by(
                NewsSnapshot.generated_at.desc()
            )
            .limit(1)
        ).scalar_one_or_none()


        if row is None:
            return None


        payload = json.loads(
            row.payload_json
        )


        return {
            "available": True,

            "status": "Stored",

            "snapshot_date":
                row.snapshot_date.isoformat(),

            "generated_at":
                row.generated_at.isoformat(),

            **payload,
        }