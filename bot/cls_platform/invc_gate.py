"""Voice-role runtime honors the dashboard Enabled switch."""


def invc_role_should_apply(role_id, enabled) -> bool:
    if not role_id:
        return False
    try:
        flag = int(enabled or 0)
    except (TypeError, ValueError):
        return False
    return flag != 0
