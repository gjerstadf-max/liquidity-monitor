from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class Signal:
    category: str
    title: str
    severity: str
    message: str
    observation_date: date | None = None


