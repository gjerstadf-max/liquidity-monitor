from dataclasses import dataclass


@dataclass(frozen=True)
class Assessment:
    category: str
    score: int
    condition: str
    confidence: str
    summary: str


from dataclasses import dataclass


@dataclass(frozen=True)
class LiquidityAssessment:
    overall_score: int
    overall_condition: str
    confidence: str

    funding: Assessment

    summary: str