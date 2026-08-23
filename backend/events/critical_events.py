from __future__ import annotations

from copy import deepcopy
from typing import Any


# =============================================================
# CRITICAL EVENT REGISTRY
# =============================================================
#
# These events are curated from validated historical
# Liquidity Monitor backtests.
#
# They are NOT generated dynamically from news.
#
# The purpose of this registry is to explain:
#
#   1. What the monitor identified
#   2. What was happening in markets
#   3. Why the episode matters
#   4. Where a user can read authoritative analysis
#
# =============================================================


MAJOR_CRITICAL_EVENTS: list[dict[str, Any]] = [

    # =========================================================
    # SEPTEMBER 2019
    # =========================================================

    {
        "id":
            "september-2019-repo",

        "period":
            "September 17–18, 2019",

        "title":
            "Repo Market Stress",

        "event_type":
            "Funding Stress",

        "severity":
            "Critical",

        "factors": [
            "Repo Market Pressure",
        ],

        "monitor_commentary": (
            "The Repo Market Pressure factor identified an "
            "acute secured-funding dislocation. Repo pricing "
            "moved dramatically away from unsecured funding, "
            "while SOFR dispersion and upper-tail pricing "
            "became extreme."
        ),

        "monitor_evidence": [
            (
                "SOFR–OBFR reached approximately +300 basis "
                "points on September 17."
            ),
            (
                "The SOFR interquartile range widened to "
                "approximately 85 basis points."
            ),
            (
                "The SOFR upper tail reached approximately "
                "375 basis points above the median rate."
            ),
            (
                "The event was detected primarily through "
                "funding-market plumbing rather than broad "
                "Treasury intermediation stress."
            ),
        ],

        "market_commentary": (
            "Large corporate tax payments and Treasury "
            "settlements removed cash from the banking "
            "system while primary dealers simultaneously "
            "needed additional financing. Reserve balances "
            "fell sharply and repo borrowing demand proved "
            "difficult to accommodate. SOFR moved above 5% "
            "on September 17 and the effective federal funds "
            "rate moved above the top of the Federal "
            "Reserve's target range."
        ),

        "why_it_matters": (
            "This episode demonstrates why funding-market "
            "liquidity cannot be inferred from Treasury "
            "market prices alone. The stress originated in "
            "the mechanics of cash availability and secured "
            "financing. The monitor's Repo Market Pressure "
            "factor is specifically designed to identify "
            "that type of dislocation."
        ),

        "sources": [
            {
                "title": (
                    "Federal Reserve — What Happened in "
                    "Money Markets in September 2019?"
                ),

                "url": (
                    "https://www.federalreserve.gov/"
                    "econres/notes/feds-notes/"
                    "what-happened-in-money-markets-in-"
                    "september-2019-20200227.html"
                ),
            },

            {
                "title": (
                    "Federal Reserve Bank of New York — "
                    "The Market Events of Mid-September 2019"
                ),

                "url": (
                    "https://www.newyorkfed.org/"
                    "research/staff_reports/sr918"
                ),
            },
        ],
    },


    # =========================================================
    # MARCH 2020
    # =========================================================

    {
        "id":
            "march-2020-treasury",

        "period":
            "March 11–18, 2020",

        "title":
            "Treasury Market Dysfunction",

        "event_type":
            "Market Functioning Stress",

        "severity":
            "Critical",

        "factors": [
            "Treasury Intermediation",
            "Repo Market Pressure",
        ],

        "monitor_commentary": (
            "Treasury Intermediation reached Critical as "
            "dealer balance-sheet adjustment, "
            "intermediation load and settlement friction "
            "became simultaneously abnormal. Repo Market "
            "Pressure also reached Critical during the "
            "broader episode."
        ),

        "monitor_evidence": [
            (
                "On March 11, balance-sheet adjustment "
                "registered approximately +2.08σ."
            ),
            (
                "Intermediation load registered "
                "approximately +2.66σ."
            ),
            (
                "Settlement friction registered "
                "approximately +3.53σ."
            ),
            (
                "By March 18, settlement friction had risen "
                "further to approximately +4.62σ even as "
                "the degree of multi-dimensional "
                "convergence began to ease."
            ),
        ],

        "market_commentary": (
            "The global dash for cash generated enormous "
            "sales of U.S. Treasury securities. Dealers "
            "absorbed large inventories while their "
            "balance-sheet capacity became increasingly "
            "constrained. Market depth collapsed, "
            "bid-ask spreads became unusually volatile and "
            "even normally liquid parts of the Treasury "
            "market experienced severe disruption. The "
            "Federal Reserve responded with very large "
            "Treasury purchases and other measures aimed "
            "at restoring market functioning."
        ),

        "why_it_matters": (
            "March 2020 is the clearest validation episode "
            "for the Treasury Intermediation factor. "
            "No single statistic caused the Critical "
            "classification. Instead, several independent "
            "dimensions deteriorated together — exactly the "
            "type of convergence the factor is designed "
            "to identify."
        ),

        "sources": [
            {
                "title": (
                    "Federal Reserve — Treasury Market "
                    "Functioning During the COVID-19 Shock"
                ),

                "url": (
                    "https://www.federalreserve.gov/"
                    "monetarypolicy/"
                    "2020-06-mpr-part2.htm"
                ),
            },

            {
                "title": (
                    "Federal Reserve Bank of New York — "
                    "The Federal Reserve's Market "
                    "Functioning Purchases"
                ),

                "url": (
                    "https://www.newyorkfed.org/"
                    "research/staff_reports/sr998"
                ),
            },
        ],
    },


    # =========================================================
    # OCTOBER 2025
    # =========================================================

    {
        "id":
            "october-2025-repo",

        "period":
            "October 16, 2025",

        "title":
            "Tightening Repo Conditions",

        "event_type":
            "Funding Stress",

        "severity":
            "Critical",

        "factors": [
            "Repo Market Pressure",
        ],

        "monitor_commentary": (
            "Repo Market Pressure reached Critical on a "
            "non-calendar date while Treasury "
            "Intermediation remained comparatively orderly. "
            "The divergence indicated that the primary "
            "problem was secured funding pressure rather "
            "than broad Treasury market dysfunction."
        ),

        "monitor_evidence": [
            (
                "Repo-market diagnostics became materially "
                "abnormal without simultaneous confirmation "
                "from Treasury Intermediation."
            ),
            (
                "The event therefore remained concentrated "
                "in funding-market plumbing rather than "
                "being classified as broad Treasury "
                "market dysfunction."
            ),
            (
                "Subsequent Federal Reserve discussion "
                "identified tightening money-market "
                "conditions as reserve balances moved "
                "closer to the ample region."
            ),
        ],

        "market_commentary": (
            "During the period surrounding the October 2025 "
            "FOMC meeting, Treasury repo rates moved notably "
            "higher relative to the interest rate on reserve "
            "balances. Market participants attributed the "
            "move to declining available liquidity, "
            "continued Federal Reserve balance-sheet runoff "
            "and large Treasury debt issuance. Standing Repo "
            "Facility usage also became more frequent, "
            "although volumes remained limited."
        ),

        "why_it_matters": (
            "The episode demonstrates the value of keeping "
            "Repo Market Pressure separate from Treasury "
            "Intermediation. Funding conditions can become "
            "materially stressed before, or without, a "
            "corresponding breakdown in Treasury market "
            "functioning."
        ),

        "sources": [
            {
                "title": (
                    "Federal Reserve — Minutes of the "
                    "October 28–29, 2025 FOMC Meeting"
                ),

                "url": (
                    "https://www.federalreserve.gov/"
                    "monetarypolicy/"
                    "fomcminutes20251029.htm"
                ),
            },

            {
                "title": (
                    "Federal Reserve — October 29, 2025 "
                    "Monetary Policy Implementation Note"
                ),

                "url": (
                    "https://www.federalreserve.gov/"
                    "newsevents/pressreleases/"
                    "monetary20251029a1.htm"
                ),
            },
        ],
    },
]


# =============================================================
# CALENDAR-TURN CRITICAL EVENTS
# =============================================================
#
# These are preserved because expected stress is still stress.
#
# They are shown separately from major market-disruption
# episodes so that users do not confuse a quarter-end
# balance-sheet event with a financial crisis.
#
# =============================================================


CALENDAR_TURN_EVENTS: list[dict[str, Any]] = [

    {
        "period":
            "December 31, 2018 – January 2, 2019",

        "title":
            "Year-End Repo Pressure",

        "event_type":
            "Year-End",

        "factor":
            "Repo Market Pressure",

        "commentary": (
            "The monitor identified pronounced secured-"
            "funding pressure across the year-end reporting "
            "turn. The severity is retained even though the "
            "calendar context provides an important "
            "explanation for the move."
        ),
    },

    {
        "period":
            "March 29, 2019",

        "title":
            "Quarter-End Repo Pressure",

        "event_type":
            "Quarter-End",

        "factor":
            "Repo Market Pressure",

        "commentary": (
            "Repo-market conditions became unusually tight "
            "around the first-quarter reporting turn."
        ),
    },

    {
        "period":
            "December 28–29, 2023",

        "title":
            "Year-End Funding Pressure",

        "event_type":
            "Year-End",

        "factor":
            "Repo Market Pressure",

        "commentary": (
            "Secured-funding diagnostics became unusually "
            "elevated immediately ahead of the year-end "
            "balance-sheet reporting date."
        ),
    },

    {
        "period":
            "September 30 – October 1, 2024",

        "title":
            "Quarter-End Funding Pressure",

        "event_type":
            "Quarter-End",

        "factor":
            "Repo Market Pressure",

        "commentary": (
            "The monitor registered Critical repo pressure "
            "at the quarter-end turn and into the first "
            "business day afterward."
        ),
    },

    {
        "period":
            "June 30 – July 1, 2025",

        "title":
            "Quarter-End Funding Pressure",

        "event_type":
            "Quarter-End",

        "factor":
            "Repo Market Pressure",

        "commentary": (
            "Secured-funding conditions became materially "
            "abnormal around the mid-year reporting turn."
        ),
    },

    {
        "period":
            "October 30–31, 2025",

        "title":
            "Month-End Repo Pressure",

        "event_type":
            "Month-End",

        "factor":
            "Repo Market Pressure",

        "commentary": (
            "Repo-market pressure intensified into the "
            "October month-end turn shortly after the "
            "broader tightening episode earlier that month."
        ),
    },

    {
        "period":
            "December 1, 2025",

        "title":
            "Post-Month-End Repo Pressure",

        "event_type":
            "Post Month-End",

        "factor":
            "Repo Market Pressure",

        "commentary": (
            "Elevated repo-market conditions persisted into "
            "the first business day following month-end."
        ),
    },

    {
        "period":
            "December 31, 2025",

        "title":
            "Year-End Repo Pressure",

        "event_type":
            "Year-End",

        "factor":
            "Repo Market Pressure",

        "commentary": (
            "The monitor again identified material secured-"
            "funding pressure at the year-end reporting "
            "turn."
        ),
    },
]


# =============================================================
# SHARED CALENDAR-TURN SOURCE
# =============================================================


CALENDAR_SOURCE = {
    "title":
        "Federal Reserve Bank of New York — SOFR Historical Data",

    "url":
        "https://www.newyorkfed.org/markets/reference-rates/sofr",
}


# =============================================================
# PUBLIC API
# =============================================================


def get_major_critical_events(
) -> list[dict[str, Any]]:
    """
    Return a defensive copy of curated major
    Critical events.
    """

    return deepcopy(
        MAJOR_CRITICAL_EVENTS
    )


def get_calendar_turn_events(
) -> list[dict[str, Any]]:
    """
    Return calendar-turn Critical episodes.

    Each event receives the common NY Fed
    reference-rate source.
    """

    events = deepcopy(
        CALENDAR_TURN_EVENTS
    )

    for event in events:

        event[
            "source"
        ] = deepcopy(
            CALENDAR_SOURCE
        )

    return events