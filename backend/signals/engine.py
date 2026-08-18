from backend.signals.funding import (
    evaluate_funding_signal,
)
from backend.signals.system_liquidity import (
    evaluate_system_liquidity_signal,
)


def run_signals() -> None:

    funding = evaluate_funding_signal()

    system_liquidity = (
        evaluate_system_liquidity_signal()
    )


    print()
    print("Liquidity Monitor Signal Engine")
    print("================================")


    print()
    print("FUNDING")
    print("--------------------------------")

    print(
        f"Signal:    {funding.title}"
    )

    print(
        f"Severity:  {funding.severity}"
    )

    print()

    print(
        funding.message
    )


    print()
    print()
    print("SYSTEM LIQUIDITY")
    print("--------------------------------")

    print(
        f"Signal:    {system_liquidity.title}"
    )

    print(
        f"Severity:  {system_liquidity.severity}"
    )

    print()

    print(
        system_liquidity.message
    )


if __name__ == "__main__":
    run_signals()