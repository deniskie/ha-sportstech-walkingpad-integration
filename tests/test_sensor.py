"""Tests for WalkingPad sensor entity wiring."""

from __future__ import annotations

import pytest

from custom_components.sportstech_walkingpad.coordinator import WalkingPadData
from custom_components.sportstech_walkingpad.sensor import SENSOR_DESCRIPTIONS, WalkingPadSensor

EXPECTED_KEYS = {"state", "speed", "incline", "heart_rate", "workout_time", "distance", "calories", "steps"}


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
