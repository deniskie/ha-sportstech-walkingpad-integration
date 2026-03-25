"""Switch entities for the Sportstech WalkingPad integration."""

from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
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
    """Set up WalkingPad switch entities from a config entry."""
    coordinator: WalkingPadCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([WalkingPadLightSwitch(coordinator)])


def _device_info(coordinator: WalkingPadCoordinator) -> DeviceInfo:
    return DeviceInfo(
        identifiers={(DOMAIN, coordinator.mac)},
        name=coordinator.device_name,
        manufacturer="Sportstech",
        model="WalkingPad",
    )


class WalkingPadLightSwitch(CoordinatorEntity[WalkingPadCoordinator], SwitchEntity):
    """Switch to toggle the WalkingPad LED light."""

    _attr_has_entity_name = True
    _attr_translation_key = "light"
    _attr_name = "Light"
    _attr_icon = "mdi:led-strip-variant"

    def __init__(self, coordinator: WalkingPadCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.mac}_light"
        self._attr_device_info = _device_info(coordinator)

    @property
    def is_on(self) -> bool:
        return self.coordinator.data.light_on

    async def async_turn_on(self, **kwargs: object) -> None:
        await self.coordinator.async_set_light(True)
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: object) -> None:
        await self.coordinator.async_set_light(False)
        self.async_write_ha_state()
