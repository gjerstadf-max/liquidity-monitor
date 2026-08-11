from backend.signals.funding import evaluate_funding_signal


def run_signals() -> None:
    signal = evaluate_funding_signal()

    print()
    print("Funding Signals")
    print("---------------------------")
    print(f"Title:     {signal.title}")
    print(f"Severity:  {signal.severity}")
    print(f"Message:   {signal.message}")


if __name__ == "__main__":
    run_signals()