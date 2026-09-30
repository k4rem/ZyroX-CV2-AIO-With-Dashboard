"""Typed Discord snowflake validation for V2 APIs."""

from __future__ import annotations

from typing import Annotated, Iterable, Optional, Union

from pydantic import AfterValidator, Field


def _validate_snowflake(value: int) -> int:
    if value < 1 or value > 9223372036854775807:
        raise ValueError("Invalid Discord snowflake")
    return value


def _validate_snowflake_str(value: Union[str, int]) -> str:
    if isinstance(value, int):
        # Accept int only when converting from DB/Python; always serialize as str in JSON.
        if value < 1 or value > 9223372036854775807:
            raise ValueError("Invalid Discord snowflake")
        return str(value)
    s = str(value).strip()
    if not s.isdigit() or len(s) < 17 or len(s) > 20:
        raise ValueError("Invalid Discord snowflake string")
    if int(s) < 1:
        raise ValueError("Invalid Discord snowflake string")
    return s


def snowflake_str_to_int(value: str) -> int:
    return int(_validate_snowflake_str(value))


def snowflake_to_str(value: Optional[int]) -> Optional[str]:
    if value is None:
        return None
    return _validate_snowflake_str(value)


def snowflake_list_to_str(values: Iterable[int]) -> list[str]:
    return [_validate_snowflake_str(v) for v in values]


DiscordSnowflake = Annotated[int, AfterValidator(_validate_snowflake)]
GuildId = Annotated[DiscordSnowflake, Field(description="Discord guild ID")]
RoleId = Annotated[DiscordSnowflake, Field(description="Discord role ID")]
ChannelId = Annotated[DiscordSnowflake, Field(description="Discord channel ID")]
UserId = Annotated[DiscordSnowflake, Field(description="Discord user ID")]
MessageId = Annotated[DiscordSnowflake, Field(description="Discord message ID")]

DiscordSnowflakeStr = Annotated[str, AfterValidator(_validate_snowflake_str)]
GuildIdStr = Annotated[DiscordSnowflakeStr, Field(description="Discord guild ID (decimal string)")]
RoleIdStr = Annotated[DiscordSnowflakeStr, Field(description="Discord role ID (decimal string)")]
ChannelIdStr = Annotated[DiscordSnowflakeStr, Field(description="Discord channel ID (decimal string)")]
UserIdStr = Annotated[DiscordSnowflakeStr, Field(description="Discord user ID (decimal string)")]
MessageIdStr = Annotated[DiscordSnowflakeStr, Field(description="Discord message ID (decimal string)")]
