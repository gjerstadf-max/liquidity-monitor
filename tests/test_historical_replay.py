from datetime import date

from backend.assessments.engine import (
    build_liquidity_assessment,
)
from backend.metrics.funding import (
    funding_spread_statistics,
)
from backend.metrics.system_liquidity import (
    system_liquidity_history_metrics,
    system_liquidity_metrics,
)

from backend.commentary.liquidity_interpreter import (
    _persistent_non_normal_factors,
)

from backend.commentary.anomaly_context import (
    build_anomaly_diagnostics,
)

from backend.commentary.policy_context import (
    build_policy_context,
)

from backend.commentary.replay_memory import (
    load_recent_replay_history,
    record_replay_day,
)

from backend.commentary.replay_hypotheses import (
    append_hypothesis_evaluation,
    create_hypothesis,
    load_active_hypotheses,
)

import pytest

from backend.commentary.replay_hypotheses import (
    apply_hypothesis_outputs,
    create_hypothesis,
    load_active_hypotheses,
)


REPLAY_DATE = date(2026, 9, 15)


def test_funding_respects_historical_date():
    stats = funding_spread_statistics(
        as_of_date=REPLAY_DATE
    )

    assert stats.observation_date <= REPLAY_DATE

    assert stats.observation_date == date(
        2026,
        9,
        14,
    )


def test_system_liquidity_respects_historical_date():
    current = system_liquidity_metrics(
        as_of_date=REPLAY_DATE
    )

    history = system_liquidity_history_metrics(
        as_of_date=REPLAY_DATE
    )

    assert current.observation_date <= REPLAY_DATE

    assert current.observation_date == date(
        2026,
        9,
        9,
    )

    assert round(
        float(
            current.net_liquidity_proxy_billions
        ),
        1,
    ) == 2148.0

    assert round(
        float(
            history.four_week_change_billions
        ),
        1,
    ) == 162.7

    assert round(
        history.zscore_52_week,
        2,
    ) == 0.19

def test_system_liquidity_respects_publication_lag():
    before_release = (
        system_liquidity_history_metrics(
            as_of_date=date(
                2026,
                9,
                17,
            )
        )
    )

    after_release = (
        system_liquidity_history_metrics(
            as_of_date=date(
                2026,
                9,
                18,
            )
        )
    )

    assert (
        before_release.observation_date
        == date(2026, 9, 9)
    )

    assert (
        after_release.observation_date
        == date(2026, 9, 16)
    )


def test_full_assessment_replays_historical_state(
    monkeypatch,
):
    from datetime import date, timedelta
    from decimal import Decimal

    import backend.metrics.bank_funding as bank_funding
    import backend.metrics.global_dollar_funding as global_dollar

    # ---------------------------------------------------------
    # BANK FUNDING — deterministic historical H.8 vintage
    # ---------------------------------------------------------

    deposit_start = date(
        2026,
        6,
        3,
    )

    def fake_bank_vintage_series(
        symbol,
        vintage_date,
    ):
        if symbol == "bank_deposits_small":
            base = Decimal("5600")
            increment = Decimal("1")

        elif symbol == "bank_deposits_large":
            base = Decimal("12300")
            increment = Decimal("2")

        elif symbol == "bank_large_time_deposits_small":
            base = Decimal("730")
            increment = Decimal("0.5")

        else:
            raise AssertionError(
                f"Unexpected bank vintage series: {symbol}"
            )

        return [
            (
                deposit_start
                + timedelta(
                    days=7 * index
                ),
                base
                + increment
                * Decimal(index),
            )
            for index in range(15)
        ]

    monkeypatch.setattr(
        bank_funding,
        "_load_vintage_series",
        fake_bank_vintage_series,
    )

    # ---------------------------------------------------------
    # GLOBAL DOLLAR FUNDING — deterministic H.4.1 vintage
    # ---------------------------------------------------------

    swap_observations = [
        (
            date(2026, 8, 19),
            Decimal("0.120"),
        ),
        (
            date(2026, 8, 26),
            Decimal("0.110"),
        ),
        (
            date(2026, 9, 2),
            Decimal("0.105"),
        ),
        (
            date(2026, 9, 9),
            Decimal("0.101"),
        ),
    ]

    fima_observations = [
        (
            date(2026, 8, 19),
            Decimal("0.001"),
        ),
        (
            date(2026, 8, 26),
            Decimal("0.001"),
        ),
        (
            date(2026, 9, 2),
            Decimal("0.000"),
        ),
        (
            date(2026, 9, 9),
            Decimal("0.001"),
        ),
    ]

    def fake_global_vintage_series(
        symbol,
        vintage_date,
    ):
        if (
            symbol
            == "central_bank_liquidity_swaps"
        ):
            return swap_observations

        if symbol == "fima_repo":
            return fima_observations

        raise AssertionError(
            f"Unexpected global-dollar series: {symbol}"
        )

    monkeypatch.setattr(
        global_dollar,
        "_load_vintage_series",
        fake_global_vintage_series,
    )

    # ---------------------------------------------------------
    # FULL ASSESSMENT
    # ---------------------------------------------------------

    assessment = build_liquidity_assessment(
        as_of_date=REPLAY_DATE
    )

    assert len(
        assessment.factors
    ) == 8

    factors = {
        factor.key: factor.assessment
        for factor in assessment.factors
    }

    assert (
        factors["funding"].verdict
        == "Normal"
    )

    assert (
        factors["system_liquidity"].verdict
        == "Normal"
    )

    assert (
        factors[
            "treasury_market_activity"
        ].verdict
        == "Normal"
    )

    assert (
        "+42 bp relative to IORB"
        in factors[
            "treasury_market_activity"
        ].summary
    )


def test_historical_replay_detects_treasury_iorb_anomaly():
    diagnostics = build_anomaly_diagnostics(
        as_of_date=date(2026, 9, 15)
    )

    assert len(diagnostics) == 1

    diagnostic = diagnostics[0]

    assert (
        diagnostic["type"]
        == "treasury_iorb_relative_pricing"
    )
    assert diagnostic["spread_bp"] == 42.0
    assert diagnostic["zscore"] == 4.2
    assert diagnostic["percentile"] == 100.0
    assert diagnostic["treasury_change_5d_bp"] ==18
    assert diagnostic["iorb_change_5d_bp"] == 0.0
    assert diagnostic["consecutive_above_95th"] ==3
    assert diagnostic["consecutive_above_99th"] ==2
    assert diagnostic["primary_mover"] == "treasury_3m"


def test_historical_replay_skips_normal_treasury_iorb_reading():
    diagnostics = build_anomaly_diagnostics(
        as_of_date=date(2026, 9, 21)
    )

    assert diagnostics == []

def test_sep15_replay_knows_fomc_schedule_not_decision():
    context = build_policy_context(
        date(2026, 9, 15)
    )

    assert context is not None
    assert context["scheduled_fomc_nearby"] is True
    assert context["meeting_dates"] == [
        "2026-09-15",
        "2026-09-16",
    ]
    assert context["meeting_in_progress"] is True
    assert (
        context["decision_known_as_of_replay"]
        is False
    )
    assert context["days_to_fomc_decision"] == 1
    assert context["days_since_fomc_decision"] is None


def test_sep16_date_only_replay_still_hides_decision():
    context = build_policy_context(
        date(2026, 9, 16)
    )

    assert context is not None
    assert context["meeting_in_progress"] is True
    assert (
        context["decision_known_as_of_replay"]
        is False
    )
    assert context["days_to_fomc_decision"] == 0


def test_sep17_replay_can_know_decision_occurred():
    context = build_policy_context(
        date(2026, 9, 17)
    )

    assert context is not None
    assert context["meeting_in_progress"] is False
    assert (
        context["decision_known_as_of_replay"]
        is True
    )
    assert context["days_since_fomc_decision"] == 1

def test_replay_memory_returns_only_prior_dates(
    tmp_path,
):
    memory_path = (
        tmp_path
        / "replay_memory.json"
    )

    for replay_date_value in [
        "2026-09-14",
        "2026-09-15",
        "2026-09-17",
    ]:
        record_replay_day(
            packet={
                "replay_date":
                    replay_date_value,

                "framework": {
                    "overall_verdict":
                        "Normal",

                    "overall_confidence":
                        "Moderate",

                    "non_normal_factors":
                        [],
                },

                "factors": [],

                "anomaly_diagnostics":
                    [],
            },
            path=memory_path,
        )

    history = (
        load_recent_replay_history(
            replay_date=date(
                2026,
                9,
                16,
            ),
            path=memory_path,
        )
    )

    assert [
        item["replay_date"]
        for item in history
    ] == [
        "2026-09-14",
        "2026-09-15",
    ]


def test_replay_memory_replaces_same_date(
    tmp_path,
):
    memory_path = (
        tmp_path
        / "replay_memory.json"
    )

    packet = {
        "replay_date":
            "2026-09-15",

        "framework": {
            "overall_verdict":
                "Normal",

            "overall_confidence":
                "Moderate",

            "non_normal_factors":
                [],
        },

        "factors": [
            {
                "key":
                    "treasury_market_activity",

                "verdict":
                    "Normal",
            }
        ],

        "anomaly_diagnostics":
            [],
    }

    record_replay_day(
        packet=packet,
        path=memory_path,
    )

    packet["framework"][
        "overall_verdict"
    ] = "Watch"

    record_replay_day(
        packet=packet,
        path=memory_path,
    )

    history = (
        load_recent_replay_history(
            replay_date=date(
                2026,
                9,
                16,
            ),
            path=memory_path,
        )
    )

    assert len(history) == 1

    assert (
        history[0]["overall_verdict"]
        == "Watch"
    )
def test_hypothesis_creation_is_persistent(
    tmp_path,
):
    ledger_path = (
        tmp_path
        / "replay_hypotheses.json"
    )

    record = create_hypothesis(
        created_date=date(
            2026,
            9,
            14,
        ),
        hypothesis=(
            "Treasury-IORB divergence may reflect "
            "short-rate repricing rather than "
            "liquidity stress."
        ),
        confidence="Moderate",
        supporting_evidence=[
            "Treasury 3M is the primary mover.",
            "Repo conditions remain orderly.",
        ],
        expected_if_true=[
            "The spread normalizes around or after "
            "the policy window.",
        ],
        would_weaken=[
            "Repo conditions deteriorate.",
        ],
        review_by=date(
            2026,
            9,
            18,
        ),
        path=ledger_path,
    )

    assert (
        record["id"]
        == "H-20260914-01"
    )

    assert (
        record["created_date"]
        == "2026-09-14"
    )

    assert record["evaluations"] == []


def test_hypothesis_evaluation_preserves_original(
    tmp_path,
):
    ledger_path = (
        tmp_path
        / "replay_hypotheses.json"
    )

    record = create_hypothesis(
        created_date=date(
            2026,
            9,
            14,
        ),
        hypothesis="Original hypothesis.",
        confidence="Moderate",
        supporting_evidence=[
            "Initial evidence.",
        ],
        expected_if_true=[
            "Expected outcome.",
        ],
        would_weaken=[
            "Contrary outcome.",
        ],
        path=ledger_path,
    )

    append_hypothesis_evaluation(
        hypothesis_id=record["id"],
        review_date=date(
            2026,
            9,
            15,
        ),
        status="strengthened",
        evidence=[
            "Expected evidence persisted.",
        ],
        rationale=(
            "The new observation is consistent "
            "with the original hypothesis."
        ),
        confidence="Moderate",
        path=ledger_path,
    )

    history = load_active_hypotheses(
        replay_date=date(
            2026,
            9,
            16,
        ),
        path=ledger_path,
    )

    assert len(history) == 1

    hypothesis = history[0]

    assert (
        hypothesis["hypothesis"]
        == "Original hypothesis."
    )

    assert (
        hypothesis["current_status"]
        == "strengthened"
    )

    assert (
        len(
            hypothesis["evaluations"]
        )
        == 1
    )


def test_hypothesis_memory_blocks_future_information(
    tmp_path,
):
    ledger_path = (
        tmp_path
        / "replay_hypotheses.json"
    )

    record = create_hypothesis(
        created_date=date(
            2026,
            9,
            14,
        ),
        hypothesis="Test hypothesis.",
        confidence="Moderate",
        supporting_evidence=[],
        expected_if_true=[],
        would_weaken=[],
        path=ledger_path,
    )

    append_hypothesis_evaluation(
        hypothesis_id=record["id"],
        review_date=date(
            2026,
            9,
            17,
        ),
        status="supported",
        evidence=[
            "Future evidence.",
        ],
        rationale="Resolved later.",
        path=ledger_path,
    )

    history_sep_16 = (
        load_active_hypotheses(
            replay_date=date(
                2026,
                9,
                16,
            ),
            path=ledger_path,
        )
    )

    assert len(history_sep_16) == 1
    assert (
        history_sep_16[0][
            "evaluations"
        ]
        == []
    )
    assert (
        history_sep_16[0][
            "current_status"
        ]
        == "active"
    )

    history_sep_18 = (
        load_active_hypotheses(
            replay_date=date(
                2026,
                9,
                18,
            ),
            path=ledger_path,
        )
    )

    assert history_sep_18 == []

def test_hypothesis_creation_is_idempotent(
    tmp_path,
):
    ledger_path = (
        tmp_path
        / "replay_hypotheses.json"
    )

    kwargs = {
        "created_date":
            date(2026, 9, 14),

        "hypothesis":
            "Test hypothesis.",

        "confidence":
            "Moderate",

        "supporting_evidence":
            ["Evidence."],

        "expected_if_true":
            ["Expected."],

        "would_weaken":
            ["Weakener."],

        "path":
            ledger_path,
    }

    first = create_hypothesis(
        **kwargs
    )

    second = create_hypothesis(
        **kwargs
    )

    assert first["id"] == second["id"]

    history = load_active_hypotheses(
        replay_date=date(
            2026,
            9,
            15,
        ),
        path=ledger_path,
    )

    assert len(history) == 1
def test_model_cannot_evaluate_unseen_hypothesis(
    tmp_path,
):
    ledger_path = (
        tmp_path
        / "replay_hypotheses.json"
    )

    with pytest.raises(
        ValueError,
        match="was not visible",
    ):
        apply_hypothesis_outputs(
            replay_date=date(
                2026,
                9,
                15,
            ),
            proposed_hypotheses=[],
            hypothesis_evaluations=[
                {
                    "hypothesis_id":
                        "H-20260999-99",

                    "status":
                        "strengthened",

                    "evidence":
                        ["Invented evidence."],

                    "rationale":
                        "Invalid evaluation.",

                    "confidence":
                        "Moderate",
                }
            ],
            visible_hypotheses=[],
            path=ledger_path,
        )

def test_bank_funding_primary_credit_respects_h41_publication_lag(
    monkeypatch,
):
    from datetime import date, timedelta
    from decimal import Decimal

    import backend.metrics.bank_funding as bank_funding

    primary = [
        (date(2026, 9, 9), Decimal("1.0")),
        (date(2026, 9, 16), Decimal("2.0")),
        (date(2026, 9, 23), Decimal("3.0")),
    ]

    deposit_start = date(2026, 6, 3)

    deposits = [
        (
            deposit_start + timedelta(days=7 * index),
            Decimal("5000") + Decimal(index),
        )
        for index in range(15)
    ]

    monkeypatch.setattr(
        bank_funding,
        "_load_series",
        lambda symbol: primary,
    )

    monkeypatch.setattr(
        bank_funding,
        "_load_vintage_series",
        lambda symbol, vintage_date: deposits,
    )

    before_release = (
        bank_funding.bank_funding_statistics(
            as_of_date=date(2026, 9, 24)
        )
    )

    after_release = (
        bank_funding.bank_funding_statistics(
            as_of_date=date(2026, 9, 25)
        )
    )

    assert (
        before_release.primary_credit_date
        == date(2026, 9, 16)
    )

    assert (
        after_release.primary_credit_date
        == date(2026, 9, 23)
    )


def test_bank_funding_h8_uses_prior_day_vintage(
    monkeypatch,
):
    from datetime import date, timedelta
    from decimal import Decimal

    import backend.metrics.bank_funding as bank_funding

    primary = [
        (date(2026, 9, 9), Decimal("1.0")),
        (date(2026, 9, 16), Decimal("2.0")),
        (date(2026, 9, 23), Decimal("3.0")),
    ]

    deposit_start = date(2026, 6, 3)

    deposits = [
        (
            deposit_start + timedelta(days=7 * index),
            Decimal("5000") + Decimal(index),
        )
        for index in range(15)
    ]
    requested_vintages = []

    def fake_load_vintage_series(
        symbol,
        vintage_date,
    ):
        requested_vintages.append(
            (
                symbol,
                vintage_date,
            )
        )
        return deposits

    monkeypatch.setattr(
        bank_funding,
        "_load_series",
        lambda symbol: primary,
    )

    monkeypatch.setattr(
        bank_funding,
        "_load_vintage_series",
        fake_load_vintage_series,
    )

    bank_funding.bank_funding_statistics(
        as_of_date=date(2026, 9, 25)
    )

    assert len(requested_vintages) == 3

    assert all(
        vintage_date == date(2026, 9, 24)
        for _, vintage_date
        in requested_vintages
    )

def test_global_dollar_funding_uses_prior_day_vintage(
    monkeypatch,
):
    from datetime import date
    from decimal import Decimal

    import backend.metrics.global_dollar_funding as global_dollar

    requested_vintages = []

    observations = [
        (
            date(2026, 9, 9),
            Decimal("0.101"),
        ),
        (
            date(2026, 9, 16),
            Decimal("0.094"),
        ),
    ]

    def fake_load_vintage_series(
        symbol,
        vintage_date,
    ):
        requested_vintages.append(
            (
                symbol,
                vintage_date,
            )
        )
        return observations

    monkeypatch.setattr(
        global_dollar,
        "_load_vintage_series",
        fake_load_vintage_series,
    )

    stats = (
        global_dollar
        .global_dollar_funding_statistics(
            as_of_date=date(2026, 9, 18)
        )
    )

    assert len(requested_vintages) == 2

    assert {
        symbol
        for symbol, _
        in requested_vintages
    } == {
        "central_bank_liquidity_swaps",
        "fima_repo",
    }

    assert all(
        vintage_date == date(2026, 9, 17)
        for _, vintage_date
        in requested_vintages
    )

    assert (
        stats.swap_date
        == date(2026, 9, 16)
    )

    assert (
        stats.fima_date
        == date(2026, 9, 16)
    )
def test_treasury_rate_replay_uses_prior_day_vintage(
    monkeypatch,
):
    from datetime import date

    import backend.metrics.treasury_market_activity as treasury

    class FakeResult:
        def all(self):
            return [
                (
                    date(2026, 9, 14),
                    4.11,
                )
            ]

    class FakeSession:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def scalar(self, statement):
            class FakeIndicator:
                id = 1

            return FakeIndicator()

        def execute(self, statement):
            return FakeResult()

    monkeypatch.setattr(
        treasury,
        "get_session",
        lambda: FakeSession(),
    )

    # The important behavior is exercised by the
    # historical path without touching production data.
    rows = treasury._load_indicator_history(
        "treasury_3m",
        as_of_date=date(2026, 9, 16),
    )

    assert rows == [
        (
            date(2026, 9, 14),
            4.11,
        )
    ]


def test_treasury_market_snapshot_historical_sequence(
    monkeypatch,
):
    from datetime import date

    import backend.metrics.treasury_market_activity as treasury

    histories = {
        "treasury_3m": [
            (date(2026, 9, 10), 4.00),
            (date(2026, 9, 11), 4.07),
            (date(2026, 9, 14), 4.11),
        ],
        "iorb": [
            (date(2026, 9, 10), 3.65),
            (date(2026, 9, 11), 3.65),
            (date(2026, 9, 14), 3.65),
        ],
    }

    def fake_history(
        symbol,
        as_of_date=None,
    ):
        return [
            row
            for row in histories[symbol]
            if (
                as_of_date is None
                or row[0] <= as_of_date
            )
        ]

    monkeypatch.setattr(
        treasury,
        "_load_indicator_history",
        fake_history,
    )

    stats = treasury.latest_treasury_market_snapshot(
        as_of_date=date(2026, 9, 16)
    )

    assert stats.observation_date == date(
        2026,
        9,
        14,
    )

    assert round(
        stats.spread_bp,
        1,
    ) == 46.0
def test_commercial_paper_uses_prior_day_vintage(
    monkeypatch,
):
    from datetime import date
    from decimal import Decimal

    import backend.metrics.commercial_paper as cp

    requested_vintages = []

    def fake_vintage_series(
        symbol,
        vintage_date,
    ):
        requested_vintages.append(
            (
                symbol,
                vintage_date,
            )
        )

        if symbol == "cp_aa_nonfinancial_30d":
            return {
                date(2026, 9, 11):
                    Decimal("3.77"),
            }

        if symbol == "cp_a2p2_nonfinancial_30d":
            return {
                date(2026, 9, 11):
                    Decimal("4.00"),
            }

        raise AssertionError(
            f"Unexpected series: {symbol}"
        )

    monkeypatch.setattr(
        cp,
        "_load_vintage_series",
        fake_vintage_series,
    )

    snapshot = (
        cp.latest_commercial_paper_snapshot(
            as_of_date=date(2026, 9, 15)
        )
    )

    assert requested_vintages == [
        (
            "cp_aa_nonfinancial_30d",
            date(2026, 9, 14),
        ),
        (
            "cp_a2p2_nonfinancial_30d",
            date(2026, 9, 14),
        ),
    ]

    assert (
        snapshot.observation_date
        == date(2026, 9, 11)
    )

    assert (
        snapshot.credit_premium_bp
        == Decimal("23.00")
    )
def test_carried_forward_factor_is_not_repeated_confirmation():
    packet = {
        "framework": {
            "non_normal_factors": [
                "treasury_intermediation",
            ],
        },
        "factors": [
            {
                "key": "treasury_intermediation",
                "verdict": "Watch",
                "observation_date": "2026-09-23",
            },
        ],
        "recent_history": [
            {
                "replay_date": "2026-09-28",
                "non_normal_factors": [
                    "treasury_intermediation",
                ],
                "factor_observation_dates": {
                    "treasury_intermediation":
                        "2026-09-23",
                },
            },
            {
                "replay_date": "2026-09-29",
                "non_normal_factors": [
                    "treasury_intermediation",
                ],
                "factor_observation_dates": {
                    "treasury_intermediation":
                        "2026-09-23",
                },
            },
        ],
    }

    assert (
        _persistent_non_normal_factors(packet)
        == []
    )


def test_distinct_factor_observations_can_establish_persistence():
    packet = {
        "framework": {
            "non_normal_factors": [
                "treasury_intermediation",
            ],
        },
        "factors": [
            {
                "key": "treasury_intermediation",
                "verdict": "Watch",
                "observation_date": "2026-09-30",
            },
        ],
        "recent_history": [
            {
                "replay_date": "2026-09-16",
                "non_normal_factors": [
                    "treasury_intermediation",
                ],
                "factor_observation_dates": {
                    "treasury_intermediation":
                        "2026-09-16",
                },
            },
            {
                "replay_date": "2026-09-23",
                "non_normal_factors": [
                    "treasury_intermediation",
                ],
                "factor_observation_dates": {
                    "treasury_intermediation":
                        "2026-09-23",
                },
            },
        ],
    }

    assert (
        _persistent_non_normal_factors(packet)
        == ["treasury_intermediation"]
    )

def test_treasury_market_activity_replay_has_observation_date():
    from datetime import date

    from backend.commentary.interpretation_context import (
        build_interpretation_context,
    )

    replay_date = date(
        2026,
        10,
        1,
    )

    packet = build_interpretation_context(
        replay_date=replay_date
    )

    factor = next(
        item
        for item in packet["factors"]
        if (
            item["key"]
            == "treasury_market_activity"
        )
    )

    assert factor["observation_date"] is not None

    observation_date = date.fromisoformat(
        factor["observation_date"]
    )

    assert observation_date <= replay_date


