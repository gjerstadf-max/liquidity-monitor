from __future__ import annotations

import argparse
from datetime import date

from backend.assessments.engine import (
    build_liquidity_assessment,
)
from backend.commentary.interpretation_context import (
    build_interpretation_context,
)
from backend.commentary.liquidity_interpreter import (
    interpret_liquidity,
)
from backend.commentary.replay_memory import (
    load_recent_replay_history,
    record_replay_day,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Replay the Liquidity Monitor assessment "
            "as of a historical date."
        )
    )

    parser.add_argument(
        "--date",
        required=True,
        help="Historical replay date in YYYY-MM-DD format.",
    )

    parser.add_argument(
        "--interpret",
        action="store_true",
        help=(
            "Generate an LLM interpretation of the "
            "historical replay packet."
        ),
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    try:
        replay_date = date.fromisoformat(
            args.date
        )
    except ValueError as exc:
        raise SystemExit(
            "--date must use YYYY-MM-DD format"
        ) from exc

    assessment = build_liquidity_assessment(
        as_of_date=replay_date
    )

    print()
    print(
        "LIQUIDITY MONITOR — HISTORICAL REPLAY"
    )
    print("=" * 76)
    print(
        f"Replay date: {replay_date.isoformat()}"
    )

    print()
    print("OVERALL")
    print(
        f"Verdict: {assessment.overall_verdict}"
    )
    print(
        f"Confidence: {assessment.confidence}"
    )
    print(
        f"Summary: {assessment.summary}"
    )

    print()
    print("FACTORS")
    print("-" * 76)

    for factor in assessment.factors:
        print()
        print(
            factor.display_name.upper()
        )
        print(
            f"Verdict: "
            f"{factor.assessment.verdict}"
        )
        print(
            f"Confidence: "
            f"{factor.assessment.confidence}"
        )
        print(
            f"Summary: "
            f"{factor.assessment.summary}"
        )

    print()
    print("=" * 76)

    if not args.interpret:
        return

    packet = build_interpretation_context(
        assessment=assessment,
        replay_date=replay_date,
    )
    recent_history = (
    load_recent_replay_history(
        replay_date=replay_date,
        limit=10,
    )
    )
    packet["recent_history"] = (
        recent_history
    )
    interpretation = interpret_liquidity(
        packet=packet
    )

    record_replay_day(
        packet=packet
    )
    
    print()
    print("HISTORICAL INTERPRETATION")
    print("=" * 76)

    print()
    print(interpretation.headline)

    print()
    print(interpretation.overall_comment)

    if interpretation.primary_drivers:
        print()
        print("PRIMARY DRIVERS")

        for item in interpretation.primary_drivers:
            print(f"- {item}")

    if interpretation.counter_evidence:
        print()
        print("WHY THIS IS NOT WORSE")

        for item in interpretation.counter_evidence:
            print(f"- {item}")

    if interpretation.what_to_watch:
        print()
        print("WHAT WOULD CHANGE THE VIEW")

        for item in interpretation.what_to_watch:
            print(f"- {item}")

    print()
    print(
        f"Model: {interpretation.model}"
    )


if __name__ == "__main__":
    main()
