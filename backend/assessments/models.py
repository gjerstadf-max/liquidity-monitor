from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Assessment:
    category: str
    verdict: str
    confidence: str
    summary: str


@dataclass(frozen=True)
class FactorAssessment:
    """
    One registered factor and its completed assessment.
    """

    key: str
    assessment: Assessment


@dataclass(frozen=True)
class LiquidityAssessment:
    overall_verdict: str
    confidence: str

    factors: tuple[
        FactorAssessment,
        ...
    ]

    summary: str

    def factor(
        self,
        key: str,
    ) -> Assessment:
        """
        Return one factor assessment by registry key.
        """

        for item in self.factors:

            if item.key == key:
                return item.assessment

        raise KeyError(
            f"Unknown liquidity factor: {key}"
        )

    # ---------------------------------------------------------
    # BACKWARD-COMPATIBLE ACCESSORS
    # ---------------------------------------------------------

    @property
    def funding(
        self,
    ) -> Assessment:

        return self.factor(
            "funding"
        )

    @property
    def system_liquidity(
        self,
    ) -> Assessment:

        return self.factor(
            "system_liquidity"
        )

    @property
    def repo_market(
        self,
    ) -> Assessment:

        return self.factor(
            "repo_market"
        )

    @property
    def treasury_intermediation(
        self,
    ) -> Assessment:

        return self.factor(
            "treasury_intermediation"
        )