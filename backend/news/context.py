from __future__ import annotations

from typing import Any


MAX_CONTEXT_ITEMS = 2


# Higher threshold for structural stories because
# we do not want ordinary "basis trade" discussion
# appearing on the homepage every day.

MATERIAL_THRESHOLDS = {
    "Current Stress": 14,
    "Policy Response": 14,
    "Structural Risk": 17,
}


ALLOWED_TOPICS = {
    "Funding / Repo",
    "Money Markets",
    "Reserves / TGA",
    "Treasury Liquidity",
}


def _relevance_score(
    story: dict[str, Any],
) -> int:

    try:
        return int(
            story
            .get("ranked_article", {})
            .get("relevance_score", 0)
        )

    except (
        TypeError,
        ValueError,
    ):
        return 0


def _article(
    story: dict[str, Any],
) -> dict[str, Any]:

    article = (
        story
        .get("ranked_article", {})
        .get("article", {})
    )

    if not isinstance(
        article,
        dict,
    ):
        return {}

    return article


def _is_material(
    story: dict[str, Any],
) -> bool:

    story_type = (
        story.get(
            "story_type"
        )
    )

    threshold = (
        MATERIAL_THRESHOLDS.get(
            story_type
        )
    )

    if threshold is None:
        return False

    article = (
        _article(
            story
        )
    )

    topic = (
        article.get(
            "topic"
        )
    )

    if topic not in ALLOWED_TOPICS:
        return False

    return (
        _relevance_score(
            story
        )
        >= threshold
    )


def build_market_context(
    market_narrative: dict[str, Any],
) -> dict[str, Any]:
    """
    Convert the detailed stored news narrative into
    a deliberately small homepage Market Context.

    News remains contextual only. It does not change
    quantitative factor signals or assessments.
    """

    if not market_narrative.get(
        "available",
        False,
    ):

        return {
            "available": False,

            "summary": (
                "Market context is temporarily unavailable. "
                "The quantitative liquidity assessment "
                "remains fully operational."
            ),

            "items": [],
        }


    stories = (
        market_narrative.get(
            "stories",
            []
        )
    )


    candidates = [
        story
        for story in stories
        if (
            isinstance(
                story,
                dict,
            )
            and
            _is_material(
                story
            )
        )
    ]


    candidates.sort(
        key=_relevance_score,
        reverse=True,
    )


    selected: list[
        dict[str, Any]
    ] = []

    seen_topics: set[str] = set()


    for story in candidates:

        article = (
            _article(
                story
            )
        )

        title = str(
            article.get(
                "title",
                ""
            )
        ).strip()

        topic = str(
            article.get(
                "topic",
                ""
            )
        ).strip()

        url = str(
            article.get(
                "url",
                ""
            )
        ).strip()


        if not title:
            continue


        # Keep the homepage from showing two versions
        # of essentially the same liquidity issue.

        if topic in seen_topics:
            continue


        seen_topics.add(
            topic
        )


        selected.append(
            {
                "text":
                    title,

                "url":
                    url,

                "topic":
                    topic,
            }
        )


        if len(
            selected
        ) >= MAX_CONTEXT_ITEMS:
            break


    if not selected:

        return {
            "available": True,

            "summary": (
                "No material market developments currently "
                "require additional context beyond the "
                "quantitative liquidity assessment."
            ),

            "items": [],
        }


    return {
        "available": True,

        "summary": (
            "Selected external developments relevant "
            "to current liquidity conditions:"
        ),

        "items":
            selected,
    }