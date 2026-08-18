from backend.metrics.funding import (
    funding_spread_statistics,
)
from backend.signals.models import Signal


def evaluate_funding_signal() -> Signal:
    """
    Evaluate SOFR-EFFR funding conditions using both:

    1. The absolute spread level.
    2. The spread's recent historical context.

    A positive SOFR-EFFR spread is treated as more concerning
    because it can indicate relatively greater pressure in
    secured overnight funding.

    Large negative readings are treated as unusual divergence,
    but not automatically as equivalent funding stress.
    """

    stats = funding_spread_statistics()

    spread = float(
        stats.current_spread_bp
    )

    zscore = stats.zscore_60d

    percentile = stats.percentile_60d


    # ---------------------------------------------------------
    # Critical funding pressure
    # ---------------------------------------------------------

    if (
        spread >= 10
        or zscore >= 3.0
    ):
        return Signal(
            category="Funding",
            title="Significant funding pressure",
            severity="Critical",
            message=(
                f"SOFR is {spread:+.0f} bp relative to EFFR. "
                f"The spread is at the "
                f"{percentile:.0f}th percentile of the recent "
                f"60-observation distribution with a "
                f"z-score of {zscore:+.2f}. "
                "Secured funding conditions show significant "
                "relative pressure."
            ),
        )


    # ---------------------------------------------------------
    # Warning
    # ---------------------------------------------------------

    if (
        spread >= 6
        or zscore >= 2.0
    ):
        return Signal(
            category="Funding",
            title="Funding pressure elevated",
            severity="Warning",
            message=(
                f"SOFR is {spread:+.0f} bp relative to EFFR. "
                f"The spread is at the "
                f"{percentile:.0f}th percentile of the recent "
                f"distribution with a "
                f"z-score of {zscore:+.2f}. "
                "The secured funding spread is elevated "
                "relative to recent conditions."
            ),
        )


    # ---------------------------------------------------------
    # Watch
    # ---------------------------------------------------------

    if (
        spread >= 3
        or zscore >= 1.25
        or percentile >= 90
    ):
        return Signal(
            category="Funding",
            title="Funding spread warrants monitoring",
            severity="Watch",
            message=(
                f"SOFR is {spread:+.0f} bp relative to EFFR. "
                f"The spread is at the "
                f"{percentile:.0f}th percentile of the recent "
                f"distribution with a "
                f"z-score of {zscore:+.2f}. "
                "Funding markets remain functional, but the "
                "secured-unsecured spread warrants monitoring."
            ),
        )


    # ---------------------------------------------------------
    # Unusual negative divergence
    # ---------------------------------------------------------

    if (
        spread <= -6
        or zscore <= -2.0
        or percentile <= 5
    ):
        return Signal(
            category="Funding",
            title="Unusual funding-rate divergence",
            severity="Watch",
            message=(
                f"SOFR is {spread:+.0f} bp relative to EFFR. "
                f"The spread is at the "
                f"{percentile:.0f}th percentile of the recent "
                f"distribution with a "
                f"z-score of {zscore:+.2f}. "
                "The divergence is unusual relative to recent "
                "history, although it does not indicate the "
                "same type of secured funding pressure as a "
                "large positive spread."
            ),
        )


    # ---------------------------------------------------------
    # Normal
    # ---------------------------------------------------------

    return Signal(
        category="Funding",
        title="Funding rates well aligned",
        severity="Normal",
        message=(
            f"SOFR is {spread:+.0f} bp relative to EFFR. "
            f"The spread is at the "
            f"{percentile:.0f}th percentile of the recent "
            f"distribution with a "
            f"z-score of {zscore:+.2f}. "
            "Secured and unsecured overnight funding rates "
            "remain well aligned with no meaningful evidence "
            "of funding pressure."
        ),
    )