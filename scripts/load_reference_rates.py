from __future__ import annotations

from backend.database.seed import (
    seed_database,
)
from backend.services.provider_refresh import (
    refresh_nyfed_reference_rates,
)


def main() -> None:
    """
    Refresh all catalog-defined New York Fed
    reference-rate series.

    Indicator definitions and child-field mappings
    come from the central market-data catalog.
    """

    print()

    print(
        "Liquidity Monitor — "
        "NY Fed Reference Rate Refresh"
    )

    print(
        "=" * 72
    )


    # Ensure any newly registered catalog indicators
    # exist before observations are written.

    seed_database()


    refresh_nyfed_reference_rates(
        observation_count=
            100
    )


    print()

    print(
        "=" * 72
    )

    print(
        "Reference-rate refresh complete."
    )


if __name__ == "__main__":

    main()