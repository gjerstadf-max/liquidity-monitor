from backend.signals.treasury_market_activity import (
    _ordinal_percentile,
)


def test_ordinal_percentile_suffixes():
    assert _ordinal_percentile(1) == "1st"
    assert _ordinal_percentile(2) == "2nd"
    assert _ordinal_percentile(3) == "3rd"
    assert _ordinal_percentile(4) == "4th"

    assert _ordinal_percentile(11) == "11th"
    assert _ordinal_percentile(12) == "12th"
    assert _ordinal_percentile(13) == "13th"

    assert _ordinal_percentile(21) == "21st"
    assert _ordinal_percentile(42) == "42nd"
    assert _ordinal_percentile(63) == "63rd"
    assert _ordinal_percentile(72) == "72nd"
