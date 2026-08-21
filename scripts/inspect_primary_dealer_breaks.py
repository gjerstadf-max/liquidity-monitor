from backend.collectors.nyfed_primary_dealers import (
    fetch_primary_dealer_series_breaks,
)


def main() -> None:

    print()
    print(
        "Liquidity Monitor — "
        "Primary Dealer Series Breaks"
    )

    print("=" * 90)


    breaks = (
        fetch_primary_dealer_series_breaks()
    )


    print()
    print(
        f"Reporting regimes: "
        f"{len(breaks)}"
    )

    print()


    print(
        f"{'Series Break':<18}"
        f"{'Start':<14}"
        f"{'End':<14}"
        f"Label"
    )

    print("-" * 90)


    for item in breaks:

        print(
            f"{item.series_break:<18}"
            f"{item.start_date:<14}"
            f"{(item.end_date or 'Current'):<14}"
            f"{item.label}"
        )


if __name__ == "__main__":
    main()