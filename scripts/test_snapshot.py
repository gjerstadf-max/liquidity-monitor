from backend.services.daily_snapshot import build_daily_snapshot


snapshot = build_daily_snapshot()

print()

print("Liquidity Monitor Snapshot")

print("---------------------------")

print(snapshot.generated_at)

print()

print(snapshot.assessment.overall_score)

print(snapshot.assessment.overall_condition)

print()

print(snapshot.morning_brief.headline)