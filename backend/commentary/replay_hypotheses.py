from __future__ import annotations

import json

from datetime import date
from pathlib import Path
from typing import Any


DEFAULT_HYPOTHESIS_PATH = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "replay_hypotheses.json"
)


ACTIVE_STATUSES = {
    "active",
    "strengthened",
    "weakened",
    "partially_supported",
}

TERMINAL_STATUSES = {
    "supported",
    "rejected",
    "resolved",
}

ALLOWED_STATUSES = (
    ACTIVE_STATUSES
    | TERMINAL_STATUSES
)


def _empty_ledger() -> dict[str, Any]:
    return {
        "version": 1,
        "hypotheses": [],
    }


def _load_ledger(
    path: Path,
) -> dict[str, Any]:
    if not path.exists():
        return _empty_ledger()

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
        return _empty_ledger()

    if not isinstance(
        data.get("hypotheses"),
        list,
    ):
        return _empty_ledger()

    return data


def _write_ledger(
    ledger: dict[str, Any],
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
            ledger,
            indent=2,
            sort_keys=True,
            default=str,
        )
        + "\n",
        encoding="utf-8",
    )

    temp_path.replace(path)


def _next_hypothesis_id(
    created_date: date,
    hypotheses: list[dict[str, Any]],
) -> str:
    prefix = (
        f"H-{created_date.strftime('%Y%m%d')}-"
    )

    existing = [
        item
        for item in hypotheses
        if str(
            item.get("id", "")
        ).startswith(prefix)
    ]

    sequence = len(existing) + 1

    return (
        f"{prefix}{sequence:02d}"
    )


def create_hypothesis(
    *,
    created_date: date,
    hypothesis: str,
    confidence: str,
    supporting_evidence: list[str],
    expected_if_true: list[str],
    would_weaken: list[str],
    review_by: date | None = None,
    path: Path | None = None,
) -> dict[str, Any]:
    """
    Create an immutable hypothesis record.

    Later evidence is appended through evaluations rather
    than rewriting the original hypothesis.
    """

    memory_path = (
        path
        if path is not None
        else DEFAULT_HYPOTHESIS_PATH
    )

    ledger = _load_ledger(
        memory_path
    )

    hypothesis_id = _next_hypothesis_id(
        created_date,
        ledger["hypotheses"],
    )

    record = {
        "id":
            hypothesis_id,

        "created_date":
            created_date.isoformat(),

        "hypothesis":
            hypothesis,

        "confidence":
            confidence,

        "supporting_evidence":
            list(supporting_evidence),

        "expected_if_true":
            list(expected_if_true),

        "would_weaken":
            list(would_weaken),

        "review_by":
            (
                review_by.isoformat()
                if review_by is not None
                else None
            ),

        "evaluations":
            [],
    }

    ledger["hypotheses"].append(
        record
    )

    _write_ledger(
        ledger,
        memory_path,
    )

    return record


def append_hypothesis_evaluation(
    *,
    hypothesis_id: str,
    review_date: date,
    status: str,
    evidence: list[str],
    rationale: str,
    confidence: str | None = None,
    path: Path | None = None,
) -> dict[str, Any]:
    """
    Append a dated evaluation without modifying the
    original hypothesis record.
    """

    if status not in ALLOWED_STATUSES:
        raise ValueError(
            f"Unsupported hypothesis status: {status}"
        )

    memory_path = (
        path
        if path is not None
        else DEFAULT_HYPOTHESIS_PATH
    )

    ledger = _load_ledger(
        memory_path
    )

    for record in ledger["hypotheses"]:
        if record.get("id") != hypothesis_id:
            continue

        created_date = date.fromisoformat(
            record["created_date"]
        )

        if review_date < created_date:
            raise ValueError(
                "Hypothesis evaluation cannot predate "
                "hypothesis creation."
            )

        evaluations = record.setdefault(
            "evaluations",
            [],
        )

        if any(
            item.get("review_date")
            == review_date.isoformat()
            for item in evaluations
        ):
            raise ValueError(
                "Hypothesis already has an evaluation "
                f"for {review_date.isoformat()}."
            )

        evaluation = {
            "review_date":
                review_date.isoformat(),

            "status":
                status,

            "evidence":
                list(evidence),

            "rationale":
                rationale,

            "confidence":
                confidence,
        }

        evaluations.append(
            evaluation
        )

        evaluations.sort(
            key=lambda item:
                item["review_date"]
        )

        _write_ledger(
            ledger,
            memory_path,
        )

        return evaluation

    raise KeyError(
        f"Unknown hypothesis id: {hypothesis_id}"
    )


def load_active_hypotheses(
    replay_date: date,
    limit: int = 10,
    path: Path | None = None,
) -> list[dict[str, Any]]:
    """
    Return hypotheses available strictly before replay_date.

    Future hypotheses and future evaluations are excluded,
    preventing look-ahead during historical replay.
    """

    memory_path = (
        path
        if path is not None
        else DEFAULT_HYPOTHESIS_PATH
    )

    ledger = _load_ledger(
        memory_path
    )

    cutoff = replay_date.isoformat()

    visible: list[dict[str, Any]] = []

    for record in ledger["hypotheses"]:
        if (
            record.get("created_date", "")
            >= cutoff
        ):
            continue

        evaluations = [
            item
            for item in record.get(
                "evaluations",
                []
            )
            if (
                item.get(
                    "review_date",
                    "",
                )
                < cutoff
            )
        ]

        status = "active"

        if evaluations:
            status = evaluations[-1][
                "status"
            ]

        if status in TERMINAL_STATUSES:
            continue

        snapshot = dict(record)

        snapshot["evaluations"] = (
            evaluations
        )

        snapshot["current_status"] = (
            status
        )

        visible.append(
            snapshot
        )

    visible.sort(
        key=lambda item: (
            item["created_date"],
            item["id"],
        )
    )

    return visible[-limit:]
