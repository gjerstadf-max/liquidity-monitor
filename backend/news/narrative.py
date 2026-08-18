from __future__ import annotations

import re

from dataclasses import dataclass

from backend.news.relevance import (
    RankedNewsArticle,
    rank_liquidity_news,
)
from backend.signals.funding import (
    evaluate_funding_signal,
)
from backend.signals.system_liquidity import (
    evaluate_system_liquidity_signal,
)


# =============================================================
# STORY LANGUAGE
# =============================================================

CURRENT_PRESSURE_PHRASES = [
    "funding pressure",
    "funding stress",
    "liquidity pressure",
    "liquidity stress",
    "repo pressure",
    "repo rates rise",
    "repo rates spike",
    "funding rates rise",
    "tightening liquidity",
    "reserve drain",
]


CURRENT_EASING_PHRASES = [
    "funding conditions ease",
    "funding markets orderly",
    "repo markets orderly",
    "repo rates fall",
    "ample liquidity",
    "abundant liquidity",
    "liquidity improves",
]


STRUCTURAL_RISK_PHRASES = [
    "basis trade",
    "leverage",
    "leveraged",
    "hedge fund",
    "dealer balance sheet",
    "balance sheet constraint",
    "market fragility",
    "financial stability",
    "nonbank",
    "margin call",
    "repo dependence",
    "repo financing",
    "treasury market liquidity",
]


POLICY_RESPONSE_PHRASES = [
    "standing repo facility",
    "repo facility",
    "treasury repo",
    "repo entry",
    "repo operations",
    "liquidity facility",
    "federal reserve facility",
    "fed intervention",
    "treasury weighs",
    "treasury considers",
    "treasury plans",
]


# =============================================================
# DATA OBJECTS
# =============================================================


@dataclass(frozen=True)
class NarrativeStory:
    ranked_article: RankedNewsArticle

    story_type: str

    matched_signal: str | None

    directional_relationship: str

    pressure_score: int
    easing_score: int


@dataclass(frozen=True)
class MarketNarrative:
    market_attention: str

    directional_confirmation: str

    funding_severity: str
    system_liquidity_severity: str

    current_stress_count: int
    easing_count: int
    structural_risk_count: int
    policy_response_count: int
    background_count: int

    confirming_count: int
    contradicting_count: int

    confirming_weight: int
    contradicting_weight: int
    attention_weight: int

    summary: str

    stories: list[NarrativeStory]


# =============================================================
# HELPERS
# =============================================================


def _article_text(
    article: RankedNewsArticle,
) -> str:

    return (
        article.article.title
        + ". "
        + (
            article.article.summary
            or ""
        )
    ).lower()


def _contains_any(
    text: str,
    phrases: list[str],
) -> bool:

    return any(
        phrase in text
        for phrase in phrases
    )


# =============================================================
# CURRENT DIRECTION
# =============================================================


def _direction_scores(
    article: RankedNewsArticle,
) -> tuple[int, int]:

    text = _article_text(
        article
    )

    pressure_score = 0
    easing_score = 0


    for phrase in CURRENT_PRESSURE_PHRASES:

        if phrase in text:
            pressure_score += 3


    for phrase in CURRENT_EASING_PHRASES:

        if phrase in text:
            easing_score += 3


    chunks = re.split(
        r"[.!?;:\n]+",
        text,
    )


    for chunk in chunks:

        chunk = chunk.strip()

        if not chunk:
            continue


        # -----------------------------------------------------
        # FUNDING / REPO
        # -----------------------------------------------------

        funding_context = (
            "repo" in chunk
            or "sofr" in chunk
            or "funding market" in chunk
            or "money market" in chunk
        )


        if funding_context:

            if _contains_any(
                chunk,
                [
                    "rising",
                    "higher",
                    "spike",
                    "surge",
                    "tightening",
                    "stress",
                    "strain",
                    "pressure",
                    "volatile",
                ],
            ):

                pressure_score += 2


            if _contains_any(
                chunk,
                [
                    "falling",
                    "lower",
                    "easing",
                    "orderly",
                    "stable",
                    "normalizing",
                ],
            ):

                easing_score += 2


        # -----------------------------------------------------
        # RESERVES
        # -----------------------------------------------------

        reserve_context = (
            "reserve balance" in chunk
            or "bank reserves" in chunk
        )


        if reserve_context:

            if _contains_any(
                chunk,
                [
                    "fall",
                    "falling",
                    "decline",
                    "declining",
                    "drop",
                    "drain",
                    "draining",
                    "lower",
                ],
            ):

                pressure_score += 2


            if _contains_any(
                chunk,
                [
                    "rise",
                    "rising",
                    "increase",
                    "increasing",
                    "rebuild",
                    "higher",
                ],
            ):

                easing_score += 2


        # -----------------------------------------------------
        # TGA
        #
        # Rising TGA drains reserves.
        # Falling TGA adds reserves.
        # -----------------------------------------------------

        tga_context = (
            "treasury general account"
            in chunk
            or " tga " in f" {chunk} "
        )


        if tga_context:

            if _contains_any(
                chunk,
                [
                    "rise",
                    "rising",
                    "increase",
                    "increasing",
                    "rebuild",
                    "rebuilding",
                    "higher",
                ],
            ):

                pressure_score += 2


            if _contains_any(
                chunk,
                [
                    "fall",
                    "falling",
                    "decline",
                    "declining",
                    "drawdown",
                    "lower",
                ],
            ):

                easing_score += 2


    return (
        pressure_score,
        easing_score,
    )


# =============================================================
# STORY TYPE
# =============================================================


def _story_type(
    article: RankedNewsArticle,
) -> tuple[str, int, int]:

    text = _article_text(
        article
    )

    (
        pressure_score,
        easing_score,
    ) = _direction_scores(
        article
    )


    # Policy response takes priority because it tells us
    # authorities are addressing a market mechanism, not
    # necessarily that acute stress already exists.

    if _contains_any(
        text,
        POLICY_RESPONSE_PHRASES,
    ):

        return (
            "Policy Response",
            pressure_score,
            easing_score,
        )


    # Structural vulnerabilities are useful context but
    # are not treated as evidence of current stress.

    if _contains_any(
        text,
        STRUCTURAL_RISK_PHRASES,
    ):

        return (
            "Structural Risk",
            pressure_score,
            easing_score,
        )


    if (
        pressure_score > easing_score
        and pressure_score > 0
    ):

        return (
            "Current Stress",
            pressure_score,
            easing_score,
        )


    if (
        easing_score > pressure_score
        and easing_score > 0
    ):

        return (
            "Easing",
            pressure_score,
            easing_score,
        )


    return (
        "Background",
        pressure_score,
        easing_score,
    )


# =============================================================
# SIGNAL MATCHING
# =============================================================


def _matched_signal(
    topic: str,
) -> str | None:

    if topic in {
        "Funding / Repo",
        "Money Markets",
    }:

        return "Funding"


    if topic == "Reserves / TGA":

        return "System Liquidity"


    return None


# =============================================================
# DIRECTIONAL RELATIONSHIP
# =============================================================


def _directional_relationship(
    story_type: str,
    matched_signal: str | None,
    funding_severity: str,
    system_severity: str,
) -> str:

    # Structural risk and policy stories intentionally
    # do not confirm or contradict current data.

    if story_type not in {
        "Current Stress",
        "Easing",
    }:

        return "NOT_DIRECTIONAL"


    if matched_signal is None:

        return "NOT_DIRECTIONAL"


    if matched_signal == "Funding":

        severity = funding_severity

    else:

        severity = system_severity


    quantitative_pressure = (
        severity != "Normal"
    )


    if story_type == "Current Stress":

        if quantitative_pressure:
            return "CONFIRMS"

        return "CONTRADICTS"


    if story_type == "Easing":

        if quantitative_pressure:
            return "CONTRADICTS"

        return "CONFIRMS"


    return "NOT_DIRECTIONAL"


# =============================================================
# MARKET ATTENTION
# =============================================================


def _market_attention_label(
    meaningful_count: int,
    attention_weight: int,
) -> str:

    if (
        meaningful_count >= 2
        and attention_weight >= 20
    ):

        return "Elevated"


    if meaningful_count >= 1:

        return "Moderate"


    return "Low"


# =============================================================
# DIRECTIONAL CONFIRMATION
# =============================================================


def _directional_confirmation_label(
    confirming_weight: int,
    contradicting_weight: int,
) -> str:

    total = (
        confirming_weight
        + contradicting_weight
    )


    if total == 0:

        return "Limited Evidence"


    confirmation_share = (
        confirming_weight
        / total
    )


    if confirmation_share >= 0.75:

        return "Strongly Confirming"


    if confirmation_share >= 0.60:

        return "Moderately Confirming"


    if confirmation_share <= 0.25:

        return "Strongly Contradicting"


    if confirmation_share <= 0.40:

        return "Moderately Contradicting"


    return "Mixed"


# =============================================================
# SUMMARY
# =============================================================


def _build_summary(
    market_attention: str,
    directional_confirmation: str,
    structural_risk_count: int,
    policy_response_count: int,
    current_stress_count: int,
    easing_count: int,
) -> str:

    if (
        market_attention == "Elevated"
        and directional_confirmation
        == "Limited Evidence"
    ):

        return (
            "Market attention to liquidity-related issues "
            "is elevated, particularly around structural "
            "vulnerabilities and policy responses. "
            "Current reporting, however, does not provide "
            "enough directional evidence to confirm or "
            "contradict the quantitative liquidity signals."
        )


    if (
        market_attention == "Low"
        and directional_confirmation
        == "Limited Evidence"
    ):

        return (
            "Current news flow shows limited market attention "
            "to the liquidity mechanisms monitored by the "
            "system, and there is insufficient directional "
            "evidence to confirm or contradict the "
            "quantitative signals."
        )


    if directional_confirmation == "Limited Evidence":

        return (
            "Market reporting is discussing liquidity-related "
            "issues, but current coverage does not provide "
            "enough directional evidence to confirm or "
            "contradict the quantitative signals."
        )


    return (
        f"Market attention is {market_attention.lower()}, "
        f"with directional evidence classified as "
        f"{directional_confirmation.lower()}. "
        f"Current coverage includes "
        f"{current_stress_count} current-stress stories, "
        f"{easing_count} easing stories, "
        f"{structural_risk_count} structural-risk stories, "
        f"and {policy_response_count} policy-response stories."
    )


# =============================================================
# MAIN ENGINE
# =============================================================


def build_market_narrative(
    final_limit: int = 8,
) -> MarketNarrative:

    funding_signal = (
        evaluate_funding_signal()
    )

    system_signal = (
        evaluate_system_liquidity_signal()
    )


    ranked_articles = (
        rank_liquidity_news(
            raw_limit=40,
            final_limit=final_limit,
            minimum_score=10,
        )
    )


    stories: list[
        NarrativeStory
    ] = []


    current_stress_count = 0
    easing_count = 0
    structural_risk_count = 0
    policy_response_count = 0
    background_count = 0

    confirming_count = 0
    contradicting_count = 0

    confirming_weight = 0
    contradicting_weight = 0
    attention_weight = 0


    for ranked_article in ranked_articles:

        (
            story_type,
            pressure_score,
            easing_score,
        ) = _story_type(
            ranked_article
        )


        matched_signal = (
            _matched_signal(
                ranked_article.article.topic
            )
        )


        relationship = (
            _directional_relationship(
                story_type=story_type,

                matched_signal=
                    matched_signal,

                funding_severity=
                    funding_signal.severity,

                system_severity=
                    system_signal.severity,
            )
        )


        stories.append(
            NarrativeStory(
                ranked_article=
                    ranked_article,

                story_type=
                    story_type,

                matched_signal=
                    matched_signal,

                directional_relationship=
                    relationship,

                pressure_score=
                    pressure_score,

                easing_score=
                    easing_score,
            )
        )


        if story_type == "Current Stress":

            current_stress_count += 1

            attention_weight += (
                ranked_article.relevance_score
            )


        elif story_type == "Easing":

            easing_count += 1

            attention_weight += (
                ranked_article.relevance_score
            )


        elif story_type == "Structural Risk":

            structural_risk_count += 1

            attention_weight += (
                ranked_article.relevance_score
            )


        elif story_type == "Policy Response":

            policy_response_count += 1

            attention_weight += (
                ranked_article.relevance_score
            )


        else:

            background_count += 1


        if relationship == "CONFIRMS":

            confirming_count += 1

            confirming_weight += (
                ranked_article.relevance_score
            )


        elif relationship == "CONTRADICTS":

            contradicting_count += 1

            contradicting_weight += (
                ranked_article.relevance_score
            )


    meaningful_count = (
        current_stress_count
        + easing_count
        + structural_risk_count
        + policy_response_count
    )


    market_attention = (
        _market_attention_label(
            meaningful_count=
                meaningful_count,

            attention_weight=
                attention_weight,
        )
    )


    directional_confirmation = (
        _directional_confirmation_label(
            confirming_weight=
                confirming_weight,

            contradicting_weight=
                contradicting_weight,
        )
    )


    summary = _build_summary(
        market_attention=
            market_attention,

        directional_confirmation=
            directional_confirmation,

        structural_risk_count=
            structural_risk_count,

        policy_response_count=
            policy_response_count,

        current_stress_count=
            current_stress_count,

        easing_count=
            easing_count,
    )


    return MarketNarrative(
        market_attention=
            market_attention,

        directional_confirmation=
            directional_confirmation,

        funding_severity=
            funding_signal.severity,

        system_liquidity_severity=
            system_signal.severity,

        current_stress_count=
            current_stress_count,

        easing_count=
            easing_count,

        structural_risk_count=
            structural_risk_count,

        policy_response_count=
            policy_response_count,

        background_count=
            background_count,

        confirming_count=
            confirming_count,

        contradicting_count=
            contradicting_count,

        confirming_weight=
            confirming_weight,

        contradicting_weight=
            contradicting_weight,

        attention_weight=
            attention_weight,

        summary=
            summary,

        stories=
            stories,
    )


# =============================================================
# TERMINAL VIEW
# =============================================================


def print_market_narrative() -> None:

    narrative = (
        build_market_narrative()
    )


    print()
    print(
        "Liquidity Monitor — News Overlay"
    )
    print("=" * 72)

    print()

    print(
        f"Market Attention:         "
        f"{narrative.market_attention}"
    )

    print(
        f"Directional Confirmation: "
        f"{narrative.directional_confirmation}"
    )

    print()

    print(
        f"Funding Signal:           "
        f"{narrative.funding_severity}"
    )

    print(
        f"System Liquidity:         "
        f"{narrative.system_liquidity_severity}"
    )

    print()

    print(
        f"Current Stress:           "
        f"{narrative.current_stress_count}"
    )

    print(
        f"Easing:                   "
        f"{narrative.easing_count}"
    )

    print(
        f"Structural Risk:          "
        f"{narrative.structural_risk_count}"
    )

    print(
        f"Policy Response:          "
        f"{narrative.policy_response_count}"
    )

    print(
        f"Background:               "
        f"{narrative.background_count}"
    )

    print()

    print(
        narrative.summary
    )


    print()
    print("Relevant Stories")
    print("-" * 72)


    for number, story in enumerate(
        narrative.stories,
        start=1,
    ):

        article = (
            story.ranked_article.article
        )


        print()

        print(
            f"{number}. "
            f"{article.title}"
        )

        print(
            f"   Source:       "
            f"{article.source}"
        )

        print(
            f"   Topic:        "
            f"{article.topic}"
        )

        print(
            f"   Story Type:   "
            f"{story.story_type}"
        )

        print(
            f"   Signal Match: "
            f"{story.matched_signal or 'Broader Context'}"
        )

        print(
            f"   Direction:    "
            f"{story.directional_relationship}"
        )

        print(
            f"   Relevance:    "
            f"{story.ranked_article.relevance_score}"
        )

        print(
            f"   URL:          "
            f"{article.url}"
        )


if __name__ == "__main__":
    print_market_narrative()