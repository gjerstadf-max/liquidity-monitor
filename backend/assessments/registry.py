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


# =============================================================
# FACTOR DEFINITION
# =============================================================


@dataclass(frozen=True)
class FactorDefinition:
    """
    Registration metadata for one Liquidity Monitor factor.

    Economic logic remains inside the factor's own
    assessment/signal modules.
    """

    key: str
    display_name: str
    assessor: Callable[
        [],
        Assessment,
    ]


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
    ),
    FactorDefinition(
        key="system_liquidity",
        display_name="System Liquidity",
        assessor=assess_system_liquidity,
    ),
    FactorDefinition(
        key="repo_market",
        display_name="Repo Market Pressure",
        assessor=assess_repo_market,
    ),
    FactorDefinition(
        key="treasury_intermediation",
        display_name="Treasury Intermediation",
        assessor=assess_treasury_intermediation,
    ),
)