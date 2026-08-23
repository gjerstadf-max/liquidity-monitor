from __future__ import annotations

from backend.database.seed import (
    seed_database,
)
from backend.services.provider_refresh import (
    refresh_fred_provider,
)


def main() -> None:

    print()

    print(
        "Liquidity Monitor — FRED Refresh"
    )

    print(
        "=" * 72
    )


    # Make sure catalog-defined indicators
    # exist before ingestion.

    seed_database()


    refresh_fred_provider(
        observation_count=
            100
    )


    print()

    print(
        "=" * 72
    )

    print(
        "FRED refresh complete."
    )


if __name__ == "__main__":

    main()