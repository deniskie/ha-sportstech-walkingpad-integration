"""Number entities for the Sportstech WalkingPad integration."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfSpeed
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import WalkingPadCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up WalkingPad number entities from a config entry."""
    coordinator: WalkingPadCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        WalkingPadSpeedNumber(coordinator),
        WalkingPadInclineNumber(coordinator),
    ])


def _device_info(coordinator: WalkingPadCoordinator) -> DeviceInfo:
    return DeviceInfo(
        identifiers={(DOMAIN, coordinator.mac)},
        name=coordinator.device_name,
        manufacturer="Sportstech",
        model="WalkingPad",
    )


class WalkingPadSpeedNumber(CoordinatorEntity[WalkingPadCoordinator], NumberEntity):
    """Speed control — sets belt speed in km/h."""

    _attr_has_entity_name = True
    _attr_translation_key = "speed_control"
    _attr_name = "Speed"
    _attr_icon = "mdi:speedometer"
    _attr_mode = NumberMode.SLIDER
    _attr_native_step = 0.1
    _attr_native_unit_of_measurement = UnitOfSpeed.KILOMETERS_PER_HOUR

    def __init__(self, coordinator: WalkingPadCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.mac}_speed_control"
        self._attr_device_info = _device_info(coordinator)

    @property
    def available(self) -> bool:
        return self.coordinator.data.available

    @property
    def native_min_value(self) -> float:
        return self.coordinator.data.min_speed

    @property
    def native_max_value(self) -> float:
        return self.coordinator.data.max_speed

    @property
    def native_value(self) -> float:
        return self.coordinator.data.speed

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_set_speed(value)


class WalkingPadInclineNumber(CoordinatorEntity[WalkingPadCoordinator], NumberEntity):
    """Incline control — sets belt incline level."""

    _attr_has_entity_name = True
    _attr_translation_key = "incline_control"
    _attr_name = "Incline"
    _attr_icon = "mdi:slope-uphill"
    _attr_mode = NumberMode.SLIDER
    _attr_native_step = 1.0
    _attr_native_unit_of_measurement = "%"
    _attr_native_min_value = 0.0

    def __init__(self, coordinator: WalkingPadCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.mac}_incline_control"
        self._attr_device_info = _device_info(coordinator)

    @property
    def available(self) -> bool:
        return self.coordinator.data.available

    @property
    def native_max_value(self) -> float:
        return float(self.coordinator.data.max_incline)

    @property
    def native_value(self) -> float:
        return float(self.coordinator.data.incline)

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_set_incline(int(value))
