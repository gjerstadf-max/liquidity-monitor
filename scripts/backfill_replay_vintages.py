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


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Capture the FRED/ALFRED vintages required "
            "for a historical liquidity replay."
        )
    )

    parser.add_argument(
        "--date",
        required=True,
        type=_parse_date,
        help="Replay date in YYYY-MM-DD format.",
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

    args = parser.parse_args()

    replay_date: date = args.date
    vintage_date = replay_date - timedelta(days=1)

    symbols = _symbols_for_replay_date(
        replay_date
    )

    print(
        "\nLIQUIDITY MONITOR — REPLAY VINTAGE BACKFILL"
    )
    print("=" * 72)
    print(f"Replay date:  {replay_date}")
    print(f"Vintage date: {vintage_date}")
    print()

    failures: list[tuple[str, Exception]] = []

    for symbol in symbols:
        print(f"{symbol}:")

        try:
            result = refresh_fred_vintage_series(
                definition=get_series(symbol),
                vintage_date=vintage_date,
                observation_count=args.count,
            )
        except Exception as exc:
            failures.append(
                (
                    symbol,
                    exc,
                )
            )
            print(f"  FAILED — {exc}")
            continue

        print(f"  {result}")

    print()
    print("=" * 72)

    if failures:
        print(
            f"Backfill completed with "
            f"{len(failures)} failure(s)."
        )

        for symbol, exc in failures:
            print(
                f"  {symbol}: "
                f"{type(exc).__name__}: {exc}"
            )

        raise SystemExit(1)

    print(
        f"Backfill completed successfully for "
        f"{len(symbols)} series."
    )


if __name__ == "__main__":
    main()
