from __future__ import annotations

from datetime import date
from typing import Any

from backend.metrics.treasury_market_activity import (
    treasury_iorb_outlier_diagnostic,
)


def build_anomaly_diagnostics(
    as_of_date: date | None = None,
) -> list[dict[str, Any]]:
    """
    Build deterministic anomaly diagnostics for the
    interpretation layer.

    Diagnostics are informational only. They never change
    factor verdicts or the overall liquidity verdict.

    Only triggered anomalies are returned.
    """

    diagnostics: list[dict[str, Any]] = []

    try:
        treasury_iorb = treasury_iorb_outlier_diagnostic(
            as_of_date=as_of_date,
        )
    except RuntimeError:
        treasury_iorb = None

    if (
        treasury_iorb is not None
        and treasury_iorb.triggered
    ):
        diagnostics.append(
            {
                "type":
                    "treasury_iorb_relative_pricing",

                "factor":
                    "treasury_market_activity",

                "diagnostic_only":
                    True,

                "changes_factor_verdict":
                    False,

                "observation_date":
                    treasury_iorb.observation_date.isoformat(),

                "spread_bp":
                    round(treasury_iorb.spread_bp, 1),

                "zscore":
                    round(treasury_iorb.spread_zscore, 2),

                "percentile":
                    round(treasury_iorb.spread_percentile, 2),

                "treasury_3m_percent":
                    round(treasury_iorb.treasury_3m_percent, 2),

                "iorb_percent":
                    round(treasury_iorb.iorb_percent, 2),

                "treasury_change_1d_bp":
                    round(treasury_iorb.treasury_change_1d_bp, 1),

                "treasury_change_5d_bp":
                    round(treasury_iorb.treasury_change_5d_bp, 1),

                "treasury_change_20d_bp":
                    round(treasury_iorb.treasury_change_20d_bp, 1),

                "iorb_change_1d_bp":
                    round(treasury_iorb.iorb_change_1d_bp, 1),

                "iorb_change_5d_bp":
                    round(treasury_iorb.iorb_change_5d_bp, 1),

                "iorb_change_20d_bp":
                    round(treasury_iorb.iorb_change_20d_bp, 1),

                "spread_change_1d_bp":
                    round(treasury_iorb.spread_change_1d_bp, 1),

                "spread_change_5d_bp":
                    round(treasury_iorb.spread_change_5d_bp, 1),

                "spread_change_20d_bp":
                    round(treasury_iorb.spread_change_20d_bp, 1),

                "consecutive_above_95th":
                    treasury_iorb.consecutive_above_95th,

                "consecutive_above_99th":
                    treasury_iorb.consecutive_above_99th,

                "primary_mover":
                    treasury_iorb.primary_mover,
            }
        )

    return diagnostics
