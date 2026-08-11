from dataclasses import dataclass


@dataclass(frozen=True)
class Signal:
    category: str
    title: str
    severity: str
    message: str