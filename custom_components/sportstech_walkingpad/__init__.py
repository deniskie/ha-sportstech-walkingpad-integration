"""Sportstech WalkingPad Home Assistant integration."""

from __future__ import annotations

import logging

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall

from .const import CONF_DEVICE_NAME, CONF_MAC_ADDRESS, CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL, DOMAIN
from .coordinator import WalkingPadCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BUTTON, Platform.NUMBER, Platform.SWITCH]

_ATTR_SPEED = "speed"
_ATTR_INCLINE = "incline"

_SERVICE_SET_SPEED_SCHEMA = vol.Schema({
    vol.Required(_ATTR_SPEED): vol.All(vol.Coerce(float), vol.Range(min=0, max=25)),
})
_SERVICE_SET_INCLINE_SCHEMA = vol.Schema({
    vol.Required(_ATTR_INCLINE): vol.All(vol.Coerce(int), vol.Range(min=0, max=15)),
})


def _all_coordinators(hass: HomeAssistant) -> list[WalkingPadCoordinator]:
    return list(hass.data.get(DOMAIN, {}).values())


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Sportstech WalkingPad from a config entry."""
    coordinator = WalkingPadCoordinator(
        hass,
        mac=entry.data[CONF_MAC_ADDRESS],
        device_name=entry.data.get(CONF_DEVICE_NAME, "WalkingPad"),
        poll_interval=entry.data.get(CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL),
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register services once (guard against multiple config entries)
    if not hass.services.has_service(DOMAIN, "start"):
        async def _start(_call: ServiceCall) -> None:
            for coord in _all_coordinators(hass):
                await coord.async_start()

        async def _stop(_call: ServiceCall) -> None:
            for coord in _all_coordinators(hass):
                await coord.async_stop()

        async def _pause(_call: ServiceCall) -> None:
            for coord in _all_coordinators(hass):
                await coord.async_pause()

        async def _set_speed(call: ServiceCall) -> None:
            speed: float = call.data[_ATTR_SPEED]
            for coord in _all_coordinators(hass):
                await coord.async_set_speed(speed)

        async def _set_incline(call: ServiceCall) -> None:
            incline: int = call.data[_ATTR_INCLINE]
            for coord in _all_coordinators(hass):
                await coord.async_set_incline(incline)

        hass.services.async_register(DOMAIN, "start", _start)
        hass.services.async_register(DOMAIN, "stop", _stop)
        hass.services.async_register(DOMAIN, "pause", _pause)
        hass.services.async_register(DOMAIN, "set_speed", _set_speed, schema=_SERVICE_SET_SPEED_SCHEMA)
        hass.services.async_register(DOMAIN, "set_incline", _set_incline, schema=_SERVICE_SET_INCLINE_SCHEMA)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        coordinator: WalkingPadCoordinator = hass.data[DOMAIN].pop(entry.entry_id)
        await coordinator.async_disconnect()

    # Remove services when no entries remain
    if not hass.data.get(DOMAIN):
        for service in ("start", "stop", "pause", "set_speed", "set_incline"):
            hass.services.async_remove(DOMAIN, service)

    return unload_ok
