from __future__ import annotations

import argparse
from datetime import date

from backend.assessments.engine import (
    build_liquidity_assessment,
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


if __name__ == "__main__":
    main()
