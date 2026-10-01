"""Dashboard welcome channels are stored as snowflake strings."""

from cogs.events.greet2 import coerce_channel_id


def test_welcome_channel_accepts_snowflake_text():
    assert coerce_channel_id("100000000000000401") == 100000000000000401
    assert coerce_channel_id(100000000000000401) == 100000000000000401
    assert coerce_channel_id(None) is None
    assert coerce_channel_id("channel") is None
