from __future__ import annotations

import json

from datetime import date,timedelta

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

def _add_business_days(
    start_date: date,
    business_days: int,
) -> date:
    current = start_date
    added = 0

    while added < business_days:
        current += timedelta(days=1)

        if current.weekday() < 5:
            added += 1

    return current

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
    for existing in ledger["hypotheses"]:
        if (
            existing.get("created_date")
            == created_date.isoformat()
            and existing.get(
                "hypothesis",
                "",
            ).strip()
            == hypothesis.strip()
        ):
            return existing

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

        for existing in evaluations:
            if (
                existing.get("review_date")
                != review_date.isoformat()
            ):
                continue

            same_evaluation = (
                existing.get("status")
                == status
                and existing.get("evidence")
                == list(evidence)
                and existing.get("rationale")
                == rationale
                and existing.get("confidence")
                == confidence
            )

            if same_evaluation:
                return existing

            raise ValueError(
                "Hypothesis already has a different "
                "evaluation for "
                f"{review_date.isoformat()}."
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
def apply_hypothesis_outputs(
    *,
    replay_date: date,
    proposed_hypotheses: list[dict[str, Any]],
    hypothesis_evaluations: list[dict[str, Any]],
    visible_hypotheses: list[dict[str, Any]],
    path: Path | None = None,
) -> dict[str, int]:
    """
    Validate and persist the model's hypothesis outputs.

    The model may evaluate only hypotheses that were
    visible in the replay packet for this date.
    """

    visible_ids = {
        item["id"]
        for item in visible_hypotheses
        if item.get("id")
    }

    evaluated = 0
    created = 0

    for evaluation in hypothesis_evaluations:
        hypothesis_id = evaluation[
            "hypothesis_id"
        ]

        if hypothesis_id not in visible_ids:
            raise ValueError(
                "Model attempted to evaluate "
                "a hypothesis that was not visible "
                f"on {replay_date.isoformat()}: "
                f"{hypothesis_id}"
            )

        append_hypothesis_evaluation(
            hypothesis_id=hypothesis_id,
            review_date=replay_date,
            status=evaluation["status"],
            evidence=evaluation["evidence"],
            rationale=evaluation["rationale"],
            confidence=evaluation.get(
                "confidence"
            ),
            path=path,
        )

        evaluated += 1

    for hypothesis in proposed_hypotheses:
        review_after_days = int(
            hypothesis[
                "review_after_days"
            ]
        )

        review_by = _add_business_days(
            replay_date,
            review_after_days,
        )

        create_hypothesis(
            created_date=replay_date,
            hypothesis=
                hypothesis["hypothesis"],
            confidence=
                hypothesis["confidence"],
            supporting_evidence=
                hypothesis[
                    "supporting_evidence"
                ],
            expected_if_true=
                hypothesis[
                    "expected_if_true"
                ],
            would_weaken=
                hypothesis[
                    "would_weaken"
                ],
            review_by=review_by,
            path=path,
        )

        created += 1

    return {
        "created": created,
        "evaluated": evaluated,
    }
