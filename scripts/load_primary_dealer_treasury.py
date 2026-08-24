from __future__ import annotations

from backend.database.seed import (
    seed_database,
)

from backend.services.provider_refresh import (
    refresh_nyfed_primary_dealers,
)


def main() -> None:
    """
    Refresh catalog-defined New York Fed
    Primary Dealer Treasury data.
    """

    print()

    print(
        "Liquidity Monitor — "
        "Primary Dealer Treasury Refresh"
    )

    print(
        "=" * 72
    )

    seed_database()

    refresh_nyfed_primary_dealers()

    print()

    print(
        "=" * 72
    )

    print(
        "Primary Dealer Treasury "
        "refresh complete."
    )


if __name__ == "__main__":
    main()