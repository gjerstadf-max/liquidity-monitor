from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from statistics import mean, pstdev

from backend.metrics.treasury_intermediation import (
    _load_intermediation_history,
)

from backend.signals.models import Signal


# =============================================================
# TREASURY INTERMEDIATION SIGNAL V1
# =============================================================
#
# Philosophy:
#
# An isolated extreme does not imply broad Treasury-market
# intermediation stress.
#
# The signal looks for convergence across three independent
# dimensions:
#
#   1. Balance-sheet adjustment
#   2. Intermediation load
#   3. Settlement friction
#
# March 2020 is the model stress episode:
# several dimensions became abnormal simultaneously.
#
# =============================================================


ELEVATED_Z = 2.0

STRONG_Z = 3.0


# =============================================================
# DIAGNOSTIC OBJECT
# =============================================================


@dataclass(frozen=True)
class TreasuryIntermediationDiagnostics:
    observation_date: date

    # ---------------------------------------------------------
    # RAW CURRENT VALUES
    # ---------------------------------------------------------

    dealer_positions_billions: float

    treasury_transactions_billions: float

    securities_borrowed_billions: float

    total_fails_billions: float

    repo_billions: float | None

    reverse_repo_billions: float | None

    # ---------------------------------------------------------
    # FOUR-WEEK CHANGES
    # ---------------------------------------------------------

    positions_change_4w_billions: float

    transactions_change_4w_billions: float

    borrowed_change_4w_billions: float

    fails_change_4w_billions: float

    # ---------------------------------------------------------
    # FOUR-WEEK CHANGE Z-SCORES
    # ---------------------------------------------------------

    positions_change_4w_z: float

    transactions_change_4w_z: float

    borrowed_change_4w_z: float

    fails_change_4w_z: float

    # ---------------------------------------------------------
    # FAILS LEVEL
    # ---------------------------------------------------------

    total_fails_z_52w: float

    # ---------------------------------------------------------
    # FACTOR DIMENSIONS
    # ---------------------------------------------------------

    @property
    def balance_sheet_adjustment_z(
        self,
    ) -> float:
        """
        Both rapid accumulation and rapid reduction of
        dealer Treasury inventory can represent unusual
        balance-sheet adjustment.

        Direction therefore does not matter here.
        """

        return abs(
            self.positions_change_4w_z
        )

    @property
    def intermediation_load_z(
        self,
    ) -> float:
        """
        Higher transaction activity or securities borrowing
        can indicate elevated demand on dealer intermediation.

        Falling activity does not independently count as
        increased intermediation load in V1.
        """

        return max(
            self.transactions_change_4w_z,
            self.borrowed_change_4w_z,
        )

    @property
    def settlement_friction_z(
        self,
    ) -> float:
        """
        Settlement friction can show up through either:

        - an unusually high level of Treasury fails, or
        - a rapid increase in fails.

        Use whichever is more abnormal.
        """

        return max(
            self.total_fails_z_52w,
            self.fails_change_4w_z,
        )


# =============================================================
# STATISTICAL HELPERS
# =============================================================


def _rolling_zscore(
    values: list[float],
    window: int = 52,
) -> float:
    """
    Z-score the latest value against a trailing window.

    The current observation is included in the trailing
    window, consistent with the diagnostic methodology
    already used elsewhere in Liquidity Monitor.
    """

    if len(values) < window:
        raise RuntimeError(
            f"At least {window} observations "
            "are required."
        )

    trailing = (
        values[
            -window:
        ]
    )

    current = (
        trailing[
            -1
        ]
    )

    average = mean(
        trailing
    )

    standard_deviation = pstdev(
        trailing
    )

    if standard_deviation == 0:
        return 0.0

    return (
        current
        -
        average
    ) / standard_deviation


# =============================================================
# HISTORICAL DIAGNOSTIC SERIES
# =============================================================


def build_treasury_intermediation_diagnostics_history(
    as_of_date: date | None = None,
) -> list[TreasuryIntermediationDiagnostics]:
    """
    Build the complete Factor #4 diagnostic history.

    Historical replay uses only observations available
    on or before as_of_date.

    Four-week changes require five weekly observations.

    A trailing 52-week z-score of those changes requires
    52 change observations, so the first Factor #4 signal
    occurs roughly 55 weeks after the raw series begins.
    """

    history = (
        _load_intermediation_history(
            as_of_date=
                as_of_date
        )
    )

    if len(history) < 56:
        raise RuntimeError(
            "At least 56 Treasury intermediation "
            "observations are required."
        )

    # ---------------------------------------------------------
    # BUILD FOUR-WEEK CHANGES
    # ---------------------------------------------------------

    change_rows: list[dict] = []

    for index in range(
        4,
        len(history),
    ):
        current = (
            history[
                index
            ]
        )

        four_weeks_ago = (
            history[
                index - 4
            ]
        )

        change_rows.append(
            {
                "history_index":
                    index,

                "observation_date":
                    current.observation_date,

                "positions_change_4w":
                    float(
                        current.dealer_positions_billions
                        -
                        four_weeks_ago.dealer_positions_billions
                    ),

                "transactions_change_4w":
                    float(
                        current.treasury_transactions_billions
                        -
                        four_weeks_ago.treasury_transactions_billions
                    ),

                "borrowed_change_4w":
                    float(
                        current.securities_borrowed_billions
                        -
                        four_weeks_ago.securities_borrowed_billions
                    ),

                "fails_change_4w":
                    float(
                        current.total_fails_billions
                        -
                        four_weeks_ago.total_fails_billions
                    ),
            }
        )

    # ---------------------------------------------------------
    # NEED 52 CHANGE OBSERVATIONS
    # ---------------------------------------------------------

    diagnostics: list[
        TreasuryIntermediationDiagnostics
    ] = []

    for change_index in range(
        51,
        len(change_rows),
    ):
        available_changes = (
            change_rows[
                : change_index + 1
            ]
        )

        current_change = (
            available_changes[
                -1
            ]
        )

        history_index = (
            current_change[
                "history_index"
            ]
        )

        current_snapshot = (
            history[
                history_index
            ]
        )

        # -----------------------------------------------------
        # POSITION CHANGE
        # -----------------------------------------------------

        position_change_values = [
            row[
                "positions_change_4w"
            ]
            for row
            in available_changes
        ]

        positions_change_z = (
            _rolling_zscore(
                position_change_values
            )
        )

        # -----------------------------------------------------
        # TRANSACTION CHANGE
        # -----------------------------------------------------

        transaction_change_values = [
            row[
                "transactions_change_4w"
            ]
            for row
            in available_changes
        ]

        transactions_change_z = (
            _rolling_zscore(
                transaction_change_values
            )
        )

        # -----------------------------------------------------
        # BORROWED CHANGE
        # -----------------------------------------------------

        borrowed_change_values = [
            row[
                "borrowed_change_4w"
            ]
            for row
            in available_changes
        ]

        borrowed_change_z = (
            _rolling_zscore(
                borrowed_change_values
            )
        )

        # -----------------------------------------------------
        # FAILS CHANGE
        # -----------------------------------------------------

        fails_change_values = [
            row[
                "fails_change_4w"
            ]
            for row
            in available_changes
        ]

        fails_change_z = (
            _rolling_zscore(
                fails_change_values
            )
        )

        # -----------------------------------------------------
        # FAILS LEVEL
        # -----------------------------------------------------

        fails_level_values = [
            float(
                item.total_fails_billions
            )
            for item
            in history[
                : history_index + 1
            ]
        ]

        total_fails_z = (
            _rolling_zscore(
                fails_level_values
            )
        )

        # -----------------------------------------------------
        # SUPPORTING FINANCING
        # -----------------------------------------------------

        repo_value = (
            float(
                current_snapshot.repo_billions
            )
            if current_snapshot.repo_billions
            is not None
            else None
        )

        reverse_repo_value = (
            float(
                current_snapshot.reverse_repo_billions
            )
            if current_snapshot.reverse_repo_billions
            is not None
            else None
        )

        # -----------------------------------------------------
        # BUILD DIAGNOSTIC
        # -----------------------------------------------------

        diagnostics.append(
            TreasuryIntermediationDiagnostics(
                observation_date=
                    current_snapshot.observation_date,

                dealer_positions_billions=
                    float(
                        current_snapshot.dealer_positions_billions
                    ),

                treasury_transactions_billions=
                    float(
                        current_snapshot.treasury_transactions_billions
                    ),

                securities_borrowed_billions=
                    float(
                        current_snapshot.securities_borrowed_billions
                    ),

                total_fails_billions=
                    float(
                        current_snapshot.total_fails_billions
                    ),

                repo_billions=
                    repo_value,

                reverse_repo_billions=
                    reverse_repo_value,

                positions_change_4w_billions=
                    current_change[
                        "positions_change_4w"
                    ],

                transactions_change_4w_billions=
                    current_change[
                        "transactions_change_4w"
                    ],

                borrowed_change_4w_billions=
                    current_change[
                        "borrowed_change_4w"
                    ],

                fails_change_4w_billions=
                    current_change[
                        "fails_change_4w"
                    ],

                positions_change_4w_z=
                    positions_change_z,

                transactions_change_4w_z=
                    transactions_change_z,

                borrowed_change_4w_z=
                    borrowed_change_z,

                fails_change_4w_z=
                    fails_change_z,

                total_fails_z_52w=
                    total_fails_z,
            )
        )

    return diagnostics


# =============================================================
# DIMENSION CLASSIFICATION
# =============================================================


def treasury_intermediation_dimension_state(
    diagnostics: TreasuryIntermediationDiagnostics,
) -> tuple[
    list[str],
    list[str],
]:
    """
    Return:

        elevated_dimensions
        strong_dimensions
    """

    dimensions = {
        "Balance-sheet adjustment":
            diagnostics.balance_sheet_adjustment_z,

        "Intermediation load":
            diagnostics.intermediation_load_z,

        "Settlement friction":
            diagnostics.settlement_friction_z,
    }

    elevated = [
        name
        for (
            name,
            value,
        ) in dimensions.items()
        if value >= ELEVATED_Z
    ]

    strong = [
        name
        for (
            name,
            value,
        ) in dimensions.items()
        if value >= STRONG_Z
    ]

    return (
        elevated,
        strong,
    )


# =============================================================
# PURE SIGNAL EVALUATOR
# =============================================================


def evaluate_treasury_intermediation_diagnostics(
    diagnostics: TreasuryIntermediationDiagnostics,
) -> Signal:
    """
    Treasury Intermediation Signal V1.

    Normal:
        No dimensions elevated.

    Watch:
        One dimension elevated.

    Warning:
        Two dimensions elevated.

    Critical:
        All three dimensions elevated AND
        settlement friction is strong.

    Important:
        An isolated extreme cannot produce Warning
        or Critical regardless of its z-score.
    """

    (
        elevated_dimensions,
        strong_dimensions,
    ) = (
        treasury_intermediation_dimension_state(
            diagnostics
        )
    )

    elevated_count = len(
        elevated_dimensions
    )

    settlement_strong = (
        diagnostics.settlement_friction_z
        >= STRONG_Z
    )

    diagnostic_text = (
        "Balance-sheet adjustment is "
        f"{diagnostics.balance_sheet_adjustment_z:.2f}σ, "
        "intermediation load is "
        f"{diagnostics.intermediation_load_z:.2f}σ, "
        "and settlement friction is "
        f"{diagnostics.settlement_friction_z:.2f}σ."
    )

    # =========================================================
    # CRITICAL
    # =========================================================
    #
    # Broad convergence is required.
    #
    # Settlement dysfunction must also be severe.
    # =========================================================

    if (
        elevated_count == 3
        and
        settlement_strong
    ):
        return Signal(
            category=
                "Treasury Intermediation",

            title=
                "Broad Treasury intermediation stress",

            severity=
                "Critical",

            message=(
                f"{diagnostic_text} "
                "Dealer balance-sheet adjustment, "
                "intermediation load, and settlement "
                "friction are simultaneously abnormal, "
                "with settlement friction at a severe "
                "level. Treasury-market intermediation "
                "shows broad evidence of stress."
            ),
        )

    # =========================================================
    # WARNING
    # =========================================================

    if elevated_count >= 2:
        dimension_text = (
            ", ".join(
                elevated_dimensions
            )
        )

        return Signal(
            category=
                "Treasury Intermediation",

            title=
                "Treasury intermediation pressure elevated",

            severity=
                "Warning",

            message=(
                f"{diagnostic_text} "
                f"Two or more dimensions are abnormal: "
                f"{dimension_text}. "
                "Pressure is evident across multiple "
                "Treasury intermediation channels, but "
                "the evidence does not meet the threshold "
                "for broad severe dysfunction."
            ),
        )

    # =========================================================
    # WATCH
    # =========================================================

    if elevated_count == 1:
        dimension = (
            elevated_dimensions[
                0
            ]
        )

        return Signal(
            category=
                "Treasury Intermediation",

            title=
                "Treasury intermediation warrants monitoring",

            severity=
                "Watch",

            message=(
                f"{diagnostic_text} "
                f"{dimension} is unusually elevated, "
                "but the other Treasury intermediation "
                "dimensions do not confirm broad pressure."
            ),
        )

    # =========================================================
    # NORMAL
    # =========================================================

    return Signal(
        category=
            "Treasury Intermediation",

        title=
            "Treasury intermediation remains orderly",

        severity=
            "Normal",

        message=(
            f"{diagnostic_text} "
            "Dealer balance-sheet adjustment, "
            "intermediation demand, and settlement "
            "conditions do not show convergent evidence "
            "of Treasury-market stress."
        ),
    )


# =============================================================
# LIVE / HISTORICAL WRAPPER
# =============================================================


def evaluate_treasury_intermediation_signal(
    as_of_date: date | None = None,
) -> Signal:
    """
    Evaluate the latest Treasury Intermediation signal
    available on or before as_of_date.
    """

    diagnostics = (
        build_treasury_intermediation_diagnostics_history(
            as_of_date=
                as_of_date
        )
    )

    if not diagnostics:
        raise RuntimeError(
            "No Treasury intermediation diagnostics "
            "are available."
        )

    return (
        evaluate_treasury_intermediation_diagnostics(
            diagnostics[
                -1
            ]
        )
    )


# =============================================================
# TERMINAL TEST
# =============================================================


if __name__ == "__main__":
    diagnostics = (
        build_treasury_intermediation_diagnostics_history()
    )

    latest = (
        diagnostics[
            -1
        ]
    )

    signal = (
        evaluate_treasury_intermediation_diagnostics(
            latest
        )
    )

    print()
    print(
        "Liquidity Monitor — "
        "Treasury Intermediation Signal V1"
    )

    print("=" * 80)

    print()
    print(
        f"Observation Date: "
        f"{latest.observation_date}"
    )

    print()

    print(
        f"Balance-sheet adjustment: "
        f"{latest.balance_sheet_adjustment_z:+.2f}σ"
    )

    print(
        f"Intermediation load:       "
        f"{latest.intermediation_load_z:+.2f}σ"
    )

    print(
        f"Settlement friction:       "
        f"{latest.settlement_friction_z:+.2f}σ"
    )

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