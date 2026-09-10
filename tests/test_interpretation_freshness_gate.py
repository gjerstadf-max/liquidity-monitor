from datetime import date
from types import SimpleNamespace

import scripts.daily_refresh as daily_refresh


def _freshness(
    *,
    observation_date: date,
    expected_date: date,
    is_current: bool,
    label: str,
    stale_days: int = 0,
):
    return SimpleNamespace(
        observation_date=observation_date,
        expected_observation_date=expected_date,
        business_days_stale=stale_days,
        is_current=is_current,
        label=label,
    )


def test_interpretation_skips_stale_required_evidence(
    monkeypatch,
):
    assessment = object()

    snapshot = SimpleNamespace(
        assessment=assessment,
        funding_freshness=_freshness(
            observation_date=date(2026, 9, 8),
            expected_date=date(2026, 9, 9),
            is_current=False,
            label="1 business day stale",
            stale_days=1,
        ),
        system_liquidity_freshness=_freshness(
            observation_date=date(2026, 9, 2),
            expected_date=date(2026, 9, 2),
            is_current=True,
            label="Current weekly release",
        ),
    )

    monkeypatch.setattr(
        daily_refresh,
        "build_daily_snapshot",
        lambda: snapshot,
    )

    monkeypatch.setattr(
        daily_refresh,
        "build_interpretation_context",
        lambda assessment: {
            "framework": {}
        },
    )

    def fail_interpreter(*args, **kwargs):
        raise AssertionError(
            "Interpreter must not be called "
            "when required evidence is stale."
        )

    def fail_save(*args, **kwargs):
        raise AssertionError(
            "Interpretation must not be saved "
            "when required evidence is stale."
        )

    monkeypatch.setattr(
        daily_refresh,
        "interpret_liquidity",
        fail_interpreter,
    )

    monkeypatch.setattr(
        daily_refresh,
        "save_liquidity_interpretation",
        fail_save,
    )

    result = (
        daily_refresh
        ._refresh_liquidity_interpretation()
    )

    assert result["status"] == (
        "skipped_stale_inputs"
    )

    assert result["saved"] is False

    assert result["stale_inputs"] == [
        "funding"
    ]


def test_interpretation_uses_and_stores_exact_context(
    monkeypatch,
):
    assessment = object()

    snapshot = SimpleNamespace(
        assessment=assessment,
        funding_freshness=_freshness(
            observation_date=date(2026, 9, 9),
            expected_date=date(2026, 9, 9),
            is_current=True,
            label="Current",
        ),
        system_liquidity_freshness=_freshness(
            observation_date=date(2026, 9, 2),
            expected_date=date(2026, 9, 2),
            is_current=True,
            label="Current weekly release",
        ),
    )

    context = {
        "framework": {
            "overall_verdict": "Watch",
        }
    }

    captured = {}

    monkeypatch.setattr(
        daily_refresh,
        "build_daily_snapshot",
        lambda: snapshot,
    )

    monkeypatch.setattr(
        daily_refresh,
        "build_interpretation_context",
        lambda assessment: context,
    )

    def fake_interpret(
        assessment=None,
        packet=None,
    ):
        captured["interpreter_context"] = packet

        return SimpleNamespace(
            fallback_used=False,
            model="test-model",
        )

    def fake_save(
        interpretation,
        assessment,
        context=None,
    ):
        captured["storage_context"] = context

        return {
            "snapshot_date": "2026-09-10",
            "generated_at":
                "2026-09-10T18:36:10+00:00",
            "overall_verdict": "Watch",
            "overall_confidence": "Moderate",
            "model": "test-model",
            "fallback_used": False,
        }

    monkeypatch.setattr(
        daily_refresh,
        "interpret_liquidity",
        fake_interpret,
    )

    monkeypatch.setattr(
        daily_refresh,
        "save_liquidity_interpretation",
        fake_save,
    )

    result = (
        daily_refresh
        ._refresh_liquidity_interpretation()
    )

    assert result["status"] == "stored"
    assert result["saved"] is True

    assert (
        captured["interpreter_context"]
        is context
    )

    assert (
        captured["storage_context"]
        is context
    )

    freshness = context[
        "evidence_freshness"
    ]

    assert freshness["validated"] is True

    assert (
        freshness["funding"]["is_current"]
        is True
    )

    assert (
        freshness[
            "system_liquidity"
        ]["is_current"]
        is True
    )