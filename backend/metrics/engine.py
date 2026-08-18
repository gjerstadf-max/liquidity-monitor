from backend.metrics.funding import (
    funding_spread_statistics,
    latest_funding_snapshot,
)
from backend.metrics.reverse_repo import (
    reverse_repo_metrics,
)
from backend.metrics.reserves import (
    reserve_balance_metrics,
)
from backend.metrics.liquidity_buffer import (
    liquidity_buffer_metrics,
)
from backend.metrics.system_liquidity import (
    system_liquidity_history_metrics,
    system_liquidity_metrics,
)

def run_metrics() -> None:

    # =========================================================
    # FUNDING
    # =========================================================

    snapshot = latest_funding_snapshot()

    stats = funding_spread_statistics()


    print()
    print("Funding Metrics")
    print("================================")

    print(
        f"Observation Date    "
        f"{snapshot.observation_date}"
    )

    print()

    print(
        f"SOFR                "
        f"{snapshot.sofr:.2f}%"
    )

    print(
        f"Daily Change        "
        f"{snapshot.sofr_change_bp:+.0f} bp"
    )

    print()

    print(
        f"EFFR                "
        f"{snapshot.effr:.2f}%"
    )

    print(
        f"Daily Change        "
        f"{snapshot.effr_change_bp:+.0f} bp"
    )

    print()

    print(
        f"SOFR - EFFR         "
        f"{snapshot.spread_basis_points:+.0f} bp"
    )

    print()

    print("Historical Spread Context")
    print("--------------------------------")

    print(
        f"Observations        "
        f"{stats.observations_used}"
    )

    print(
        f"30-Day Average      "
        f"{stats.average_30d_bp:+.2f} bp"
    )

    print(
        f"60-Day Average      "
        f"{stats.average_60d_bp:+.2f} bp"
    )

    print(
        f"60-Day Range        "
        f"{stats.minimum_60d_bp:+.0f} to "
        f"{stats.maximum_60d_bp:+.0f} bp"
    )

    print(
        f"60-Day Percentile   "
        f"{stats.percentile_60d:.0f}"
    )

    print(
        f"60-Day Z-Score      "
        f"{stats.zscore_60d:+.2f}"
    )


    # =========================================================
    # ON RRP
    # =========================================================

    rrp = reverse_repo_metrics()


    print()
    print()
    print("ON RRP Metrics")
    print("================================")

    print(
        f"Observation Date    "
        f"{rrp.observation_date}"
    )

    print()

    print(
        f"Current Balance     "
        f"${rrp.current_balance_billions:,.3f}B"
    )

    print(
        f"Daily Change        "
        f"${rrp.daily_change_billions:+,.3f}B"
    )

    print()

    print(
        f"20-Day Average      "
        f"${rrp.average_20d_billions:,.3f}B"
    )

    print(
        f"60-Day Average      "
        f"${rrp.average_60d_billions:,.3f}B"
    )

    print(
        f"60-Day Range        "
        f"${rrp.minimum_60d_billions:,.3f}B"
        f" to "
        f"${rrp.maximum_60d_billions:,.3f}B"
    )

    print(
        f"60-Day Percentile   "
        f"{rrp.percentile_60d:.0f}"
    )


    # =========================================================
    # RESERVE BALANCES
    # =========================================================

    reserves = reserve_balance_metrics()


    print()
    print()
    print("Reserve Balance Metrics")
    print("================================")

    print(
        f"Observation Date    "
        f"{reserves.observation_date}"
    )

    print()

    print(
        f"Current Balance     "
        f"${reserves.current_balance_billions:,.3f}B"
    )

    print(
        f"Weekly Change       "
        f"${reserves.weekly_change_billions:+,.3f}B"
    )

    print(
        f"4-Week Change       "
        f"${reserves.four_week_change_billions:+,.3f}B"
    )

    print()

    print(
        f"13-Week Average     "
        f"${reserves.average_13_week_billions:,.3f}B"
    )

    print(
        f"13-Week Range       "
        f"${reserves.minimum_13_week_billions:,.3f}B"
        f" to "
        f"${reserves.maximum_13_week_billions:,.3f}B"
    )

    print(
        f"52-Week Percentile  "
        f"{reserves.percentile_52_week:.0f}"
    )

    print(
        f"Observations Used   "
        f"{reserves.observations_used}"
    )

    # =========================================================
    # LIQUIDITY BUFFER PROXY
    # =========================================================

    buffer = liquidity_buffer_metrics()


    print()
    print()
    print("Liquidity Buffer Proxy")
    print("================================")

    print(
        f"Observation Date    "
        f"{buffer.observation_date}"
    )

    print()

    print(
        f"Reserve Balances    "
        f"${buffer.reserve_balances_billions:,.3f}B"
    )

    print(
        f"ON RRP              "
        f"${buffer.on_rrp_billions:,.3f}B"
    )

    print(
        f"Combined Buffer     "
        f"${buffer.combined_buffer_billions:,.3f}B"
    )

    print()

    print(
        f"Weekly Change       "
        f"${buffer.weekly_change_billions:+,.3f}B"
    )

    print(
        f"4-Week Change       "
        f"${buffer.four_week_change_billions:+,.3f}B"
    )

    print()

    print("4-Week Change by Component")
    print("--------------------------------")

    print(
        f"Reserve Balances    "
        f"${buffer.reserve_change_4_week_billions:+,.3f}B"
    )

    print(
        f"ON RRP              "
        f"${buffer.rrp_change_4_week_billions:+,.3f}B"
    )

    print()

    print("Current Composition")
    print("--------------------------------")

    print(
        f"Reserve Balances    "
        f"{buffer.reserve_share_percent:.1f}%"
    )

    print(
        f"ON RRP              "
        f"{buffer.rrp_share_percent:.1f}%"
    )


    # =========================================================
    # SYSTEM LIQUIDITY
    # =========================================================

    liquidity = system_liquidity_metrics()

    print()
    print()
    print("System Liquidity Proxy")
    print("================================")

    print(
        f"Observation Date    "
        f"{liquidity.observation_date}"
    )

    print()

    print(
        f"Reserve Balances    "
        f"${liquidity.reserve_balances_billions:,.3f}B"
    )

    print(
        f"ON RRP              "
        f"${liquidity.on_rrp_billions:,.3f}B"
    )

    print(
        f"TGA                 "
        f"${liquidity.tga_billions:,.3f}B"
    )

    print()

    print(
        f"Net Liquidity Proxy "
        f"${liquidity.net_liquidity_proxy_billions:,.3f}B"
    )

    print(
        f"Weekly Change       "
        f"${liquidity.weekly_change_billions:+,.3f}B"
    )

    print(
        f"4-Week Change       "
        f"${liquidity.four_week_change_billions:+,.3f}B"
    )


    print()
    print("Weekly Contribution")
    print("--------------------------------")

    print(
        f"Reserve Balances    "
        f"${liquidity.reserve_weekly_contribution_billions:+,.3f}B"
    )

    print(
        f"ON RRP              "
        f"${liquidity.rrp_weekly_contribution_billions:+,.3f}B"
    )

    print(
        f"TGA Effect          "
        f"${liquidity.tga_weekly_contribution_billions:+,.3f}B"
    )


    print()
    print("4-Week Contribution")
    print("--------------------------------")

    print(
        f"Reserve Balances    "
        f"${liquidity.reserve_4_week_contribution_billions:+,.3f}B"
    )

    print(
        f"ON RRP              "
        f"${liquidity.rrp_4_week_contribution_billions:+,.3f}B"
    )

    print(
        f"TGA Effect          "
        f"${liquidity.tga_4_week_contribution_billions:+,.3f}B"
    )
    # =========================================================
    # SYSTEM LIQUIDITY HISTORICAL CONTEXT
    # =========================================================

    history = (
        system_liquidity_history_metrics()
    )


    print()
    print()
    print("System Liquidity Historical Context")
    print("================================")

    print(
        f"Observation Date    "
        f"{history.observation_date}"
    )

    print(
        f"Observations Used   "
        f"{history.observations_used}"
    )

    print()

    print(
        f"Current Proxy       "
        f"${history.current_proxy_billions:,.3f}B"
    )

    print(
        f"4-Week Change       "
        f"${history.four_week_change_billions:+,.3f}B"
    )

    print(
        f"13-Week Change      "
        f"${history.thirteen_week_change_billions:+,.3f}B"
    )

    print()

    print(
        f"13-Week Average     "
        f"${history.average_13_week_billions:,.3f}B"
    )

    print(
        f"52-Week Average     "
        f"${history.average_52_week_billions:,.3f}B"
    )

    print(
        f"52-Week Range       "
        f"${history.minimum_52_week_billions:,.3f}B"
        f" to "
        f"${history.maximum_52_week_billions:,.3f}B"
    )

    print()

    print(
        f"52-Week Percentile  "
        f"{history.percentile_52_week:.0f}"
    )

    print(
        f"52-Week Z-Score     "
        f"{history.zscore_52_week:+.2f}"
    )

if __name__ == "__main__":
    run_metrics()