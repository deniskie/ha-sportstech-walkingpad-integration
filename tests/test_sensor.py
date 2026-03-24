"""Tests for WalkingPad sensor entity wiring."""

from __future__ import annotations

import pytest

from custom_components.sportstech_walkingpad.coordinator import WalkingPadData
from custom_components.sportstech_walkingpad.sensor import (
    SENSOR_DESCRIPTIONS,
    TOTAL_SENSOR_DESCRIPTIONS,
    WalkingPadSensor,
    WalkingPadTotalSensor,
)

EXPECTED_KEYS = {"state", "speed", "incline", "heart_rate", "workout_time", "distance", "calories", "steps"}
EXPECTED_TOTAL_KEYS = {"total_workout_time", "total_distance", "total_calories", "total_steps"}


class TestSensorDescriptions:
    def test_all_expected_keys_present(self) -> None:
        keys = {d.key for d in SENSOR_DESCRIPTIONS}
        assert keys == EXPECTED_KEYS

    def test_no_duplicate_keys(self) -> None:
        keys = [d.key for d in SENSOR_DESCRIPTIONS]
        assert len(keys) == len(set(keys))

    def test_all_have_value_fn(self) -> None:
        for desc in SENSOR_DESCRIPTIONS:
            assert callable(desc.value_fn), f"{desc.key} missing value_fn"


class TestSensorValueFunctions:
    """Test the value_fn lambdas against WalkingPadData directly – no HA entity needed."""

    def _data(self, **kw: object) -> WalkingPadData:
        d = WalkingPadData()
        for k, v in kw.items():
            setattr(d, k, v)
        return d

    def _fn(self, key: str):
        return next(d.value_fn for d in SENSOR_DESCRIPTIONS if d.key == key)

    def test_state_fn(self) -> None:
        assert self._fn("state")(self._data(state="running")) == "running"

    def test_speed_fn(self) -> None:
        assert self._fn("speed")(self._data(speed=3.5)) == pytest.approx(3.5)

    def test_incline_fn(self) -> None:
        assert self._fn("incline")(self._data(incline=5)) == 5

    def test_heart_rate_fn_zero_returns_none(self) -> None:
        assert self._fn("heart_rate")(self._data(heart=0)) is None

    def test_heart_rate_fn_nonzero(self) -> None:
        assert self._fn("heart_rate")(self._data(heart=72)) == 72

    def test_workout_time_fn(self) -> None:
        assert self._fn("workout_time")(self._data(time=300)) == 300

    def test_distance_fn(self) -> None:
        assert self._fn("distance")(self._data(distance=500)) == 500

    def test_calories_fn(self) -> None:
        assert self._fn("calories")(self._data(calories=12.3)) == pytest.approx(12.3)

    def test_steps_fn(self) -> None:
        assert self._fn("steps")(self._data(steps=1234)) == 1234


class TestSensorEntity:
    def _make_sensor(self, make_coordinator, key: str) -> WalkingPadSensor:
        coordinator = make_coordinator()
        desc = next(d for d in SENSOR_DESCRIPTIONS if d.key == key)
        return WalkingPadSensor(coordinator, desc)

    def test_unique_id_format(self, make_coordinator: object) -> None:
        sensor = self._make_sensor(make_coordinator, "speed")
        assert sensor._attr_unique_id == "AA:BB:CC:DD:EE:FF_speed"

    def test_unique_ids_are_unique_per_coordinator(self, make_coordinator: object) -> None:
        coordinator = make_coordinator()
        sensors = [WalkingPadSensor(coordinator, d) for d in SENSOR_DESCRIPTIONS]
        ids = [s._attr_unique_id for s in sensors]
        assert len(ids) == len(set(ids))

    def test_available_reflects_data(self, make_coordinator: object) -> None:
        coordinator = make_coordinator()
        desc = next(d for d in SENSOR_DESCRIPTIONS if d.key == "state")
        sensor = WalkingPadSensor(coordinator, desc)
        assert sensor.available is False
        coordinator.data.available = True
        assert sensor.available is True

    def test_native_value_delegates_to_value_fn(self, make_coordinator: object) -> None:
        coordinator = make_coordinator()
        coordinator.data.speed = 2.5
        desc = next(d for d in SENSOR_DESCRIPTIONS if d.key == "speed")
        sensor = WalkingPadSensor(coordinator, desc)
        assert sensor.native_value == pytest.approx(2.5)


class TestTotalSensorDescriptions:
    def test_all_expected_total_keys_present(self) -> None:
        keys = {d.key for d in TOTAL_SENSOR_DESCRIPTIONS}
        assert keys == EXPECTED_TOTAL_KEYS

    def test_no_duplicate_keys(self) -> None:
        keys = [d.key for d in TOTAL_SENSOR_DESCRIPTIONS]
        assert len(keys) == len(set(keys))

    def test_all_have_value_fn(self) -> None:
        for desc in TOTAL_SENSOR_DESCRIPTIONS:
            assert callable(desc.value_fn), f"{desc.key} missing value_fn"


class TestWalkingPadTotalSensor:
    def _make_total(self, make_coordinator, key: str) -> WalkingPadTotalSensor:
        coordinator = make_coordinator()
        desc = next(d for d in TOTAL_SENSOR_DESCRIPTIONS if d.key == key)
        return WalkingPadTotalSensor(coordinator, desc)

    def test_initial_value_is_zero(self, make_coordinator: object) -> None:
        sensor = self._make_total(make_coordinator, "total_steps")
        assert sensor._attr_native_value == 0.0

    def test_accumulates_on_session_end(self, make_coordinator: object) -> None:
        """Session end detected when value drops from >0 to 0."""
        coordinator = make_coordinator()
        desc = next(d for d in TOTAL_SENSOR_DESCRIPTIONS if d.key == "total_steps")
        sensor = WalkingPadTotalSensor(coordinator, desc)

        # Session 1: 500 steps, then stop
        coordinator.data.steps = 500
        sensor._handle_coordinator_update()
        coordinator.data.steps = 0
        sensor._handle_coordinator_update()
        assert sensor._attr_native_value == pytest.approx(500)

        # Session 2: 300 steps, then stop
        coordinator.data.steps = 300
        sensor._handle_coordinator_update()
        coordinator.data.steps = 0
        sensor._handle_coordinator_update()
        assert sensor._attr_native_value == pytest.approx(800)

    def test_no_accumulation_while_running(self, make_coordinator: object) -> None:
        """Rising values during a session must not trigger accumulation."""
        coordinator = make_coordinator()
        desc = next(d for d in TOTAL_SENSOR_DESCRIPTIONS if d.key == "total_distance")
        sensor = WalkingPadTotalSensor(coordinator, desc)

        for dist in [100, 200, 350, 500]:
            coordinator.data.distance = dist
            sensor._handle_coordinator_update()

        assert sensor._attr_native_value == pytest.approx(0)

    def test_calories_fractional_accumulation(self, make_coordinator: object) -> None:
        coordinator = make_coordinator()
        desc = next(d for d in TOTAL_SENSOR_DESCRIPTIONS if d.key == "total_calories")
        sensor = WalkingPadTotalSensor(coordinator, desc)

        coordinator.data.calories = 12.3
        sensor._handle_coordinator_update()
        coordinator.data.calories = 0.0
        sensor._handle_coordinator_update()
        assert sensor._attr_native_value == pytest.approx(12.3)

    def test_multiple_sessions_accumulate(self, make_coordinator: object) -> None:
        coordinator = make_coordinator()
        desc = next(d for d in TOTAL_SENSOR_DESCRIPTIONS if d.key == "total_workout_time")
        sensor = WalkingPadTotalSensor(coordinator, desc)

        sessions = [300, 450, 180]
        for duration in sessions:
            coordinator.data.time = duration
            sensor._handle_coordinator_update()
            coordinator.data.time = 0
            sensor._handle_coordinator_update()

        assert sensor._attr_native_value == pytest.approx(sum(sessions))

    async def test_restore_previous_total(self, make_coordinator: object) -> None:
        """Total is restored from persisted state after HA restart."""
        coordinator = make_coordinator()
        desc = next(d for d in TOTAL_SENSOR_DESCRIPTIONS if d.key == "total_steps")
        sensor = WalkingPadTotalSensor(coordinator, desc)
        sensor._restore_native_value = 9500.0

        await sensor.async_added_to_hass()
        assert sensor._attr_native_value == pytest.approx(9500.0)

    async def test_new_session_added_to_restored_total(self, make_coordinator: object) -> None:
        """Session after HA restart adds on top of restored total."""
        coordinator = make_coordinator()
        desc = next(d for d in TOTAL_SENSOR_DESCRIPTIONS if d.key == "total_steps")
        sensor = WalkingPadTotalSensor(coordinator, desc)
        sensor._restore_native_value = 5000.0

        await sensor.async_added_to_hass()

        coordinator.data.steps = 200
        sensor._handle_coordinator_update()
        coordinator.data.steps = 0
        sensor._handle_coordinator_update()

        assert sensor._attr_native_value == pytest.approx(5200.0)

    def test_unique_id_format(self, make_coordinator: object) -> None:
        sensor = self._make_total(make_coordinator, "total_steps")
        assert sensor._attr_unique_id == "AA:BB:CC:DD:EE:FF_total_steps"
