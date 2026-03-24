"""Sportstech WalkingPad Home Assistant integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import CONF_DEVICE_NAME, CONF_MAC_ADDRESS, CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL, DOMAIN
from .coordinator import WalkingPadCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]


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

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        coordinator: WalkingPadCoordinator = hass.data[DOMAIN].pop(entry.entry_id)
        await coordinator.async_disconnect()
    return unload_ok
