from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from backend.assessments.funding import (
    assess_funding,
)

from backend.assessments.models import (
    Assessment,
)

from backend.assessments.repo_market import (
    assess_repo_market,
)

from backend.assessments.system_liquidity import (
    assess_system_liquidity,
)

from backend.assessments.treasury_intermediation import (
    assess_treasury_intermediation,
)

from backend.assessments.treasury_market_activity import (
    assess_treasury_market_activity,
)

from backend.commentary.factor_commentary import (
    funding_watch,
    funding_what_matters,
    repo_watch,
    repo_what_matters,
    system_liquidity_watch,
    system_liquidity_what_matters,
    treasury_intermediation_watch,
    treasury_intermediation_what_matters,
    treasury_market_activity_watch,
    treasury_market_activity_what_matters,
)
from backend.assessments.commercial_paper import (
    assess_commercial_paper,
)

from backend.commentary.factor_commentary import (
    commercial_paper_what_matters,
    commercial_paper_watch,
)

# =============================================================
# TYPES
# =============================================================


AssessmentBuilder = Callable[
    [],
    Assessment,
]

WhatMattersBuilder = Callable[
    [],
    str,
]

WatchBuilder = Callable[
    [str],
    str,
]


# =============================================================
# FACTOR DEFINITION
# =============================================================


@dataclass(frozen=True)
class FactorDefinition:
    """
    Central registration metadata for one
    Liquidity Monitor factor.

    The registry connects generic application plumbing
    to explicitly coded factor economics.
    """

    key: str

    display_name: str

    assessor: AssessmentBuilder

    what_matters_builder: WhatMattersBuilder

    watch_builder: WatchBuilder


# =============================================================
# FACTOR REGISTRY
# =============================================================


FACTOR_REGISTRY: tuple[
    FactorDefinition,
    ...
] = (

    FactorDefinition(
        key="funding",
        display_name="Funding Conditions",
        assessor=assess_funding,
        what_matters_builder=
            funding_what_matters,
        watch_builder=
            funding_watch,
    ),

    FactorDefinition(
        key="system_liquidity",
        display_name="System Liquidity",
        assessor=assess_system_liquidity,
        what_matters_builder=
            system_liquidity_what_matters,
        watch_builder=
            system_liquidity_watch,
    ),

    FactorDefinition(
        key="repo_market",
        display_name="Repo Market Pressure",
        assessor=assess_repo_market,
        what_matters_builder=
            repo_what_matters,
        watch_builder=
            repo_watch,
    ),

    FactorDefinition(
        key="treasury_intermediation",
        display_name="Treasury Intermediation",
        assessor=assess_treasury_intermediation,
        what_matters_builder=
            treasury_intermediation_what_matters,
        watch_builder=
            treasury_intermediation_watch,
    ),

    FactorDefinition(
        key="treasury_market_activity",
        display_name="Treasury Market Activity",
        assessor=assess_treasury_market_activity,
        what_matters_builder=
            treasury_market_activity_what_matters,
        watch_builder=
            treasury_market_activity_watch,
    ),

    FactorDefinition(
        key="commercial_paper",
        display_name="Commercial Paper",
        assessor=assess_commercial_paper,
        what_matters_builder=
            commercial_paper_what_matters,
        watch_builder=
            commercial_paper_watch,
    ),

)


FACTOR_BY_KEY = {

    definition.key:
        definition

    for definition
    in FACTOR_REGISTRY

}


def factor_definition(
    key: str,
) -> FactorDefinition:
    """
    Return one registered factor definition.
    """

    try:

        return FACTOR_BY_KEY[
            key
        ]

    except KeyError as exc:

        raise KeyError(
            f"Unknown liquidity factor: {key}"
        ) from exc