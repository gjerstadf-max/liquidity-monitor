from __future__ import annotations

from datetime import (
    datetime,
    timezone,
)

from backend.assessments.engine import (
    build_liquidity_assessment,
)

from backend.commentary.interpretation_storage import (
    save_liquidity_interpretation,
)

from backend.commentary.liquidity_interpreter import (
    interpret_liquidity,
)

from backend.services.market_data_refresh import (
    refresh_market_data,
)


# =============================================================
# LIQUIDITY INTERPRETATION
# =============================================================


def _refresh_liquidity_interpretation() -> dict[str, object]:
    """
    Build and store the current AI liquidity interpretation.

    Interpretation is downstream of the deterministic market-data,
    metric, signal and assessment layers.

    Failure here must never cause the market-data refresh itself
    to fail.

    If the model call falls back to deterministic commentary, do
    not overwrite the most recent successfully generated AI
    interpretation.
    """

    try:

        assessment = (
            build_liquidity_assessment()
        )

        interpretation = (
            interpret_liquidity(
                assessment=assessment
            )
        )

        if interpretation.fallback_used:

            print()

            print(
                "Liquidity interpretation:"
                " AI unavailable — fallback generated."
            )

            print(
                "Stored AI interpretation was not overwritten."
            )

            return {
                "status": "fallback",
                "saved": False,
                "model": interpretation.model,
            }

        saved = (
            save_liquidity_interpretation(
                interpretation=
                    interpretation,
                assessment=
                    assessment,
            )
        )

        print()

        print(
            "Liquidity interpretation:"
            " generated and stored."
        )

        print(
            "Overall verdict: "
            f"{saved['overall_verdict']}"
        )

        print(
            "Overall confidence: "
            f"{saved['overall_confidence']}"
        )

        print(
            "Model: "
            f"{saved['model']}"
        )

        return {
            "status": "stored",
            "saved": True,
            **saved,
        }

    except Exception as exc:

        print()

        print(
            "Liquidity interpretation refresh failed: "
            f"{exc}"
        )

        print(
            "Market-data refresh remains valid."
        )

        return {
            "status": "failed",
            "saved": False,
            "error": str(exc),
        }


# =============================================================
# DAILY REFRESH
# =============================================================


def daily_refresh() -> None:
    """
    Run the Liquidity Monitor production refresh.

    Sequence:

        1. Refresh market data
        2. Build deterministic eight-factor assessment
        3. Generate AI cross-factor interpretation
        4. Store successful interpretation

    The deterministic framework remains authoritative.

    AI interpretation is an explanatory layer only and cannot
    cause the market-data refresh to fail.
    """

    started_at = datetime.now(
        timezone.utc
    )

    print()

    print(
        "Liquidity Monitor Daily Refresh"
    )

    print(
        "=" * 72
    )

    print(
        "Started: "
        f"{started_at.isoformat()}"
    )

    # ---------------------------------------------------------
    # MARKET DATA
    # ---------------------------------------------------------

    try:

        result = (
            refresh_market_data()
        )

    except Exception as exc:

        print()

        print(
            "=" * 72
        )

        print(
            "DAILY REFRESH FAILED"
        )

        print(
            "=" * 72
        )

        print()

        print(
            f"Error: {exc}"
        )

        raise

    # ---------------------------------------------------------
    # INTELLIGENT INTERPRETATION
    # ---------------------------------------------------------

    interpretation_result = (
        _refresh_liquidity_interpretation()
    )

    # ---------------------------------------------------------
    # COMPLETE
    # ---------------------------------------------------------

    completed_at = datetime.now(
        timezone.utc
    )

    print()

    print(
        "=" * 72
    )

    print(
        "DAILY REFRESH COMPLETE"
    )

    print(
        "=" * 72
    )

    print()

    print(
        "Providers refreshed: "
        f"{result.provider_count}"
    )

    print(
        "Catalog series refreshed: "
        f"{result.series_count}"
    )

    print(
        "Observations inserted: "
        f"{result.inserted}"
    )

    print()

    print(
        "Structured datasets refreshed: "
        f"{result.structured_dataset_count}"
    )

    print(
        "Structured records inserted: "
        f"{result.structured_inserted}"
    )

    print(
        "Structured records updated: "
        f"{result.structured_updated}"
    )

    print(
        "Structured records skipped: "
        f"{result.structured_skipped}"
    )

    print(
        "Observations skipped: "
        f"{result.skipped}"
    )

    print()

    print(
        "Interpretation status: "
        f"{interpretation_result['status']}"
    )

    print(
        "Interpretation stored: "
        f"{interpretation_result['saved']}"
    )

    print()

    print(
        "Completed: "
        f"{completed_at.isoformat()}"
    )


# =============================================================
# DIRECT EXECUTION
# =============================================================


if __name__ == "__main__":
    daily_refresh()