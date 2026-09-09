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


# =============================================================
# PUBLICATION CUTOFFS
# =============================================================

# EFFR is normally published around 9:00 a.m. ET.
#
# Since the funding snapshot requires a common SOFR/EFFR
# observation date, EFFR controls the expected daily date.
#
# Allow a small buffer before considering the prior
# business day's observation due.

FUNDING_PUBLICATION_CUTOFF = time(
    hour=9,
    minute=15,
)


# Federal Reserve H.4.1 data are normally released
# each Thursday at approximately 4:30 p.m. ET.
#
# Reserve balances and the Treasury General Account
# are Wednesday observations contained in that release.
#
# Allow a small buffer before considering the newest
# weekly observation due.

SYSTEM_PUBLICATION_CUTOFF = time(
    hour=16,
    minute=45,
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
        weekday
        - current.weekday()
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

    while (
        current.weekday()
        != weekday
    ):
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


def _next_fed_business_day(
    target_date: date,
) -> date:
    """
    Return target_date when it is a Fed business day.

    Otherwise advance until the next Fed business day.
    """

    candidate = target_date

    while not is_fed_business_day(
        candidate
    ):
        candidate += timedelta(days=1)

    return candidate


def _normalize_now(
    now: datetime | None,
) -> datetime:
    """
    Normalize an optional datetime to New York time.
    """

    if now is None:
        return datetime.now(
            NEW_YORK
        )

    if now.tzinfo is None:
        return now.replace(
            tzinfo=NEW_YORK
        )

    return now.astimezone(
        NEW_YORK
    )


# =============================================================
# EXPECTED FUNDING DATE
# =============================================================


def expected_funding_observation_date(
    now: datetime | None = None,
) -> date:
    """
    Determine which common SOFR/EFFR observation
    should reasonably be available right now.

    Since EFFR is the later-published rate, its
    publication schedule controls the common date.
    """

    now_et = _normalize_now(
        now
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
# EXPECTED SYSTEM-LIQUIDITY DATE
# =============================================================


def _most_recent_wednesday(
    target_date: date,
) -> date:
    """
    Return the most recent Wednesday on or
    before target_date.
    """

    days_since_wednesday = (
        target_date.weekday()
        - 2
    ) % 7

    return (
        target_date
        - timedelta(
            days=days_since_wednesday
        )
    )


def _system_publication_date(
    observation_date: date,
) -> date:
    """
    Determine the publication date associated with
    one Wednesday H.4.1 observation.

    Normal publication is Thursday.

    If Thursday is a Federal Reserve holiday,
    publication shifts to the next business day.
    """

    normal_publication_date = (
        observation_date
        + timedelta(days=1)
    )

    return _next_fed_business_day(
        normal_publication_date
    )


def expected_system_liquidity_observation_date(
    now: datetime | None = None,
) -> date:
    """
    Determine which weekly H.4.1 observation should
    reasonably be available right now.

    Reserve balances and the Treasury General Account
    are Wednesday observations normally published
    Thursday afternoon.

    Before the current week's H.4.1 release is due,
    the previous Wednesday remains the expected
    observation.

    After publication, the current Wednesday becomes
    the expected observation.
    """

    now_et = _normalize_now(
        now
    )

    candidate_observation_date = (
        _most_recent_wednesday(
            now_et.date()
        )
    )

    # Normally only the current and prior Wednesday
    # need to be examined. Looping allows the logic
    # to remain robust around holidays.

    for _ in range(4):

        publication_date = (
            _system_publication_date(
                candidate_observation_date
            )
        )

        publication_datetime = (
            datetime.combine(
                publication_date,
                SYSTEM_PUBLICATION_CUTOFF,
                tzinfo=NEW_YORK,
            )
        )

        if (
            now_et
            >= publication_datetime
        ):
            return (
                candidate_observation_date
            )

        candidate_observation_date -= (
            timedelta(days=7)
        )

    raise RuntimeError(
        "Unable to determine expected "
        "system-liquidity observation date."
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


def _weekly_releases_between(
    observation_date: date,
    expected_date: date,
) -> int:
    """
    Count how many weekly observation cycles
    separate the stored observation from the
    expected H.4.1 observation.
    """

    if observation_date >= expected_date:
        return 0

    days_stale = (
        expected_date
        - observation_date
    ).days

    return max(
        1,
        (
            days_stale
            + 6
        )
        // 7,
    )


# =============================================================
# FUNDING FRESHNESS
# =============================================================


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
            f"{stale_days} "
            "business days stale"
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


# =============================================================
# SYSTEM-LIQUIDITY FRESHNESS
# =============================================================


def system_liquidity_data_freshness(
    observation_date: date,
    now: datetime | None = None,
) -> DataFreshness:
    """
    Evaluate freshness of the weekly H.4.1
    system-liquidity observation.

    A Wednesday observation remains current until
    the following weekly release becomes due.

    This prevents normal weekly publication timing
    from being incorrectly labeled stale simply
    because several calendar days have passed.
    """

    expected_date = (
        expected_system_liquidity_observation_date(
            now=now
        )
    )

    stale_business_days = (
        _business_days_between(
            observation_date,
            expected_date,
        )
    )

    stale_releases = (
        _weekly_releases_between(
            observation_date,
            expected_date,
        )
    )

    if stale_releases == 0:
        label = (
            "Current weekly release"
        )

    elif stale_releases == 1:
        label = (
            "1 weekly release stale"
        )

    else:
        label = (
            f"{stale_releases} "
            "weekly releases stale"
        )

    return DataFreshness(
        observation_date=
            observation_date,

        expected_observation_date=
            expected_date,

        business_days_stale=
            stale_business_days,

        is_current=
            stale_releases == 0,

        label=
            label,
    )