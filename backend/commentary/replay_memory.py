from __future__ import annotations

import json

from datetime import date
from pathlib import Path
from typing import Any


DEFAULT_MEMORY_PATH = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "replay_memory.json"
)


def _empty_memory() -> dict[str, Any]:
    return {
        "version": 1,
        "days": [],
    }


def _load_memory(
    path: Path,
) -> dict[str, Any]:
    if not path.exists():
        return _empty_memory()

    try:
        data = json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )
    except (
        json.JSONDecodeError,
        OSError,
    ):
        return _empty_memory()

    if not isinstance(
        data.get("days"),
        list,
    ):
        return _empty_memory()

    return data


def _write_memory(
    memory: dict[str, Any],
    path: Path,
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temp_path = path.with_suffix(
        ".tmp"
    )

    temp_path.write_text(
        json.dumps(
            memory,
            indent=2,
            sort_keys=True,
            default=str,
        )
        + "\n",
        encoding="utf-8",
    )

    temp_path.replace(path)


def _build_day_record(
    packet: dict[str, Any],
) -> dict[str, Any]:
    framework = packet.get(
        "framework",
        {},
    )

    factors = packet.get(
        "factors",
        [],
    )

    factor_verdicts = {
        factor["key"]: factor["verdict"]
        for factor in factors
        if (
            factor.get("key")
            and factor.get("verdict")
        )
    }

    record = {
        "replay_date":
            packet["replay_date"],

        "overall_verdict":
            framework.get(
                "overall_verdict"
            ),

        "overall_confidence":
            framework.get(
                "overall_confidence"
            ),

        "factor_verdicts":
            factor_verdicts,

        "non_normal_factors":
            framework.get(
                "non_normal_factors",
                [],
            ),

        "anomaly_diagnostics":
            packet.get(
                "anomaly_diagnostics",
                [],
            ),
    }

    policy_context = packet.get(
        "policy_context"
    )

    if policy_context is not None:
        record["policy_context"] = (
            policy_context
        )

    return record


def record_replay_day(
    packet: dict[str, Any],
    path: Path | None = None,
) -> None:
    """
    Persist one deterministic replay-day state.

    Re-running the same replay date replaces the prior
    record rather than creating a duplicate.
    """

    memory_path = (
        path
        if path is not None
        else DEFAULT_MEMORY_PATH
    )

    replay_date = packet.get(
        "replay_date"
    )

    if not replay_date:
        raise ValueError(
            "Replay packet does not contain replay_date."
        )

    memory = _load_memory(
        memory_path
    )

    days = [
        day
        for day in memory["days"]
        if (
            day.get("replay_date")
            != replay_date
        )
    ]

    days.append(
        _build_day_record(packet)
    )

    days.sort(
        key=lambda item:
            item["replay_date"]
    )

    memory["days"] = days

    _write_memory(
        memory,
        memory_path,
    )


def load_recent_replay_history(
    replay_date: date,
    limit: int = 10,
    path: Path | None = None,
) -> list[dict[str, Any]]:
    """
    Return only replay states strictly before the current
    replay date.

    Future records can therefore never leak into an
    earlier historical replay.
    """

    memory_path = (
        path
        if path is not None
        else DEFAULT_MEMORY_PATH
    )

    memory = _load_memory(
        memory_path
    )

    cutoff = replay_date.isoformat()

    prior_days = [
        day
        for day in memory["days"]
        if (
            day.get("replay_date", "")
            < cutoff
        )
    ]

    return prior_days[-limit:]
