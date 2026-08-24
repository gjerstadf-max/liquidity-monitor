from __future__ import annotations

from backend.database.seed import (
    seed_database,
)
from backend.services.provider_refresh import (
    refresh_nyfed_reverse_repo,
)


def main() -> None:
    """
    Refresh catalog-defined New York Fed
    overnight reverse-repo data.
    """

    print()

    print(
        "Liquidity Monitor — "
        "ON RRP Refresh"
    )

    print(
        "=" * 72
    )


    seed_database()


    refresh_nyfed_reverse_repo(
        observation_count=
            400
    )


    print()

    print(
        "=" * 72
    )

    print(
        "ON RRP refresh complete."
    )


if __name__ == "__main__":

    main()