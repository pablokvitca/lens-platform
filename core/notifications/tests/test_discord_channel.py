"""Tests for Discord notification channel."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestSendDiscordDM:
    @pytest.mark.asyncio
    async def test_sends_dm_to_user(self):
        from core.notifications.channels.discord import send_discord_dm

        mock_bot = MagicMock()
        mock_user = AsyncMock()
        mock_bot.fetch_user = AsyncMock(return_value=mock_user)

        with patch("core.notifications.channels.discord._bot", mock_bot):
            result = await send_discord_dm(
                discord_id="123456789",
                message="Hello!",
            )

        assert result is True
        mock_bot.fetch_user.assert_called_once_with(123456789)
        mock_user.send.assert_called_once_with("Hello!")

    @pytest.mark.asyncio
    async def test_returns_false_when_bot_not_set(self):
        from core.notifications.channels.discord import send_discord_dm

        with patch("core.notifications.channels.discord._bot", None):
            result = await send_discord_dm(
                discord_id="123456789",
                message="Hello!",
            )

        assert result is False


class TestSendDiscordChannelMessage:
    @pytest.mark.asyncio
    async def test_sends_message_to_channel(self):
        from core.notifications.channels.discord import send_discord_channel_message

        mock_bot = MagicMock()
        mock_channel = AsyncMock()
        mock_bot.fetch_channel = AsyncMock(return_value=mock_channel)

        with patch("core.notifications.channels.discord._bot", mock_bot):
            result = await send_discord_channel_message(
                channel_id="987654321",
                message="Meeting reminder!",
            )

        assert result is True
        mock_bot.fetch_channel.assert_called_once_with(987654321)
        mock_channel.send.assert_called_once_with("Meeting reminder!")
