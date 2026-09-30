"""Typed Discord snowflake validation for V2 APIs."""

from __future__ import annotations

from typing import Annotated

from pydantic import AfterValidator, Field


def _validate_snowflake(value: int) -> int:
    if value < 1 or value > 9223372036854775807:
        raise ValueError("Invalid Discord snowflake")
    return value


DiscordSnowflake = Annotated[int, AfterValidator(_validate_snowflake)]
GuildId = Annotated[DiscordSnowflake, Field(description="Discord guild ID")]
RoleId = Annotated[DiscordSnowflake, Field(description="Discord role ID")]
ChannelId = Annotated[DiscordSnowflake, Field(description="Discord channel ID")]
UserId = Annotated[DiscordSnowflake, Field(description="Discord user ID")]
MessageId = Annotated[DiscordSnowflake, Field(description="Discord message ID")]
