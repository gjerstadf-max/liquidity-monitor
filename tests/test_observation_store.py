from datetime import date
from decimal import Decimal
from types import SimpleNamespace

import backend.services.observation_store as observation_store


class _FakeScalars:
    def all(self):
        return []


class _FakeSession:
    def __init__(self):
        self.added = []
        self.committed = False

    def __enter__(self):
        return self

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback,
    ):
        return False

    def scalar(self, statement):
        return SimpleNamespace(
            id=123
        )

    def scalars(self, statement):
        return _FakeScalars()

    def add(self, value):
        self.added.append(
            value
        )

    def commit(self):
        self.committed = True


def test_store_values_returns_result_for_nonempty_input(
    monkeypatch,
):
    session = _FakeSession()

    monkeypatch.setattr(
        observation_store,
        "get_session",
        lambda: session,
    )

    result = (
        observation_store.store_values(
            indicator_symbol=
                "test_series",
            values=[
                (
                    date(
                        2026,
                        10,
                        1,
                    ),
                    Decimal(
                        "123.45"
                    ),
                ),
            ],
        )
    )

    assert isinstance(
        result,
        observation_store.StoreResult,
    )

    assert result.symbol == "test_series"
    assert result.received == 1
    assert result.inserted == 1
    assert result.skipped == 0
    assert (
        result.latest_date
        == date(
            2026,
            10,
            1,
        )
    )
    assert (
        result.latest_value
        == Decimal(
            "123.45"
        )
    )

    assert len(
        session.added
    ) == 1

    assert session.committed is True
