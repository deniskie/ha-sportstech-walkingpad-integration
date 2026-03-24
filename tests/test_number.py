"""Tests for WalkingPad number entities."""

from __future__ import annotations

from unittest.mock import AsyncMock

from custom_components.sportstech_walkingpad.number import (
    WalkingPadInclineNumber,
    WalkingPadSpeedNumber,
)


class TestSpeedNumber:
    def test_unique_id(self, make_coordinator) -> None:
        c = make_coordinator(mac="AA:BB:CC:DD:EE:FF")
        entity = WalkingPadSpeedNumber(c)
        assert entity._attr_unique_id == "AA:BB:CC:DD:EE:FF_speed_control"

    def test_native_value_reflects_current_speed(self, make_coordinator) -> None:
        c = make_coordinator()
        c.data.speed = 4.5
        entity = WalkingPadSpeedNumber(c)
        assert entity.native_value == 4.5

    def test_min_value_from_coordinator(self, make_coordinator) -> None:
        c = make_coordinator()
        c.data.min_speed = 0.5
        entity = WalkingPadSpeedNumber(c)
        assert entity.native_min_value == 0.5

    def test_max_value_from_coordinator(self, make_coordinator) -> None:
        c = make_coordinator()
        c.data.max_speed = 8.0
        entity = WalkingPadSpeedNumber(c)
        assert entity.native_max_value == 8.0

    def test_unavailable_when_data_unavailable(self, make_coordinator) -> None:
        c = make_coordinator()
        c.data.available = False
        entity = WalkingPadSpeedNumber(c)
        assert entity.available is False

    async def test_set_value_calls_async_set_speed(self, make_coordinator) -> None:
        c = make_coordinator()
        c.async_set_speed = AsyncMock()
        entity = WalkingPadSpeedNumber(c)
        await entity.async_set_native_value(3.5)
        c.async_set_speed.assert_awaited_once_with(3.5)


class TestInclineNumber:
    def test_unique_id(self, make_coordinator) -> None:
        c = make_coordinator(mac="AA:BB:CC:DD:EE:FF")
        entity = WalkingPadInclineNumber(c)
        assert entity._attr_unique_id == "AA:BB:CC:DD:EE:FF_incline_control"

    def test_native_value_reflects_current_incline(self, make_coordinator) -> None:
        c = make_coordinator()
        c.data.incline = 5
        entity = WalkingPadInclineNumber(c)
        assert entity.native_value == 5.0

    def test_max_value_from_coordinator(self, make_coordinator) -> None:
        c = make_coordinator()
        c.data.max_incline = 12
        entity = WalkingPadInclineNumber(c)
        assert entity.native_max_value == 12.0

    def test_min_value_is_zero(self, make_coordinator) -> None:
        c = make_coordinator()
        entity = WalkingPadInclineNumber(c)
        assert entity._attr_native_min_value == 0.0

    def test_unavailable_when_data_unavailable(self, make_coordinator) -> None:
        c = make_coordinator()
        c.data.available = False
        entity = WalkingPadInclineNumber(c)
        assert entity.available is False

    async def test_set_value_calls_async_set_incline(self, make_coordinator) -> None:
        c = make_coordinator()
        c.async_set_incline = AsyncMock()
        entity = WalkingPadInclineNumber(c)
        await entity.async_set_native_value(7.0)
        c.async_set_incline.assert_awaited_once_with(7)

    async def test_set_value_converts_to_int(self, make_coordinator) -> None:
        c = make_coordinator()
        c.async_set_incline = AsyncMock()
        entity = WalkingPadInclineNumber(c)
        await entity.async_set_native_value(3.9)
        c.async_set_incline.assert_awaited_once_with(3)
