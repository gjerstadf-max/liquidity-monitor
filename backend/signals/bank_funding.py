from __future__ import annotations

from datetime import date

from backend.metrics.bank_funding import (
    BankFundingStatistics,
    bank_funding_statistics,
)
from backend.signals.models import Signal


# =============================================================
# PRIMARY CREDIT THRESHOLDS
# =============================================================

PRIMARY_WATCH_PCT = 0.10
PRIMARY_CONFIRMABLE_WARNING_PCT = 0.25
PRIMARY_WARNING_PCT = 0.50
PRIMARY_CRITICAL_PCT = 0.75


# =============================================================
# DEPOSIT-STRESS THRESHOLDS
# =============================================================

SMALL_BANK_DEPOSIT_STRESS_PCT = -1.00
SMALL_BANK_DEPOSIT_SEVERE_PCT = -2.00

MIGRATION_CONFIRMATION_PP = -2.50
MIGRATION_SEVERE_PP = -1.50


# =============================================================
# CORE SIGNAL
# =============================================================


def evaluate_bank_funding_statistics(
    stats: BankFundingStatistics,
) -> Signal:
    """
    Bank Funding Stress signal.

    Primary credit relative to domestic-bank deposits is
    the anchor measure of acute bank liquidity demand.

    Deposit behavior provides confirmation and helps
    identify deposit-flight / migration episodes.

    Deposit behavior alone cannot generate Warning or
    Critical.
    """

    primary_ratio = (
        stats.primary_credit_pct_deposits
    )

    small_4w = (
        stats.small_bank_deposits_4w_pct
    )

    migration_4w = (
        stats.small_minus_large_4w_pp
    )

    # =========================================================
    # SUPPORTING DEPOSIT DIAGNOSTICS
    # =========================================================

    actual_deposit_stress = (
        small_4w
        <= SMALL_BANK_DEPOSIT_STRESS_PCT
    )

    relative_migration_stress = (
        migration_4w
        <= MIGRATION_CONFIRMATION_PP
    )

    deposit_confirmation = (
        actual_deposit_stress
        or
        relative_migration_stress
    )

    severe_deposit_flight = (
        small_4w
        <= SMALL_BANK_DEPOSIT_SEVERE_PCT
        and
        migration_4w
        <= MIGRATION_SEVERE_PP
    )

    # =========================================================
    # COMMON TEXT
    # =========================================================

    diagnostic_text = (
        f"Federal Reserve primary credit is "
        f"${float(stats.primary_credit_billions):,.1f}B, "
        f"equal to {primary_ratio:.3f}% of domestic-bank "
        f"deposits. Small-bank deposits changed "
        f"{small_4w:+.2f}% over four weeks, while their "
        f"growth relative to large banks was "
        f"{migration_4w:+.2f} percentage points."
    )

    # =========================================================
    # CRITICAL
    # =========================================================

    if (
        primary_ratio
        >= PRIMARY_CRITICAL_PCT
    ):

        return Signal(
            category=
                "Bank Funding",

            title=
                "Bank funding severely stressed",

            severity=
                "Critical",

            message=(
                f"{diagnostic_text} "
                "Reliance on Federal Reserve primary "
                "credit is at a historically extreme "
                "level, indicating severe banking-system "
                "liquidity stress."
            ),
        )

    # =========================================================
    # WARNING
    # =========================================================

    if (
        primary_ratio
        >= PRIMARY_WARNING_PCT
        or
        (
            primary_ratio
            >= PRIMARY_CONFIRMABLE_WARNING_PCT
            and
            deposit_confirmation
        )
    ):

        return Signal(
            category=
                "Bank Funding",

            title=
                "Bank funding pressure elevated",

            severity=
                "Warning",

            message=(
                f"{diagnostic_text} "
                "Bank liquidity demand is economically "
                "meaningful and is consistent with "
                "elevated funding pressure."
            ),
        )

    # =========================================================
    # WATCH
    # =========================================================

    if (
        primary_ratio
        >= PRIMARY_WATCH_PCT
        or
        severe_deposit_flight
    ):

        return Signal(
            category=
                "Bank Funding",

            title=
                "Bank funding warrants monitoring",

            severity=
                "Watch",

            message=(
                f"{diagnostic_text} "
                "Bank funding conditions show enough "
                "deterioration to warrant monitoring, "
                "but do not yet indicate severe "
                "system-wide funding stress."
            ),
        )

    # =========================================================
    # NORMAL
    # =========================================================

    return Signal(
        category=
            "Bank Funding",

        title=
            "Bank funding conditions orderly",

        severity=
            "Normal",

        message=(
            f"{diagnostic_text} "
            "Primary-credit usage and deposit behavior "
            "do not indicate unusual banking-system "
            "funding stress."
        ),
    )


# =============================================================
# LIVE / HISTORICAL WRAPPER
# =============================================================


def evaluate_bank_funding_signal(
    as_of_date: date | None = None,
) -> Signal:

    stats = (
        bank_funding_statistics(
            as_of_date=
                as_of_date,
        )
    )

    return (
        evaluate_bank_funding_statistics(
            stats
        )
    )


# =============================================================
# TERMINAL TEST
# =============================================================


if __name__ == "__main__":

    signal = (
        evaluate_bank_funding_signal()
    )

    print()

    print(
        "Liquidity Monitor — "
        "Bank Funding Signal"
    )

    print("=" * 72)

    print()

    print(
        f"Severity: "
        f"{signal.severity}"
    )

    print(
        f"Title:    "
        f"{signal.title}"
    )

    print()

    print(
        signal.message
    )