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
from backend.commentary.replay_hypotheses import (
    apply_hypothesis_outputs,
    load_active_hypotheses,
)
from backend.commentary.liquidity_interpreter import (
    _persistent_non_normal_factors,
    interpret_liquidity,
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
    active_hypotheses = (
        load_active_hypotheses(
            replay_date=replay_date,
            limit=10,
        )
    )
    packet["active_hypotheses"] = (
        active_hypotheses
    )
    packet["persistent_non_normal_factors"] = (
    _persistent_non_normal_factors(
        packet
    )
)
    interpretation = interpret_liquidity(
        packet=packet
    )
    hypothesis_updates = (
        apply_hypothesis_outputs(
            replay_date=replay_date,
            proposed_hypotheses=
                interpretation.proposed_hypotheses,
            hypothesis_evaluations=
                interpretation.hypothesis_evaluations,
            visible_hypotheses=
                active_hypotheses,
        )
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

    if interpretation.proposed_hypotheses:
        print()
        print("PROPOSED HYPOTHESES")

        for index, hypothesis in enumerate(
            interpretation.proposed_hypotheses,
            start=1,
        ):
            print()
            print(
                f"Hypothesis {index}: "
                f"{hypothesis['hypothesis']}"
            )

            print(
                f"Confidence: "
                f"{hypothesis['confidence']}"
            )

            print("Supporting evidence:")
            for item in hypothesis[
                "supporting_evidence"
            ]:
                print(f"  - {item}")

            print("Expected if true:")
            for item in hypothesis[
                "expected_if_true"
            ]:
                print(f"  - {item}")

            print("Would weaken:")
            for item in hypothesis[
                "would_weaken"
            ]:
                print(f"  - {item}")

            print(
                "Review after: "
                f"{hypothesis['review_after_days']} "
                "day(s)"
            )

    if interpretation.hypothesis_evaluations:
        print()
        print("HYPOTHESIS EVALUATIONS")

        for evaluation in (
            interpretation.hypothesis_evaluations
        ):
            print()
            print(
                f"{evaluation['hypothesis_id']}: "
                f"{evaluation['status']}"
            )

            print(
                f"Confidence: "
                f"{evaluation['confidence']}"
            )

            print(
                f"Rationale: "
                f"{evaluation['rationale']}"
            )

            print("Evidence:")
            for item in evaluation["evidence"]:
                print(f"  - {item}")

    print()
    print(
        f"Model: {interpretation.model}"
    )


if __name__ == "__main__":
    main()
