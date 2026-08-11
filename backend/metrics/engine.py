from backend.metrics.funding import latest_funding_snapshot


def run_metrics() -> None:
    snapshot = latest_funding_snapshot()

    print()
    print("Funding Metrics")
    print("---------------------------")
    print(f"SOFR              {snapshot.sofr:.2f}%")
    print(f"EFFR              {snapshot.effr:.2f}%")
    print(f"SOFR - EFFR       {snapshot.spread_basis_points:.0f} bp")
    print()
    print(f"Observation Date   {snapshot.observation_date}")


if __name__ == "__main__":
    run_metrics()