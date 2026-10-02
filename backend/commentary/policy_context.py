from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any


@dataclass(frozen=True)
class FomcMeeting:
    start_date: date
    end_date: date


# Official Federal Reserve 2026 FOMC calendar.
FOMC_MEETINGS_2026 = (
    FomcMeeting(
        date(2026, 1, 27),
        date(2026, 1, 28),
    ),
    FomcMeeting(
        date(2026, 3, 17),
        date(2026, 3, 18),
    ),
    FomcMeeting(
        date(2026, 4, 28),
        date(2026, 4, 29),
    ),
    FomcMeeting(
        date(2026, 6, 16),
        date(2026, 6, 17),
    ),
    FomcMeeting(
        date(2026, 7, 28),
        date(2026, 7, 29),
    ),
    FomcMeeting(
        date(2026, 9, 15),
        date(2026, 9, 16),
    ),
    FomcMeeting(
        date(2026, 10, 27),
        date(2026, 10, 28),
    ),
    FomcMeeting(
        date(2026, 12, 8),
        date(2026, 12, 9),
    ),
)


def build_policy_context(
    as_of_date: date,
) -> dict[str, Any] | None:
    """
    Return scheduled FOMC context known as of a replay date.

    Date-only historical replay uses a deliberately conservative
    rule: a policy decision on the final meeting date is not
    considered known until the following calendar date.

    No policy outcome, rate change, or future decision is exposed.
    """

    if as_of_date.year != 2026:
        return None

    nearby_window = timedelta(days=3)

    for meeting in FOMC_MEETINGS_2026:
        window_start = (
            meeting.start_date
            - nearby_window
        )
        window_end = (
            meeting.end_date
            + nearby_window
        )

        if not (
            window_start
            <= as_of_date
            <= window_end
        ):
            continue

        meeting_in_progress = (
            meeting.start_date
            <= as_of_date
            <= meeting.end_date
        )

        decision_known = (
            as_of_date
            > meeting.end_date
        )

        days_to_decision = None
        days_since_decision = None

        if not decision_known:
            days_to_decision = (
                meeting.end_date
                - as_of_date
            ).days
        else:
            days_since_decision = (
                as_of_date
                - meeting.end_date
            ).days

        return {
            "scheduled_fomc_nearby": True,

            "meeting_dates": [
                meeting.start_date.isoformat(),
                meeting.end_date.isoformat(),
            ],

            "decision_date":
                meeting.end_date.isoformat(),

            "meeting_in_progress":
                meeting_in_progress,

            "decision_known_as_of_replay":
                decision_known,

            "policy_transition_window":
                True,

            "days_to_fomc_decision":
                days_to_decision,

            "days_since_fomc_decision":
                days_since_decision,

            "timing_precision":
                "date_only_conservative",

            "economic_context": (
                "Short-dated Treasury yields can reflect "
                "expectations about policy over their maturity, "
                "while IORB is a current administered rate. "
                "The existence of a scheduled FOMC meeting does "
                "not establish the direction or size of any "
                "future policy decision."
            ),
        }

    return {
        "scheduled_fomc_nearby": False,
        "policy_transition_window": False,
    }
