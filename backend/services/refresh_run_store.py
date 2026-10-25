
from __future__ import annotations

from datetime import datetime, timezone

from backend.database.connection import get_session
from backend.database.models import RefreshRun

from datetime import timedelta

from sqlalchemy import select

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

def format_utc(value: datetime | None) -> str | None:
    if value is None:
        return None

    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc).isoformat()

def start_refresh_run(
    batch_id: str,
    component: str,
) -> int:
    """
    Create an audit record when a provider refresh starts.

    Returns the database ID of the new record.
    """
    with get_session() as session:
        record = RefreshRun(
            batch_id=batch_id,
            component=component,
            started_at=utc_now(),
            status="running",
        )

        session.add(record)
        session.commit()

        return record.id


def complete_refresh_run(
    run_id: int,
    *,
    received: int,
    inserted: int,
) -> None:
    """
    Mark a provider refresh as successfully completed.
    """
    with get_session() as session:
        record = session.get(RefreshRun, run_id)

        if record is None:
            raise RuntimeError(
                f"Refresh run {run_id} does not exist."
            )

        if record.status != "running":
            raise RuntimeError(
                f"Refresh run {run_id} is not running."
            )

        record.completed_at = utc_now()
        record.status = "success"
        record.received = received
        record.inserted = inserted

        session.commit()


def fail_refresh_run(
    run_id: int,
    error: Exception,
) -> None:
    """
    Record failure without persisting potentially sensitive
    exception messages, request URLs, or API credentials.
    """
    with get_session() as session:
        record = session.get(RefreshRun, run_id)

        if record is None:
            raise RuntimeError(
                f"Refresh run {run_id} does not exist."
            )

        if record.status != "running":
            raise RuntimeError(
                f"Refresh run {run_id} is not running."
            )

        record.completed_at = utc_now()
        record.status = "failed"
        record.error_type = type(error).__name__

        session.commit()

def get_latest_refresh_health(
    timeout_minutes: int = 30,
) -> list[dict[str, object]]:
    """
    Return the latest recorded attempt for each component.

    A long-running attempt is flagged as possibly interrupted
    without changing the stored audit record.
    """
    now = utc_now()
    latest = {}

    with get_session() as session:
        records = session.scalars(
            select(RefreshRun).order_by(
                RefreshRun.started_at.desc(),
                RefreshRun.id.desc(),
            )
        ).all()

        for record in records:
            if record.component in latest:
                continue

            status = record.status

            started_at = record.started_at

            # SQLite may return naive datetimes even when
            # timezone=True is specified.
            if started_at.tzinfo is None:
                started_at = started_at.replace(
                    tzinfo=timezone.utc
                )

            if (
                status == "running"
                and now - started_at
                > timedelta(minutes=timeout_minutes)
            ):
                status = "possibly_interrupted"

            latest[record.component] = {
                "component": record.component,
                "status": status,
                "started_at": started_at.isoformat(),
                "completed_at": format_utc(record.completed_at),
                "error_type": record.error_type,
                "received": record.received,
                "inserted": record.inserted,
            }

    return list(latest.values())


def get_production_refresh_health() -> list[dict[str, object]]:
    """
    Return operational health for registered production components.

    Latest attempt and last success are reported separately.
    No economic liquidity signals are modified.
    """
    from backend.services.market_data_refresh import (
        PROVIDERS,
        STRUCTURED_DATASETS,
    )

    components = [
        name for name, _ in PROVIDERS
    ] + [
        name for name, _ in STRUCTURED_DATASETS
    ]

    latest_health = {
        record["component"]: record
        for record in get_latest_refresh_health()
        if record["component"] in components
    }

    with get_session() as session:
        successful_runs = session.scalars(
            select(RefreshRun)
            .where(
                RefreshRun.component.in_(components),
                RefreshRun.status == "success",
            )
            .order_by(
                RefreshRun.started_at.desc(),
                RefreshRun.id.desc(),
            )
        ).all()

        last_success = {}
        for record in successful_runs:
            if record.component not in last_success:
                last_success[record.component] = record

        results = []

        for component in components:
            latest = latest_health.get(component)
            success = last_success.get(component)

            results.append({
                "component": component,
                "latest_status": (
                    latest["status"]
                    if latest
                    else "not_recorded"
                ),
                "latest_started_at": (
                    latest["started_at"]
                    if latest
                    else None
                ),
                "latest_error_type": (
                    latest["error_type"]
                    if latest
                    else None
                ),
                "last_success_at": (
                    format_utc(success.completed_at)
                    if success and success.completed_at
                    else None
                ),
            })

    return results
