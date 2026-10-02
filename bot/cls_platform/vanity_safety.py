"""F0 guard. Status matching is not built. The old loop assigned one role to every member."""

VANITY_UNAVAILABLE = (
    "Vanity Roles is temporarily unavailable while member-status matching is being rebuilt."
)


def vanity_automation_allowed() -> bool:
    return False
