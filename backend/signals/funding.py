from backend.metrics.funding import latest_funding_snapshot
from backend.signals.models import Signal


def evaluate_funding_signal() -> Signal:
    snapshot = latest_funding_snapshot()
    spread = snapshot.spread_basis_points

    if abs(spread) <= 2:
        return Signal(
            category="Funding",
            title="Funding rates well aligned",
            severity="Normal",
            message=(
                f"SOFR and EFFR are closely aligned at a spread of "
                f"{spread:.0f} basis points."
            ),
        )

    if abs(spread) <= 5:
        return Signal(
            category="Funding",
            title="Funding spread warrants monitoring",
            severity="Watch",
            message=(
                f"SOFR and EFFR are separated by {spread:.0f} basis points."
            ),
        )

    return Signal(
        category="Funding",
        title="Funding spread elevated",
        severity="Warning",
        message=(
            f"SOFR and EFFR are separated by {spread:.0f} basis points, "
            "which is outside the normal range used by this initial rule."
        ),
    )