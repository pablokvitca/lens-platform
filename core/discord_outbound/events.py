# core/discord_outbound/events.py
from datetime import datetime

import discord


async def create_scheduled_event(
    guild: discord.Guild,
    name: str,
    start_time: datetime,
    end_time: datetime,
    channel: discord.VoiceChannel,
    description: str = "",
) -> discord.ScheduledEvent:
    """Create a Discord scheduled event in a voice channel."""
    return await guild.create_scheduled_event(
        name=name,
        start_time=start_time,
        end_time=end_time,
        channel=channel,
        description=description,
        privacy_level=discord.PrivacyLevel.guild_only,
    )
