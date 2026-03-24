"""Tests for WalkingPad button entities."""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, patch

from custom_components.sportstech_walkingpad.button import (
    BUTTON_DESCRIPTIONS,
    WalkingPadButton,
)
from custom_components.sportstech_walkingpad.coordinator import WalkingPadCoordinator


class TestButtonDescriptions:
    def test_three_buttons_defined(self) -> None:
        assert len(BUTTON_DESCRIPTIONS) == 3

    def test_keys(self) -> None:
        keys = {d.key for d in BUTTON_DESCRIPTIONS}
        assert keys == {"start", "stop", "pause"}

    def test_all_have_icons(self) -> None:
        for desc in BUTTON_DESCRIPTIONS:
            assert desc.icon is not None

    def test_all_have_actions(self) -> None:
        for desc in BUTTON_DESCRIPTIONS:
            assert desc.action is not None


class TestWalkingPadButton:
    def _make_button(self, coordinator: WalkingPadCoordinator, key: str) -> WalkingPadButton:
        desc = next(d for d in BUTTON_DESCRIPTIONS if d.key == key)
        return WalkingPadButton(coordinator, desc)

    def test_unique_id(self, make_coordinator) -> None:
        c = make_coordinator(mac="AA:BB:CC:DD:EE:FF")
        btn = self._make_button(c, "start")
        assert btn._attr_unique_id == "AA:BB:CC:DD:EE:FF_start"

    def test_unavailable_when_data_unavailable(self, make_coordinator) -> None:
        c = make_coordinator()
        c.data.available = False
        btn = self._make_button(c, "stop")
        assert btn.available is False

    def test_available_when_data_available(self, make_coordinator) -> None:
        c = make_coordinator()
        c.data.available = True
        btn = self._make_button(c, "start")
        assert btn.available is True

    async def test_press_start_calls_async_start(self, make_coordinator) -> None:
        c = make_coordinator()
        c.async_start = AsyncMock()
        btn = self._make_button(c, "start")
        await btn.async_press()
        c.async_start.assert_awaited_once()

    async def test_press_stop_calls_async_stop(self, make_coordinator) -> None:
        c = make_coordinator()
        c.async_stop = AsyncMock()
        btn = self._make_button(c, "stop")
        await btn.async_press()
        c.async_stop.assert_awaited_once()

    async def test_press_pause_calls_async_pause(self, make_coordinator) -> None:
        c = make_coordinator()
        c.async_pause = AsyncMock()
        btn = self._make_button(c, "pause")
        await btn.async_press()
        c.async_pause.assert_awaited_once()
