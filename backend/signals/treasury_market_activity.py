from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from backend.metrics.treasury_market_activity import (
    treasury_auction_absorption_statistics,
    treasury_bill_supply_statistics,
    treasury_market_spread_statistics,
)
from backend.signals.models import Signal


# =============================================================
# TREASURY MARKET ACTIVITY SIGNAL V1
# =============================================================
#
# Philosophy:
#
# Treasury Market Activity asks whether Treasury bill supply
# is creating an unusual absorption burden and whether the
# market is having difficulty absorbing that supply.
#
# Core dimensions:
#
#   1. Supply Load
#      - trailing 28-day gross bill issuance
#
#   2. Auction Absorption
#      - tenor-normalized bid-to-cover
#      - tenor-normalized primary-dealer take-down
#
# Supporting context:
#
#   3. Treasury 3M - IORB
#
# High supply alone warrants monitoring, not a stress signal.
# The strongest warning comes when heavy supply and weak
# auction absorption occur together.
#
# =============================================================


SUPPLY_WATCH_Z = 1.50

ABSORPTION_WATCH_Z = 1.00
ABSORPTION_WARNING_Z = 1.50
ABSORPTION_CRITICAL_Z = 2.50

COMBINED_SUPPLY_WARNING_Z = 1.50
COMBINED_ABSORPTION_WARNING_Z = 1.00

COMBINED_SUPPLY_CRITICAL_Z = 2.00
COMBINED_ABSORPTION_CRITICAL_Z = 1.50


# =============================================================
# DIAGNOSTICS
# =============================================================


@dataclass(frozen=True)
class TreasuryMarketActivityDiagnostics:
    observation_date: date

    gross_bill_supply_billions: float
    regular_bill_supply_billions: float
    cmb_supply_billions: float

    supply_percentile_52w: float
    supply_z_52w: float

    absorption_pressure: float
    absorption_percentile: float
    absorption_z: float

    auctions_used: int
    auction_offering_billions: float

    treasury_iorb_spread_bp: float
    treasury_iorb_percentile: float
    treasury_iorb_z: float


# =============================================================
# BUILD DIAGNOSTICS
# =============================================================


def build_treasury_market_activity_diagnostics(
    as_of_date: date | None = None,
) -> TreasuryMarketActivityDiagnostics:
    """
    Build Factor #5 diagnostics using only information
    available on or before as_of_date.
    """

    supply = treasury_bill_supply_statistics(
        window_days=28,
        as_of_date=as_of_date,
    )

    absorption = treasury_auction_absorption_statistics(
        window_days=28,
        lookback=52,
        minimum_history=20,
        as_of_date=as_of_date,
    )

    pricing = treasury_market_spread_statistics(
        lookback=60,
        as_of_date=as_of_date,
    )

    return TreasuryMarketActivityDiagnostics(
        observation_date=supply.observation_date,

        gross_bill_supply_billions=(
            supply.gross_supply_billions
        ),

        regular_bill_supply_billions=(
            supply.regular_supply_billions
        ),

        cmb_supply_billions=(
            supply.cmb_supply_billions
        ),

        supply_percentile_52w=(
            supply.trailing_52_week_percentile
        ),

        supply_z_52w=(
            supply.trailing_52_week_zscore
        ),

        absorption_pressure=(
            absorption.current_pressure
        ),

        absorption_percentile=(
            absorption.historical_percentile
        ),

        absorption_z=(
            absorption.historical_zscore
        ),

        auctions_used=(
            absorption.auctions_used
        ),

        auction_offering_billions=(
            absorption.offering_amount_billions
        ),

        treasury_iorb_spread_bp=(
            pricing.current_spread_bp
        ),

        treasury_iorb_percentile=(
            pricing.percentile
        ),

        treasury_iorb_z=(
            pricing.zscore
        ),
    )


# =============================================================
# SIGNAL
# =============================================================


def evaluate_treasury_market_activity_signal(
    as_of_date: date | None = None,
) -> Signal:
    """
    Evaluate Treasury Market Activity Signal V1.

    High supply alone can trigger Watch.

    Weak absorption is more important economically and
    can independently trigger Warning or Critical.

    Simultaneously elevated supply and weak absorption
    escalate more quickly.

    Treasury 3M - IORB is supporting context only and
    does not independently determine severity.
    """

    diagnostics = (
        build_treasury_market_activity_diagnostics(
            as_of_date=as_of_date
        )
    )

    supply_z = (
        diagnostics.supply_z_52w
    )

    absorption_z = (
        diagnostics.absorption_z
    )

    supply_pct = (
        diagnostics.supply_percentile_52w
    )

    absorption_pct = (
        diagnostics.absorption_percentile
    )

    gross_supply = (
        diagnostics.gross_bill_supply_billions
    )

    cmb_supply = (
        diagnostics.cmb_supply_billions
    )

    # =========================================================
    # CRITICAL
    # =========================================================

    if (
        absorption_z >= ABSORPTION_CRITICAL_Z
        or (
            supply_z
            >= COMBINED_SUPPLY_CRITICAL_Z
            and absorption_z
            >= COMBINED_ABSORPTION_CRITICAL_Z
        )
    ):
        return Signal(
            category="Treasury Market Activity",
            title=(
                "Treasury auction absorption "
                "is materially stressed"
            ),
            severity="Critical",
            message=(
                f"Gross Treasury bill supply over the "
                f"past 28 days is ${gross_supply:,.0f}B, "
                f"at the {supply_pct:.0f}th percentile "
                f"of its trailing 52-week distribution "
                f"with a z-score of {supply_z:+.2f}. "
                f"Auction absorption pressure is at the "
                f"{absorption_pct:.0f}th percentile of "
                f"its historical distribution with a "
                f"z-score of {absorption_z:+.2f}. "
                "Treasury supply and auction demand are "
                "showing broad evidence of market pressure."
            ),
        )

    # =========================================================
    # WARNING — HIGH SUPPLY + WEAK ABSORPTION
    # =========================================================

    if (
        supply_z
        >= COMBINED_SUPPLY_WARNING_Z
        and absorption_z
        >= COMBINED_ABSORPTION_WARNING_Z
    ):
        return Signal(
            category="Treasury Market Activity",
            title=(
                "Heavy Treasury supply is meeting "
                "weaker auction absorption"
            ),
            severity="Warning",
            message=(
                f"Gross Treasury bill supply over the "
                f"past 28 days is ${gross_supply:,.0f}B, "
                f"at the {supply_pct:.0f}th percentile "
                f"of its trailing 52-week distribution "
                f"with a z-score of {supply_z:+.2f}. "
                f"Auction absorption pressure is at the "
                f"{absorption_pct:.0f}th percentile with "
                f"a z-score of {absorption_z:+.2f}. "
                "Both supply load and auction absorption "
                "are deteriorating simultaneously."
            ),
        )

    # =========================================================
    # WARNING — WEAK ABSORPTION
    # =========================================================

    if (
        absorption_z
        >= ABSORPTION_WARNING_Z
    ):
        return Signal(
            category="Treasury Market Activity",
            title=(
                "Treasury auction absorption "
                "is unusually weak"
            ),
            severity="Warning",
            message=(
                f"Auction absorption pressure is at the "
                f"{absorption_pct:.0f}th percentile of "
                f"its historical distribution with a "
                f"z-score of {absorption_z:+.2f}. "
                f"Gross bill supply over the past 28 days "
                f"is ${gross_supply:,.0f}B with a "
                f"trailing 52-week z-score of "
                f"{supply_z:+.2f}. "
                "Weak auction demand and/or elevated "
                "primary-dealer take-down warrant closer "
                "monitoring."
            ),
        )

    # =========================================================
    # WATCH — ABSORPTION
    # =========================================================

    if (
        absorption_z
        >= ABSORPTION_WATCH_Z
    ):
        return Signal(
            category="Treasury Market Activity",
            title=(
                "Treasury auction absorption "
                "warrants monitoring"
            ),
            severity="Watch",
            message=(
                f"Auction absorption pressure is at the "
                f"{absorption_pct:.0f}th percentile of "
                f"its historical distribution with a "
                f"z-score of {absorption_z:+.2f}. "
                f"Gross bill supply over the past 28 days "
                f"is ${gross_supply:,.0f}B with a "
                f"trailing 52-week z-score of "
                f"{supply_z:+.2f}. "
                "Auction demand is somewhat weaker than "
                "normal, but current evidence does not "
                "indicate broad Treasury-market stress."
            ),
        )

    # =========================================================
    # WATCH — HIGH SUPPLY / ORDERLY ABSORPTION
    # =========================================================

    if (
        supply_z
        >= SUPPLY_WATCH_Z
    ):
        cmb_text = ""

        if cmb_supply > 0:
            cmb_text = (
                f" Cash Management Bills account for "
                f"${cmb_supply:,.0f}B of current "
                f"28-day supply."
            )

        return Signal(
            category="Treasury Market Activity",
            title=(
                "Treasury bill supply is unusually "
                "heavy but being absorbed normally"
            ),
            severity="Watch",
            message=(
                f"Gross Treasury bill supply over the "
                f"past 28 days is ${gross_supply:,.0f}B, "
                f"at the {supply_pct:.0f}th percentile "
                f"of its trailing 52-week distribution "
                f"with a z-score of {supply_z:+.2f}. "
                f"Auction absorption pressure is at the "
                f"{absorption_pct:.0f}th percentile with "
                f"a z-score of {absorption_z:+.2f}. "
                "The issuance burden is unusually high, "
                "but auction results do not currently "
                "indicate difficulty absorbing the supply."
                f"{cmb_text}"
            ),
        )

    # =========================================================
    # NORMAL
    # =========================================================

    return Signal(
        category="Treasury Market Activity",
        title=(
            "Treasury supply and auction absorption "
            "remain orderly"
        ),
        severity="Normal",
        message=(
            f"Gross Treasury bill supply over the past "
            f"28 days is ${gross_supply:,.0f}B, at the "
            f"{supply_pct:.0f}th percentile of its "
            f"trailing 52-week distribution with a "
            f"z-score of {supply_z:+.2f}. "
            f"Auction absorption pressure is at the "
            f"{absorption_pct:.0f}th percentile with a "
            f"z-score of {absorption_z:+.2f}. "
            f"The 3-month Treasury yield is "
            f"{diagnostics.treasury_iorb_spread_bp:+.0f} "
            f"bp relative to IORB, with a recent z-score "
            f"of {diagnostics.treasury_iorb_z:+.2f}. "
            "Current Treasury bill issuance and auction "
            "demand do not indicate unusual market pressure."
        ),
    )


# =============================================================
# TERMINAL DISPLAY
# =============================================================


def print_treasury_market_activity_signal(
    as_of_date: date | None = None,
) -> None:
    diagnostics = (
        build_treasury_market_activity_diagnostics(
            as_of_date=as_of_date
        )
    )

    signal = (
        evaluate_treasury_market_activity_signal(
            as_of_date=as_of_date
        )
    )

    print()
    print(
        "TREASURY MARKET ACTIVITY SIGNAL"
    )
    print(
        "=" * 78
    )

    print()
    print(
        "SUPPLY LOAD"
    )
    print(
        "-" * 78
    )

    print(
        f"Gross 28-day supply: "
        f"${diagnostics.gross_bill_supply_billions:,.1f}B"
    )

    print(
        f"52-week percentile:  "
        f"{diagnostics.supply_percentile_52w:.1f}"
    )

    print(
        f"52-week z-score:      "
        f"{diagnostics.supply_z_52w:+.2f}"
    )

    print()
    print(
        "AUCTION ABSORPTION"
    )
    print(
        "-" * 78
    )

    print(
        f"Pressure:             "
        f"{diagnostics.absorption_pressure:+.2f}"
    )

    print(
        f"Historical percentile: "
        f"{diagnostics.absorption_percentile:.1f}"
    )

    print(
        f"Historical z-score:   "
        f"{diagnostics.absorption_z:+.2f}"
    )

    print()
    print(
        "RELATIVE PRICING — SUPPORTING"
    )
    print(
        "-" * 78
    )

    print(
        f"3M Treasury - IORB:   "
        f"{diagnostics.treasury_iorb_spread_bp:+.1f} bp"
    )

    print(
        f"Recent percentile:    "
        f"{diagnostics.treasury_iorb_percentile:.1f}"
    )

    print(
        f"Recent z-score:       "
        f"{diagnostics.treasury_iorb_z:+.2f}"
    )

    print()
    print(
        "SIGNAL"
    )
    print(
        "-" * 78
    )

    print(
        f"Severity: {signal.severity}"
    )

    print(
        f"Title:    {signal.title}"
    )

    print()
    print(
        signal.message
    )
    print()


if __name__ == "__main__":
    print_treasury_market_activity_signal()
