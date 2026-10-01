"""Join to Create arming rules.

Disabling the module must keep the stored channel IDs. The bot only creates a
temporary channel when the module is enabled and both required channels exist.
"""


def j2c_should_arm(enabled, join_channel_id, control_channel_id) -> bool:
    if enabled in (0, False, None, "0"):
        return False
    if not join_channel_id or not control_channel_id:
        return False
    return True
