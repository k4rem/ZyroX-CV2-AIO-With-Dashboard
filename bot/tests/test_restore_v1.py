"""Restore plans report absent members and refuse execution unless explicitly allowed."""

from cls_platform.restore import RestoreError, build_plan, confirmation_phrase, execute_plan, execution_allowed

DOC = {
    "roles": [
        {"id": "100000000000000010", "name": "Mod", "position": 2, "permissions": "8", "managed": False},
        {"id": "100000000000000011", "name": "Muted", "position": 1, "permissions": "0", "managed": False},
    ],
    "channels": [
        {"id": "100000000000000020", "name": "staff", "type": "category", "parent_id": None, "position": 0, "overwrites": []},
        {
            "id": "100000000000000021",
            "name": "ops",
            "type": "text",
            "parent_id": "100000000000000020",
            "position": 1,
            "overwrites": [{"id": "100000000000000010", "type": "role", "allow": "1024", "deny": "0"}],
        },
    ],
    "bans": ["100000000000000030"],
    "members": [
        {"user_id": "100000000000000040", "role_ids": ["100000000000000010"]},
        {"user_id": "100000000000000041", "role_ids": ["100000000000000011"]},
    ],
    "settings": {"name": "Recovered"},
}


class FakeGuild:
    def __init__(self):
        self.roles = []
        self.channels = []
        self.bans = []
        self.members = {}
        self.settings = None
        self._n = 500

    async def create_role(self, *, name, permissions):
        self._n += 1
        row = type("Role", (), {"id": self._n, "name": name, "permissions": permissions})()
        self.roles.append(row)
        return row

    async def create_channel(self, *, name, parent_id, kind=None):
        self._n += 1
        row = type("Channel", (), {"id": self._n, "name": name, "parent_id": parent_id, "overwrites": []})()
        self.channels.append(row)
        return row

    async def set_overwrite(self, channel_id, target_id, allow, deny):
        channel = next(item for item in self.channels if item.id == channel_id)
        channel.overwrites.append((target_id, allow, deny))

    async def ban(self, user_id):
        self.bans.append(user_id)

    async def set_member_roles(self, user_id, role_ids):
        self.members[user_id] = role_ids

    async def edit_settings(self, settings):
        self.settings = settings


def test_plan_marks_absent_members_and_orders_roles():
    plan = build_plan(DOC, {"100000000000000040"})
    assert [role["name"] for role in plan["roles"]] == ["Muted", "Mod"]
    assert plan["categories"][0]["name"] == "staff"
    absent = next(item for item in plan["members"] if item["user_id"].endswith("041"))
    assert absent["status"] == "REQUIRES MEMBER REAUTHORIZATION"
    present = next(item for item in plan["members"] if item["user_id"].endswith("040"))
    assert present["status"] == "present"
    assert execution_allowed(100000000000000100) is False


async def test_execute_requires_confirmation_and_flag():
    plan = build_plan(DOC, {"100000000000000040"})
    plan["confirmation"] = confirmation_phrase("abc")
    guild = FakeGuild()
    try:
        await execute_plan(plan, guild, confirmation="no", allow_execution=True)
        assert False
    except RestoreError as exc:
        assert str(exc) == "confirmation_required"
    refused = await execute_plan(plan, guild, confirmation=plan["confirmation"], allow_execution=False)
    assert refused["executed"] is False
    assert guild.roles == []
    done = await execute_plan(plan, guild, confirmation=plan["confirmation"], allow_execution=True)
    assert done["executed"] is True
    assert [role.name for role in guild.roles] == ["Muted", "Mod"]
    assert guild.channels[0].name == "staff"
    assert guild.channels[1].parent_id == str(guild.channels[0].id)
    assert guild.bans == ["100000000000000030"]
    assert "100000000000000041" not in guild.members
    assert guild.settings["name"] == "Recovered"
