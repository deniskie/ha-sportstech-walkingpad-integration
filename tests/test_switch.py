"""Tests for WalkingPad switch entities."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from custom_components.sportstech_walkingpad.switch import WalkingPadLightSwitch


class TestWalkingPadLightSwitch:
    def test_unique_id(self, make_coordinator) -> None:
        c = make_coordinator(mac="AA:BB:CC:DD:EE:FF")
        switch = WalkingPadLightSwitch(c)
        assert switch._attr_unique_id == "AA:BB:CC:DD:EE:FF_light"

    def test_is_off_by_default(self, make_coordinator) -> None:
        c = make_coordinator()
        switch = WalkingPadLightSwitch(c)
        assert switch.is_on is False

    def test_is_on_when_data_light_on(self, make_coordinator) -> None:
        c = make_coordinator()
        c.data.light_on = True
        switch = WalkingPadLightSwitch(c)
        assert switch.is_on is True

    async def test_turn_on(self, make_coordinator) -> None:
        c = make_coordinator()
        c.async_set_light = AsyncMock()
        switch = WalkingPadLightSwitch(c)
        switch.async_write_ha_state = lambda: None
        await switch.async_turn_on()
        c.async_set_light.assert_awaited_once_with(True)

    async def test_turn_off(self, make_coordinator) -> None:
        c = make_coordinator()
        c.async_set_light = AsyncMock()
        switch = WalkingPadLightSwitch(c)
        switch.async_write_ha_state = lambda: None
        await switch.async_turn_off()
        c.async_set_light.assert_awaited_once_with(False)


class TestLightCommand:
    async def test_light_on_sends_correct_frame(self, make_coordinator) -> None:
        from unittest.mock import AsyncMock, MagicMock

        c = make_coordinator()
        mock_client = MagicMock()
        mock_client.is_connected = True
        mock_client.write_gatt_char = AsyncMock()
        c._client = mock_client

        async def _noop() -> None: ...
        c._ensure_connected = _noop  # type: ignore[method-assign]

        await c.async_set_light(True)
        frame: bytes = mock_client.write_gatt_char.call_args[0][1]
        # frame = STX + [0x5C, 0x01, 0x01, 0x00, 0x00, 0x00] + XOR + ETX
        assert frame[1] == 0x5C
        assert frame[2] == 0x01
        assert frame[3] == 0x01  # on
        assert c.data.light_on is True

    async def test_light_off_sends_correct_frame(self, make_coordinator) -> None:
        from unittest.mock import AsyncMock, MagicMock

        c = make_coordinator()
        mock_client = MagicMock()
        mock_client.is_connected = True
        mock_client.write_gatt_char = AsyncMock()
        c._client = mock_client
        c.data.light_on = True

        async def _noop() -> None: ...
        c._ensure_connected = _noop  # type: ignore[method-assign]

        await c.async_set_light(False)
        frame: bytes = mock_client.write_gatt_char.call_args[0][1]
        assert frame[3] == 0x00  # off
        assert c.data.light_on is False
