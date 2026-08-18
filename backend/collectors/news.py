from __future__ import annotations

import html
import re
import xml.etree.ElementTree as ET

from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import httpx


GOOGLE_NEWS_RSS_URL = (
    "https://news.google.com/rss/search"
)


# =============================================================
# TARGETED SEARCHES
# =============================================================

NEWS_SEARCHES = {
    "Funding / Repo": (
        '("repo market" OR '
        '"repo rates" OR '
        '"funding markets" OR '
        '"funding pressure" OR '
        '"standing repo facility" OR '
        '"SOFR" liquidity OR '
        '"SOFR" repo) '
        'when:30d'
    ),

    "Treasury Liquidity": (
        '("Treasury basis trade" OR '
        '"Treasury market liquidity" OR '
        '"Treasury market" repo OR '
        '"dealer balance sheet" Treasury OR '
        '"Treasury market" leverage) '
        'when:30d'
    ),

    "Reserves / TGA": (
        '("bank reserves" liquidity OR '
        '"reserve balances" liquidity OR '
        '"Treasury General Account" liquidity OR '
        '"TGA" reserves) '
        'when:30d'
    ),
}


@dataclass(frozen=True)
class NewsArticle:
    title: str

    url: str

    source: str

    source_url: str | None

    published_at: datetime | None

    topic: str

    summary: str | None


# =============================================================
# HELPERS
# =============================================================


def _clean_html(
    value: str | None,
) -> str | None:

    if not value:
        return None

    text = re.sub(
        r"<[^>]+>",
        " ",
        value,
    )

    text = html.unescape(
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    ).strip()

    return text or None


def _parse_date(
    value: str | None,
) -> datetime | None:

    if not value:
        return None

    try:

        parsed = (
            parsedate_to_datetime(
                value
            )
        )

        if parsed.tzinfo is None:

            parsed = (
                parsed.replace(
                    tzinfo=timezone.utc
                )
            )

        return parsed.astimezone(
            timezone.utc
        )

    except Exception:

        return None


def _normalize_title(
    title: str,
) -> str:

    title = title.lower()

    title = re.sub(
        r"[^a-z0-9\s]",
        " ",
        title,
    )

    title = re.sub(
        r"\s+",
        " ",
        title,
    )

    return title.strip()


# =============================================================
# ONE RSS SEARCH
# =============================================================


def _fetch_search(
    topic: str,
    query: str,
) -> list[NewsArticle]:

    try:

        response = httpx.get(
            GOOGLE_NEWS_RSS_URL,

            params={
                "q": query,
                "hl": "en-US",
                "gl": "US",
                "ceid": "US:en",
            },

            headers={
                "User-Agent":
                    "Mozilla/5.0 "
                    "LiquidityMonitor/1.0"
            },

            timeout=20.0,

            follow_redirects=True,
        )

        response.raise_for_status()

    except httpx.HTTPError as exc:

        print(
            f"News search unavailable "
            f"for {topic}: {exc}"
        )

        return []


    try:

        root = ET.fromstring(
            response.text
        )

    except ET.ParseError as exc:

        print(
            f"Could not parse "
            f"{topic} RSS: {exc}"
        )

        return []


    articles: list[
        NewsArticle
    ] = []


    for item in root.findall(
        "./channel/item"
    ):

        title = (
            item.findtext("title")
            or ""
        ).strip()

        url = (
            item.findtext("link")
            or ""
        ).strip()


        if not title or not url:
            continue


        source_element = (
            item.find("source")
        )


        if source_element is not None:

            source = (
                source_element.text
                or "Unknown"
            ).strip()

            source_url = (
                source_element.attrib.get(
                    "url"
                )
            )

        else:

            source = "Unknown"
            source_url = None


        # Remove Google News source suffix.

        suffix = (
            f" - {source}"
        )

        if (
            source != "Unknown"
            and title.endswith(
                suffix
            )
        ):

            title = title[
                :-len(suffix)
            ].strip()


        articles.append(
            NewsArticle(
                title=title,

                url=url,

                source=source,

                source_url=
                    source_url,

                published_at=
                    _parse_date(
                        item.findtext(
                            "pubDate"
                        )
                    ),

                topic=topic,

                summary=
                    _clean_html(
                        item.findtext(
                            "description"
                        )
                    ),
            )
        )


    return articles


# =============================================================
# MAIN COLLECTOR
# =============================================================


def fetch_liquidity_news(
    limit: int = 40,
) -> list[NewsArticle]:

    all_articles: list[
        NewsArticle
    ] = []


    for topic, query in (
        NEWS_SEARCHES.items()
    ):

        articles = (
            _fetch_search(
                topic=topic,
                query=query,
            )
        )

        all_articles.extend(
            articles
        )


    # ---------------------------------------------------------
    # DEDUPLICATE
    # ---------------------------------------------------------

    articles_by_title: dict[
        str,
        NewsArticle,
    ] = {}


    for article in all_articles:

        key = _normalize_title(
            article.title
        )


        if key not in articles_by_title:

            articles_by_title[
                key
            ] = article


    articles = list(
        articles_by_title.values()
    )


    # ---------------------------------------------------------
    # SORT NEWEST FIRST
    # ---------------------------------------------------------

    articles.sort(
        key=lambda article: (
            article.published_at
            or datetime.min.replace(
                tzinfo=timezone.utc
            )
        ),
        reverse=True,
    )


    return articles[
        :limit
    ]


# =============================================================
# TERMINAL TEST
# =============================================================


def print_liquidity_news() -> None:

    articles = (
        fetch_liquidity_news(
            limit=40
        )
    )


    print()
    print(
        "Liquidity Monitor News Feed"
    )
    print("=" * 72)

    print(
        f"Articles found: "
        f"{len(articles)}"
    )


    for number, article in enumerate(
        articles,
        start=1,
    ):

        print()

        print(
            f"{number}. "
            f"{article.title}"
        )

        print(
            f"   Source: "
            f"{article.source}"
        )

        print(
            f"   Topic:  "
            f"{article.topic}"
        )


        if article.published_at:

            print(
                f"   Date:   "
                f"{article.published_at}"
            )


        print(
            f"   URL:    "
            f"{article.url}"
        )


if __name__ == "__main__":
    print_liquidity_news()