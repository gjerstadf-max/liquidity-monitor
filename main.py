from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from backend.api.routes import router as api_router
from backend.services.daily_snapshot import build_daily_snapshot

from backend.events.critical_events import (
    get_calendar_turn_events,
    get_major_critical_events,
)




app = FastAPI(
    title="Liquidity Monitor",
    version="0.4.0",
)


app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static",
)


templates = Jinja2Templates(
    directory="templates"
)


app.include_router(api_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "liquidity-monitor",
    }


@app.get("/")
def home(request: Request):
    snapshot = build_daily_snapshot(
        include_news=True
    )

    critical_events = (
    get_major_critical_events()
)

    calendar_turn_events = (
    get_calendar_turn_events()
)


    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "snapshot": snapshot,
            "critical_events": critical_events,
            "calendar_turn_events": calendar_turn_events,
        },
    )

