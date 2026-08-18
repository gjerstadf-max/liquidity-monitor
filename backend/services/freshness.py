from __future__ import annotations

from dataclasses import dataclass
from datetime import (
    date,
    datetime,
    time,
    timedelta,
)
from zoneinfo import ZoneInfo


NEW_YORK = ZoneInfo(
    "America/New_York"
)

# EFFR is normally published around 9:00 a.m. ET.
# We allow a small buffer before considering the
# prior business day's observation due.
FUNDING_PUBLICATION_CUTOFF = time(
    hour=9,
    minute=15,
)


@dataclass(frozen=True)
class DataFreshness:
    observation_date: date
    expected_observation_date: date

    business_days_stale: int

    is_current: bool

    label: str


# =============================================================
# HOLIDAY HELPERS
# =============================================================


def _nth_weekday(
    year: int,
    month: int,
    weekday: int,
    occurrence: int,
) -> date:
    """
    Return the nth weekday of a month.

    Monday = 0
    Sunday = 6
    """

    current = date(
        year,
        month,
        1,
    )

    days_until_weekday = (
        weekday - current.weekday()
    ) % 7

    return (
        current
        + timedelta(
            days=days_until_weekday
        )
        + timedelta(
            weeks=occurrence - 1
        )
    )


def _last_weekday(
    year: int,
    month: int,
    weekday: int,
) -> date:
    """
    Return the last specified weekday of a month.
    """

    if month == 12:
        next_month = date(
            year + 1,
            1,
            1,
        )
    else:
        next_month = date(
            year,
            month + 1,
            1,
        )

    current = (
        next_month
        - timedelta(days=1)
    )

    while current.weekday() != weekday:
        current -= timedelta(days=1)

    return current


def _fixed_fed_holiday(
    year: int,
    month: int,
    day: int,
) -> set[date]:
    """
    Federal Reserve Bank convention:

    Saturday holiday:
        Reserve Banks remain open Friday.

    Sunday holiday:
        Following Monday is closed.
    """

    holiday = date(
        year,
        month,
        day,
    )

    dates = {
        holiday,
    }

    if holiday.weekday() == 6:
        dates.add(
            holiday
            + timedelta(days=1)
        )

    return dates


def _fed_holidays(
    year: int,
) -> set[date]:

    holidays: set[date] = set()


    # New Year's Day

    holidays |= _fixed_fed_holiday(
        year,
        1,
        1,
    )


    # Martin Luther King Jr. Day
    # Third Monday in January

    holidays.add(
        _nth_weekday(
            year,
            1,
            0,
            3,
        )
    )


    # Washington's Birthday
    # Third Monday in February

    holidays.add(
        _nth_weekday(
            year,
            2,
            0,
            3,
        )
    )


    # Memorial Day
    # Last Monday in May

    holidays.add(
        _last_weekday(
            year,
            5,
            0,
        )
    )


    # Juneteenth

    if year >= 2021:

        holidays |= _fixed_fed_holiday(
            year,
            6,
            19,
        )


    # Independence Day

    holidays |= _fixed_fed_holiday(
        year,
        7,
        4,
    )


    # Labor Day
    # First Monday in September

    holidays.add(
        _nth_weekday(
            year,
            9,
            0,
            1,
        )
    )


    # Columbus Day
    # Second Monday in October

    holidays.add(
        _nth_weekday(
            year,
            10,
            0,
            2,
        )
    )


    # Veterans Day

    holidays |= _fixed_fed_holiday(
        year,
        11,
        11,
    )


    # Thanksgiving
    # Fourth Thursday in November

    holidays.add(
        _nth_weekday(
            year,
            11,
            3,
            4,
        )
    )


    # Christmas

    holidays |= _fixed_fed_holiday(
        year,
        12,
        25,
    )


    return holidays


# =============================================================
# BUSINESS-DAY LOGIC
# =============================================================


def is_fed_business_day(
    target_date: date,
) -> bool:

    if target_date.weekday() >= 5:
        return False

    if (
        target_date
        in _fed_holidays(
            target_date.year
        )
    ):
        return False

    return True


def previous_fed_business_day(
    target_date: date,
) -> date:

    candidate = (
        target_date
        - timedelta(days=1)
    )

    while not is_fed_business_day(
        candidate
    ):
        candidate -= timedelta(days=1)

    return candidate


# =============================================================
# EXPECTED FUNDING DATE
# =============================================================


def expected_funding_observation_date(
    now: datetime | None = None,
) -> date:
    """
    Determine which SOFR/EFFR observation should
    reasonably be available right now.

    Since EFFR is the later-published rate, its
    publication schedule controls the common date.
    """

    if now is None:

        now_et = datetime.now(
            NEW_YORK
        )

    elif now.tzinfo is None:

        now_et = now.replace(
            tzinfo=NEW_YORK
        )

    else:

        now_et = now.astimezone(
            NEW_YORK
        )


    today = now_et.date()


    # If today is a Fed business day and we are
    # past the publication cutoff, today's publication
    # should be available.
    #
    # That publication represents the PRIOR
    # business day's market activity.

    if (
        is_fed_business_day(today)
        and now_et.time()
        >= FUNDING_PUBLICATION_CUTOFF
    ):

        publication_day = today

    else:

        publication_day = (
            previous_fed_business_day(
                today
            )
        )


    return previous_fed_business_day(
        publication_day
    )


# =============================================================
# FRESHNESS CALCULATION
# =============================================================


def _business_days_between(
    observation_date: date,
    expected_date: date,
) -> int:

    if observation_date >= expected_date:
        return 0


    stale_days = 0

    current = observation_date


    while current < expected_date:

        current += timedelta(days=1)

        if is_fed_business_day(
            current
        ):
            stale_days += 1


    return stale_days


def funding_data_freshness(
    observation_date: date,
    now: datetime | None = None,
) -> DataFreshness:

    expected_date = (
        expected_funding_observation_date(
            now=now
        )
    )


    stale_days = (
        _business_days_between(
            observation_date,
            expected_date,
        )
    )


    if stale_days == 0:

        label = "Current"

    elif stale_days == 1:

        label = (
            "1 business day stale"
        )

    else:

        label = (
            f"{stale_days} business days stale"
        )


    return DataFreshness(
        observation_date=
            observation_date,

        expected_observation_date=
            expected_date,

        business_days_stale=
            stale_days,

        is_current=
            stale_days == 0,

        label=
            label,
    )