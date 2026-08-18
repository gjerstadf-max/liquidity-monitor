from __future__ import annotations

import re

from dataclasses import dataclass
from datetime import datetime, timezone
from difflib import SequenceMatcher

from backend.collectors.news import (
    NewsArticle,
    fetch_liquidity_news,
)


# =============================================================
# SOURCE QUALITY
# =============================================================

SOURCE_SCORES = {
    "Reuters": 6,
    "Bloomberg": 6,
    "Financial Times": 6,
    "The Wall Street Journal": 6,
    "Wall Street Journal": 6,

    "CNBC": 5,
    "MarketWatch": 4,
    "Barron's": 4,
    "The Economist": 4,

    "Yahoo Finance": 3,
    "Newsquawk": 3,
}


# =============================================================
# TOPIC IMPORTANCE
# =============================================================

TOPIC_SCORES = {
    "Funding / Repo": 5,
    "Reserves / TGA": 5,
    "Treasury Liquidity": 5,
    "Money Markets": 4,
    "Other": 0,
}


# =============================================================
# TRUE LIQUIDITY LANGUAGE
# =============================================================

HIGH_VALUE_PHRASES = [
    "repo market",
    "repo rates",
    "repo funding",
    "standing repo facility",
    "funding pressure",
    "funding stress",
    "money market stress",
    "reserve balances",
    "bank reserves",
    "treasury general account",
    "basis trade",
    "dealer balance sheet",
    "market liquidity",
    "treasury market liquidity",
    "short-term funding",
]


MEDIUM_VALUE_PHRASES = [
    "sofr",
    "money markets",
    "liquidity",
    "treasury issuance",
    "treasury financing",
    "funding conditions",
    "funding markets",
    "cash balances",
]


# =============================================================
# FALSE POSITIVES
# =============================================================

# SOFR is frequently just the reference rate on a loan
# or security. These stories are not market-liquidity news.

BENCHMARK_REFERENCE_PATTERNS = [
    r"priced .* over sofr",
    r"priced .* to sofr",
    r"pricing .* over sofr",
    r"guidance .* sofr",
    r"bps? .* sofr",
    r"basis points .* sofr",
    r"loan .* sofr",
    r"notes .* sofr",
    r"bond .* sofr",
    r"facility .* sofr",
]


# We already collect TGA directly from official sources.
# Automated daily balance recaps are data duplication,
# not market interpretation.

RAW_DATA_PATTERNS = [
    r"tga balance .* daily treasury statement",
    r"treasury general account balance .* daily treasury statement",
    r"daily treasury statement .* tga",
]


NOISE_PHRASES = [
    "crypto",
    "bitcoin",
    "mortgage rates",
    "personal loan",
    "consumer loan",
    "startup funding",
    "venture funding",
    "real estate financing",
]


@dataclass(frozen=True)
class RankedNewsArticle:
    article: NewsArticle

    relevance_score: int

    source_score: int
    topic_score: int
    recency_score: int
    keyword_score: int
    noise_penalty: int


# =============================================================
# EXCLUSIONS
# =============================================================


def _article_text(
    article: NewsArticle,
) -> str:

    return (
        article.title
        + " "
        + (article.summary or "")
    ).lower()


def _matches_pattern(
    text: str,
    patterns: list[str],
) -> bool:

    return any(
        re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        )
        for pattern in patterns
    )


def _is_benchmark_reference(
    article: NewsArticle,
) -> bool:

    text = _article_text(
        article
    )

    return _matches_pattern(
        text,
        BENCHMARK_REFERENCE_PATTERNS,
    )


def _is_raw_data_update(
    article: NewsArticle,
) -> bool:

    text = _article_text(
        article
    )

    return _matches_pattern(
        text,
        RAW_DATA_PATTERNS,
    )


# =============================================================
# SCORING
# =============================================================


def _source_score(
    source: str,
) -> int:

    if source in SOURCE_SCORES:
        return SOURCE_SCORES[source]

    source_lower = (
        source.lower()
    )

    for name, score in (
        SOURCE_SCORES.items()
    ):

        if name.lower() in source_lower:
            return score

    # Unknown sources get very little credit.
    return 0


def _recency_score(
    published_at: datetime | None,
) -> int:

    if published_at is None:
        return 0

    now = datetime.now(
        timezone.utc
    )

    age_hours = (
        now - published_at
    ).total_seconds() / 3600


    if age_hours <= 24:
        return 5

    if age_hours <= 48:
        return 4

    if age_hours <= 72:
        return 3

    if age_hours <= 120:
        return 2

    if age_hours <= 168:
        return 1

    return 0


def _keyword_score(
    article: NewsArticle,
) -> int:

    text = _article_text(
        article
    )

    score = 0


    for phrase in HIGH_VALUE_PHRASES:

        if phrase in text:
            score += 3


    for phrase in MEDIUM_VALUE_PHRASES:

        if phrase in text:
            score += 1


    return min(
        score,
        12,
    )


def _noise_penalty(
    article: NewsArticle,
) -> int:

    text = _article_text(
        article
    )

    penalty = 0


    for phrase in NOISE_PHRASES:

        if phrase in text:
            penalty += 5


    return min(
        penalty,
        15,
    )


def score_article(
    article: NewsArticle,
) -> RankedNewsArticle:

    source = _source_score(
        article.source
    )

    topic = TOPIC_SCORES.get(
        article.topic,
        0,
    )

    recency = _recency_score(
        article.published_at
    )

    keywords = _keyword_score(
        article
    )

    noise = _noise_penalty(
        article
    )


    total = (
        source
        + topic
        + recency
        + keywords
        - noise
    )


    return RankedNewsArticle(
        article=article,

        relevance_score=total,

        source_score=source,
        topic_score=topic,
        recency_score=recency,
        keyword_score=keywords,
        noise_penalty=noise,
    )


# =============================================================
# DUPLICATES
# =============================================================


def _normalize_title(
    title: str,
) -> str:

    title = title.lower()

    title = re.sub(
        r"[^a-z0-9\s]",
        "",
        title,
    )

    title = re.sub(
        r"\s+",
        " ",
        title,
    )

    return title.strip()


def _titles_are_similar(
    title_a: str,
    title_b: str,
) -> bool:

    normalized_a = (
        _normalize_title(
            title_a
        )
    )

    normalized_b = (
        _normalize_title(
            title_b
        )
    )


    ratio = SequenceMatcher(
        None,
        normalized_a,
        normalized_b,
    ).ratio()


    return ratio >= 0.75


def _remove_duplicates(
    ranked_articles: list[
        RankedNewsArticle
    ],
) -> list[RankedNewsArticle]:

    unique: list[
        RankedNewsArticle
    ] = []


    for candidate in ranked_articles:

        duplicate = False


        for existing in unique:

            if _titles_are_similar(
                candidate.article.title,
                existing.article.title,
            ):

                duplicate = True
                break


        if not duplicate:

            unique.append(
                candidate
            )


    return unique


# =============================================================
# MAIN RANKING
# =============================================================


def rank_liquidity_news(
    raw_limit: int = 40,
    final_limit: int = 8,
    minimum_score: int = 10,
) -> list[RankedNewsArticle]:

    articles = fetch_liquidity_news(
        limit=raw_limit
    )


    # Remove stories that merely reference SOFR
    # as a benchmark rate.

    articles = [
        article
        for article in articles
        if not _is_benchmark_reference(
            article
        )
    ]


    # Remove automated TGA/raw-data recaps.
    # Our quantitative pipeline already captures
    # these data directly.

    articles = [
        article
        for article in articles
        if not _is_raw_data_update(
            article
        )
    ]


    ranked = [
        score_article(
            article
        )
        for article in articles
    ]


    ranked = [
        article
        for article in ranked
        if article.relevance_score
        >= minimum_score
    ]


    ranked.sort(
        key=lambda item:
            item.relevance_score,
        reverse=True,
    )


    ranked = _remove_duplicates(
        ranked
    )


    return ranked[
        :final_limit
    ]


# =============================================================
# TERMINAL OUTPUT
# =============================================================


def print_ranked_news() -> None:

    ranked = (
        rank_liquidity_news()
    )


    print()
    print(
        "Liquidity Monitor — Relevant News"
    )
    print("=" * 72)


    if not ranked:

        print()
        print(
            "No sufficiently relevant "
            "liquidity stories found."
        )

        return


    for number, item in enumerate(
        ranked,
        start=1,
    ):

        article = item.article


        print()

        print(
            f"{number}. "
            f"{article.title}"
        )

        print(
            f"   Source:    "
            f"{article.source}"
        )

        print(
            f"   Topic:     "
            f"{article.topic}"
        )

        print(
            f"   Relevance: "
            f"{item.relevance_score}"
        )

        print(
            "   Score:     "
            f"source {item.source_score}, "
            f"topic {item.topic_score}, "
            f"recency {item.recency_score}, "
            f"keywords {item.keyword_score}, "
            f"noise -{item.noise_penalty}"
        )

        print(
            f"   URL:       "
            f"{article.url}"
        )


if __name__ == "__main__":
    print_ranked_news()