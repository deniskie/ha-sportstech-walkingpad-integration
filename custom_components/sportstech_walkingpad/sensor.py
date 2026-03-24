"""Sensor entities for the Sportstech WalkingPad integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    RestoreSensor,
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    UnitOfLength,
    UnitOfSpeed,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import WalkingPadCoordinator


@dataclass(frozen=True)
class WalkingPadSensorDescription(SensorEntityDescription):
    """Extends SensorEntityDescription with a value accessor."""

    value_fn: Any = None  # Callable[[WalkingPadData], StateType]


# ---------------------------------------------------------------------------
# Session sensors (reset on each belt stop)
# ---------------------------------------------------------------------------

SENSOR_DESCRIPTIONS: tuple[WalkingPadSensorDescription, ...] = (
    WalkingPadSensorDescription(
        key="state",
        translation_key="state",
        name="State",
        icon="mdi:walk",
        value_fn=lambda d: d.state,
    ),
    WalkingPadSensorDescription(
        key="speed",
        translation_key="speed",
        name="Speed",
        native_unit_of_measurement=UnitOfSpeed.KILOMETERS_PER_HOUR,
        device_class=SensorDeviceClass.SPEED,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda d: d.speed,
    ),
    WalkingPadSensorDescription(
        key="incline",
        translation_key="incline",
        name="Incline",
        native_unit_of_measurement="%",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:slope-uphill",
        value_fn=lambda d: d.incline,
    ),
    WalkingPadSensorDescription(
        key="heart_rate",
        translation_key="heart_rate",
        name="Heart Rate",
        native_unit_of_measurement="bpm",
        device_class=SensorDeviceClass.HEART_RATE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.heart if d.heart > 0 else None,
    ),
    WalkingPadSensorDescription(
        key="workout_time",
        translation_key="workout_time",
        name="Workout Time",
        native_unit_of_measurement=UnitOfTime.SECONDS,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda d: d.time,
    ),
    WalkingPadSensorDescription(
        key="distance",
        translation_key="distance",
        name="Distance",
        native_unit_of_measurement=UnitOfLength.METERS,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda d: d.distance,
    ),
    WalkingPadSensorDescription(
        key="calories",
        translation_key="calories",
        name="Calories",
        native_unit_of_measurement="kcal",
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:fire",
        suggested_display_precision=1,
        value_fn=lambda d: d.calories,
    ),
    WalkingPadSensorDescription(
        key="steps",
        translation_key="steps",
        name="Steps",
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:foot-print",
        value_fn=lambda d: d.steps,
    ),
)

# ---------------------------------------------------------------------------
# Total (lifetime) sensors — accumulate across sessions, persist across reboots
# ---------------------------------------------------------------------------

TOTAL_SENSOR_DESCRIPTIONS: tuple[WalkingPadSensorDescription, ...] = (
    WalkingPadSensorDescription(
        key="total_workout_time",
        translation_key="total_workout_time",
        name="Total Workout Time",
        native_unit_of_measurement=UnitOfTime.SECONDS,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda d: d.time,
    ),
    WalkingPadSensorDescription(
        key="total_distance",
        translation_key="total_distance",
        name="Total Distance",
        native_unit_of_measurement=UnitOfLength.METERS,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda d: d.distance,
    ),
    WalkingPadSensorDescription(
        key="total_calories",
        translation_key="total_calories",
        name="Total Calories",
        native_unit_of_measurement="kcal",
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:fire",
        suggested_display_precision=1,
        value_fn=lambda d: d.calories,
    ),
    WalkingPadSensorDescription(
        key="total_steps",
        translation_key="total_steps",
        name="Total Steps",
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:foot-print",
        value_fn=lambda d: d.steps,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up WalkingPad sensor entities from a config entry."""
    coordinator: WalkingPadCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        *(WalkingPadSensor(coordinator, desc) for desc in SENSOR_DESCRIPTIONS),
        *(WalkingPadTotalSensor(coordinator, desc) for desc in TOTAL_SENSOR_DESCRIPTIONS),
    ])


# ---------------------------------------------------------------------------
# Entity classes
# ---------------------------------------------------------------------------

def _device_info(coordinator: WalkingPadCoordinator) -> DeviceInfo:
    return DeviceInfo(
        identifiers={(DOMAIN, coordinator.mac)},
        name=coordinator.device_name,
        manufacturer="Sportstech",
        model="WalkingPad",
    )


class WalkingPadSensor(CoordinatorEntity[WalkingPadCoordinator], SensorEntity):
    """Live session sensor — resets when the belt stops."""

    entity_description: WalkingPadSensorDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: WalkingPadCoordinator,
        description: WalkingPadSensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.mac}_{description.key}"
        self._attr_device_info = _device_info(coordinator)

    @property
    def available(self) -> bool:
        return self.coordinator.data.available

    @property
    def native_value(self):
        return self.entity_description.value_fn(self.coordinator.data)


class WalkingPadTotalSensor(CoordinatorEntity[WalkingPadCoordinator], RestoreSensor):
    """Lifetime accumulator sensor.

    Adds each completed session's value to a running total.
    A session end is detected when the coordinator resets the metric to 0
    after it was non-zero (belt stopped). The total is restored across
    HA restarts via RestoreSensor.
    """

    entity_description: WalkingPadSensorDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: WalkingPadCoordinator,
        description: WalkingPadSensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.mac}_{description.key}"
        self._attr_device_info = _device_info(coordinator)
        self._attr_native_value: float = 0.0
        self._last_session_value: float = 0.0

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last_data = await self.async_get_last_sensor_data()
        if last_data and last_data.native_value is not None:
            self._attr_native_value = float(last_data.native_value)

    @callback
    def _handle_coordinator_update(self) -> None:
        current = float(self.entity_description.value_fn(self.coordinator.data) or 0)
        if self._last_session_value > 0 and current == 0:
            # Session ended: commit the last known session value to the total
            self._attr_native_value = (self._attr_native_value or 0) + self._last_session_value
        self._last_session_value = current
        self.async_write_ha_state()
