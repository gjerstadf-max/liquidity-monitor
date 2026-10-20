from __future__ import annotations

import argparse
from datetime import date, timedelta

from backend.assessments.engine import (
    build_liquidity_assessment,
)


def _parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            "Date must use YYYY-MM-DD format."
        ) from exc


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run deterministic Liquidity Monitor assessments "
            "across a historical date range."
        )
    )
    parser.add_argument(
        "--start",
        required=True,
        type=_parse_date,
        help="First replay date in YYYY-MM-DD format.",
    )
    parser.add_argument(
        "--end",
        required=True,
        type=_parse_date,
        help="Last replay date in YYYY-MM-DD format.",
    )
    return parser.parse_args()


def _factor_verdicts(assessment) -> dict[str, str]:
    return {
        factor.key: factor.assessment.verdict
        for factor in assessment.factors
    }


def main() -> None:
    args = parse_args()

    if args.end < args.start:
        raise SystemExit(
            "--end must be on or after --start"
        )

    headers = (
        "DATE",
        "OVERALL",
        "FUNDING",
        "SYSTEM",
        "REPO",
        "TREAS-INT",
        "TREAS-MKT",
        "CP",
        "BANK",
        "GLOBAL-$",
    )

    rows: list[tuple[str, ...]] = []

    current_date = args.start

    while current_date <= args.end:
        assessment = build_liquidity_assessment(
            as_of_date=current_date
        )

        factors = _factor_verdicts(assessment)

        rows.append(
            (
                current_date.isoformat(),
                assessment.overall_verdict,
                factors.get(
                    "funding",
                    "-",
                ),
                factors.get(
                    "system_liquidity",
                    "-",
                ),
                factors.get(
                    "repo_market",
                    "-",
                ),
                factors.get(
                    "treasury_intermediation",
                    "-",
                ),
                factors.get(
                    "treasury_market_activity",
                    "-",
                ),
                factors.get(
                    "commercial_paper",
                    "-",
                ),
                factors.get(
                    "bank_funding",
                    "-",
                ),
                factors.get(
                    "global_dollar_funding",
                    "-",
                ),
            )
        )

        current_date += timedelta(days=1)

    widths = [
        max(
            len(headers[index]),
            max(
                len(row[index])
                for row in rows
            ),
        )
        for index in range(len(headers))
    ]

    def format_row(row: tuple[str, ...]) -> str:
        return "  ".join(
            value.ljust(widths[index])
            for index, value in enumerate(row)
        )

    print()
    print(
        "LIQUIDITY MONITOR — HISTORICAL RANGE REPLAY"
    )
    print("=" * 120)
    print(
        f"Range: {args.start.isoformat()} "
        f"through {args.end.isoformat()}"
    )
    print()
    print(format_row(headers))
    print(
        "  ".join(
            "-" * width
            for width in widths
        )
    )

    for row in rows:
        print(format_row(row))

    print()
    print(
        f"{len(rows)} replay date(s) evaluated."
    )


if __name__ == "__main__":
    main()
