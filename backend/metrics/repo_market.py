from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from statistics import mean, pstdev

from sqlalchemy import select

from backend.database.connection import get_session
from backend.database.models import Indicator, Observation


BP = Decimal("100")


# =============================================================
# DATA OBJECTS
# =============================================================


@dataclass(frozen=True)
class RepoMarketSnapshot:
    observation_date: date

    sofr: Decimal
    tgcr: Decimal
    bgcr: Decimal
    effr: Decimal
    obfr: Decimal

    sofr_effr_spread_bp: Decimal
    sofr_obfr_spread_bp: Decimal

    sofr_tgcr_spread_bp: Decimal
    sofr_bgcr_spread_bp: Decimal

    sofr_p25: Decimal
    sofr_p75: Decimal
    sofr_p99: Decimal

    sofr_iqr_bp: Decimal
    sofr_upper_tail_bp: Decimal

    sofr_volume_billions: Decimal


@dataclass(frozen=True)
class RepoMetricContext:
    current: Decimal

    average_20d: Decimal
    average_60d: Decimal

    minimum_60d: Decimal
    maximum_60d: Decimal

    percentile_60d: float
    zscore_60d: float


@dataclass(frozen=True)
class RepoMarketStatistics:
    observation_date: date

    observations_used: int

    sofr_effr: RepoMetricContext
    sofr_obfr: RepoMetricContext

    sofr_tgcr: RepoMetricContext
    sofr_bgcr: RepoMetricContext

    sofr_iqr: RepoMetricContext
    sofr_upper_tail: RepoMetricContext

    sofr_volume: RepoMetricContext


# =============================================================
# DATABASE HELPERS
# =============================================================


def _load_series(
    symbol: str,
) -> dict[date, Decimal]:

    with get_session() as session:

        rows = session.scalars(
            select(Observation)
            .join(Indicator)
            .where(
                Indicator.symbol == symbol
            )
            .order_by(
                Observation.observation_date.desc()
            )
        ).all()

    if not rows:

        raise RuntimeError(
            f"No observations found "
            f"for {symbol.upper()}."
        )

    return {
        row.observation_date: row.value
        for row in rows
    }


# =============================================================
# COMMON REPO HISTORY
# =============================================================


def _load_repo_history(
    as_of_date: date | None = None,
) -> list[RepoMarketSnapshot]:
    """
    Construct common daily repo observations.

    When as_of_date is supplied, observations after
    that date are excluded. This prevents look-ahead
    bias in historical replay.
    """

    sofr = _load_series("sofr")
    tgcr = _load_series("tgcr")
    bgcr = _load_series("bgcr")
    effr = _load_series("effr")
    obfr = _load_series("obfr")

    sofr_p25 = _load_series(
        "sofr_p25"
    )

    sofr_p75 = _load_series(
        "sofr_p75"
    )

    sofr_p99 = _load_series(
        "sofr_p99"
    )

    sofr_volume = _load_series(
        "sofr_volume"
    )


    common_dates = (
        set(sofr)
        & set(tgcr)
        & set(bgcr)
        & set(effr)
        & set(obfr)
        & set(sofr_p25)
        & set(sofr_p75)
        & set(sofr_p99)
        & set(sofr_volume)
    )


    if as_of_date is not None:

        common_dates = {
            observation_date
            for observation_date
            in common_dates
            if observation_date <= as_of_date
        }


    if not common_dates:

        raise RuntimeError(
            "No common repo-market "
            "observation dates found."
        )


    history: list[
        RepoMarketSnapshot
    ] = []


    for observation_date in sorted(
        common_dates,
        reverse=True,
    ):

        sofr_value = (
            sofr[observation_date]
        )

        tgcr_value = (
            tgcr[observation_date]
        )

        bgcr_value = (
            bgcr[observation_date]
        )

        effr_value = (
            effr[observation_date]
        )

        obfr_value = (
            obfr[observation_date]
        )

        p25 = (
            sofr_p25[observation_date]
        )

        p75 = (
            sofr_p75[observation_date]
        )

        p99 = (
            sofr_p99[observation_date]
        )

        volume = (
            sofr_volume[observation_date]
        )


        history.append(
            RepoMarketSnapshot(
                observation_date=
                    observation_date,

                sofr=
                    sofr_value,

                tgcr=
                    tgcr_value,

                bgcr=
                    bgcr_value,

                effr=
                    effr_value,

                obfr=
                    obfr_value,

                sofr_effr_spread_bp=(
                    sofr_value
                    - effr_value
                ) * BP,

                sofr_obfr_spread_bp=(
                    sofr_value
                    - obfr_value
                ) * BP,

                sofr_tgcr_spread_bp=(
                    sofr_value
                    - tgcr_value
                ) * BP,

                sofr_bgcr_spread_bp=(
                    sofr_value
                    - bgcr_value
                ) * BP,

                sofr_p25=
                    p25,

                sofr_p75=
                    p75,

                sofr_p99=
                    p99,

                sofr_iqr_bp=(
                    p75
                    - p25
                ) * BP,

                sofr_upper_tail_bp=(
                    p99
                    - sofr_value
                ) * BP,

                sofr_volume_billions=
                    volume,
            )
        )


    return history


# =============================================================
# STATISTICAL CONTEXT
# =============================================================


def _metric_context(
    values: list[Decimal],
) -> RepoMetricContext:

    if len(values) < 2:

        raise RuntimeError(
            "At least two observations "
            "are required."
        )


    current = values[0]

    last_20 = values[:20]
    last_60 = values[:60]


    average_20 = (
        sum(
            last_20,
            Decimal("0"),
        )
        / Decimal(
            len(last_20)
        )
    )


    average_60 = (
        sum(
            last_60,
            Decimal("0"),
        )
        / Decimal(
            len(last_60)
        )
    )


    minimum = min(
        last_60
    )

    maximum = max(
        last_60
    )


    observations_at_or_below = sum(
        1
        for value in last_60
        if value <= current
    )


    percentile = (
        observations_at_or_below
        / len(last_60)
        * 100
    )


    float_values = [
        float(value)
        for value in last_60
    ]


    historical_mean = mean(
        float_values
    )

    historical_std = pstdev(
        float_values
    )


    if historical_std == 0:

        zscore = 0.0

    else:

        zscore = (
            float(current)
            - historical_mean
        ) / historical_std


    return RepoMetricContext(
        current=current,

        average_20d=
            average_20,

        average_60d=
            average_60,

        minimum_60d=
            minimum,

        maximum_60d=
            maximum,

        percentile_60d=
            percentile,

        zscore_60d=
            zscore,
    )


# =============================================================
# PUBLIC FUNCTIONS
# =============================================================


def latest_repo_market_snapshot(
    as_of_date: date | None = None,
) -> RepoMarketSnapshot:

    history = _load_repo_history(
        as_of_date=as_of_date
    )

    return history[0]


def repo_market_statistics(
    lookback: int = 60,
    as_of_date: date | None = None,
) -> RepoMarketStatistics:
    """
    Historical statistics using only observations
    available on or before as_of_date.

    If as_of_date is None, the latest data are used.
    """

    if lookback < 20:

        raise ValueError(
            "lookback must be "
            "at least 20"
        )


    history = _load_repo_history(
        as_of_date=as_of_date
    )


    selected = (
        history[:lookback]
    )


    if len(selected) < 20:

        raise RuntimeError(
            "At least 20 common repo-market "
            "observations are required."
        )


    return RepoMarketStatistics(
        observation_date=
            selected[0].observation_date,

        observations_used=
            len(selected),

        sofr_effr=
            _metric_context(
                [
                    item.sofr_effr_spread_bp
                    for item in selected
                ]
            ),

        sofr_obfr=
            _metric_context(
                [
                    item.sofr_obfr_spread_bp
                    for item in selected
                ]
            ),

        sofr_tgcr=
            _metric_context(
                [
                    item.sofr_tgcr_spread_bp
                    for item in selected
                ]
            ),

        sofr_bgcr=
            _metric_context(
                [
                    item.sofr_bgcr_spread_bp
                    for item in selected
                ]
            ),

        sofr_iqr=
            _metric_context(
                [
                    item.sofr_iqr_bp
                    for item in selected
                ]
            ),

        sofr_upper_tail=
            _metric_context(
                [
                    item.sofr_upper_tail_bp
                    for item in selected
                ]
            ),

        sofr_volume=
            _metric_context(
                [
                    item.sofr_volume_billions
                    for item in selected
                ]
            ),
    )


# =============================================================
# CURRENT-DATE DISPLAY
# =============================================================


def _print_context(
    name: str,
    context: RepoMetricContext,
    units: str = "bp",
) -> None:

    print()
    print(name)

    print(
        f"  Current:       "
        f"{context.current:.2f} {units}"
    )

    print(
        f"  20-day avg:    "
        f"{context.average_20d:.2f} {units}"
    )

    print(
        f"  60-day avg:    "
        f"{context.average_60d:.2f} {units}"
    )

    print(
        f"  60-day range:  "
        f"{context.minimum_60d:.2f} "
        f"to "
        f"{context.maximum_60d:.2f} "
        f"{units}"
    )

    print(
        f"  Percentile:    "
        f"{context.percentile_60d:.0f}"
    )

    print(
        f"  Z-score:       "
        f"{context.zscore_60d:+.2f}"
    )


def print_repo_market_diagnostics() -> None:

    snapshot = (
        latest_repo_market_snapshot()
    )

    statistics = (
        repo_market_statistics()
    )


    print()
    print(
        "Liquidity Monitor — "
        "Repo Market Internals"
    )

    print("=" * 72)

    print()
    print(
        f"Observation Date: "
        f"{snapshot.observation_date}"
    )


    print()
    print("Reference Rates")
    print("-" * 72)

    print(
        f"SOFR: {snapshot.sofr:.2f}%"
    )

    print(
        f"TGCR: {snapshot.tgcr:.2f}%"
    )

    print(
        f"BGCR: {snapshot.bgcr:.2f}%"
    )

    print(
        f"EFFR: {snapshot.effr:.2f}%"
    )

    print(
        f"OBFR: {snapshot.obfr:.2f}%"
    )


    print()
    print("Historical Diagnostics")
    print("-" * 72)


    _print_context(
        "SOFR - EFFR",
        statistics.sofr_effr,
    )

    _print_context(
        "SOFR - OBFR",
        statistics.sofr_obfr,
    )

    _print_context(
        "SOFR - TGCR",
        statistics.sofr_tgcr,
    )

    _print_context(
        "SOFR - BGCR",
        statistics.sofr_bgcr,
    )

    _print_context(
        "SOFR Interquartile Range",
        statistics.sofr_iqr,
    )

    _print_context(
        "SOFR 99th Percentile - Median",
        statistics.sofr_upper_tail,
    )

    _print_context(
        "SOFR Transaction Volume",
        statistics.sofr_volume,
        units="$B",
    )


if __name__ == "__main__":
    print_repo_market_diagnostics()