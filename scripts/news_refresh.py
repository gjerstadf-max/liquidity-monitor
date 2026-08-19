from __future__ import annotations

from backend.database.init_db import (
    init_db,
)
from backend.news.narrative import (
    build_market_narrative,
)
from backend.news.storage import (
    save_market_narrative,
)


def main() -> None:

    print()
    print(
        "Liquidity Monitor — News Refresh"
    )
    print("=" * 72)


    # Idempotent. Creates the news_snapshots
    # table if it does not already exist.

    init_db()


    print()
    print(
        "Fetching and classifying "
        "current market news..."
    )


    narrative = (
        build_market_narrative(
            final_limit=6
        )
    )


    result = (
        save_market_narrative(
            narrative
        )
    )


    print()
    print(
        "News snapshot saved."
    )

    print(
        f"Date: "
        f"{result['snapshot_date']}"
    )

    print(
        f"Generated: "
        f"{result['generated_at']}"
    )

    print(
        f"Market Attention: "
        f"{result['market_attention']}"
    )

    print(
        f"Directional Confirmation: "
        f"{result['directional_confirmation']}"
    )

    print(
        f"Stories: "
        f"{result['story_count']}"
    )


if __name__ == "__main__":
    main()