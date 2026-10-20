from __future__ import annotations

import argparse

from datetime import date, timedelta

from backend.catalog.series import get_series

from backend.services.provider_refresh import (
    refresh_fred_vintage_series,
)


IORB_START_DATE = date(2021, 7, 29)


BASE_REPLAY_VINTAGE_SYMBOLS = (
    "treasury_3m",
    "cp_aa_nonfinancial_30d",
    "cp_a2p2_nonfinancial_30d",
    "bank_deposits_small",
    "bank_deposits_large",
    "bank_large_time_deposits_small",
    "central_bank_liquidity_swaps",
)


def _parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            "Date must use YYYY-MM-DD format."
        ) from exc


def _symbols_for_replay_date(
    replay_date: date,
) -> tuple[str, ...]:
    administered_rate_symbol = (
        "iorb"
        if replay_date >= IORB_START_DATE
        else "ioer"
    )

    return (
        *BASE_REPLAY_VINTAGE_SYMBOLS,
        administered_rate_symbol,
    )


def _replay_dates(
    start_date: date,
    end_date: date,
):
    current_date = start_date

    while current_date <= end_date:
        yield current_date
        current_date += timedelta(days=1)


def _backfill_replay_date(
    replay_date: date,
    observation_count: int,
) -> list[tuple[date, str, Exception]]:
    vintage_date = replay_date - timedelta(days=1)

    symbols = _symbols_for_replay_date(
        replay_date
    )

    print()
    print("-" * 72)
    print(f"Replay date:  {replay_date}")
    print(f"Vintage date: {vintage_date}")
    print("-" * 72)

    failures: list[
        tuple[date, str, Exception]
    ] = []

    for symbol in symbols:
        print(f"{symbol}:")

        try:
            result = refresh_fred_vintage_series(
                definition=get_series(symbol),
                vintage_date=vintage_date,
                observation_count=observation_count,
            )
        except Exception as exc:
            failures.append(
                (
                    replay_date,
                    symbol,
                    exc,
                )
            )

            print(f"  FAILED — {exc}")
            continue

        print(f"  {result}")

    return failures


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Capture the FRED/ALFRED vintages required "
            "for historical liquidity replay."
        )
    )

    date_group = parser.add_mutually_exclusive_group(
        required=True
    )

    date_group.add_argument(
        "--date",
        type=_parse_date,
        help=(
            "Single replay date in YYYY-MM-DD format."
        ),
    )

    date_group.add_argument(
        "--start",
        type=_parse_date,
        help=(
            "First replay date in YYYY-MM-DD format."
        ),
    )

    parser.add_argument(
        "--end",
        type=_parse_date,
        help=(
            "Last replay date in YYYY-MM-DD format. "
            "Required with --start."
        ),
    )

    parser.add_argument(
        "--count",
        type=int,
        default=100,
        help=(
            "Number of observations to request for each "
            "ALFRED series. Default: 100."
        ),
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.date is not None:
        if args.end is not None:
            raise SystemExit(
                "--end cannot be used with --date"
            )

        start_date = args.date
        end_date = args.date

    else:
        if args.end is None:
            raise SystemExit(
                "--end is required when using --start"
            )

        start_date = args.start
        end_date = args.end

        if end_date < start_date:
            raise SystemExit(
                "--end must be on or after --start"
            )

    print()
    print(
        "LIQUIDITY MONITOR — REPLAY VINTAGE BACKFILL"
    )
    print("=" * 72)
    print(
        f"Replay range: {start_date} through {end_date}"
    )

    failures: list[
        tuple[date, str, Exception]
    ] = []

    replay_count = 0

    for replay_date in _replay_dates(
        start_date,
        end_date,
    ):
        replay_count += 1

        failures.extend(
            _backfill_replay_date(
                replay_date=replay_date,
                observation_count=args.count,
            )
        )

    print()
    print("=" * 72)

    if failures:
        print(
            f"Backfill completed with "
            f"{len(failures)} failure(s)."
        )

        for replay_date, symbol, exc in failures:
            print(
                f"  {replay_date} | {symbol}: "
                f"{type(exc).__name__}: {exc}"
            )

        raise SystemExit(1)

    print(
        f"Backfill completed successfully for "
        f"{replay_count} replay date(s)."
    )


if __name__ == "__main__":
    main()