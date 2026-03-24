"""Config flow for the Sportstech WalkingPad integration."""

from __future__ import annotations

import logging
import re
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.components import bluetooth
from homeassistant.components.bluetooth import BluetoothServiceInfoBleak
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONF_DEVICE_NAME,
    CONF_MAC_ADDRESS,
    DEFAULT_DEVICE_NAME,
    DOMAIN,
    WALKINGPAD_SERVICE_UUID,
)

_LOGGER = logging.getLogger(__name__)

_MAC_RE = re.compile(r"^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$")


class WalkingPadConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):  # type: ignore[call-arg]
    """Handle a config flow for Sportstech WalkingPad."""

    VERSION = 1

    def __init__(self) -> None:
        self._discovered_devices: dict[str, str] = {}  # mac -> name
        self._mac: str | None = None
        self._name: str | None = None

    async def async_step_bluetooth(self, discovery_info: BluetoothServiceInfoBleak) -> FlowResult:
        """Handle device discovered via bluetooth integration."""
        await self.async_set_unique_id(discovery_info.address)
        self._abort_if_unique_id_configured()

        self._mac = discovery_info.address
        self._name = discovery_info.name or DEFAULT_DEVICE_NAME

        self.context["title_placeholders"] = {"name": self._name}
        return await self.async_step_confirm()

    async def async_step_confirm(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Confirm a bluetooth-discovered device."""
        if user_input is not None:
            return self.async_create_entry(
                title=self._name or DEFAULT_DEVICE_NAME,
                data={
                    CONF_MAC_ADDRESS: self._mac,
                    CONF_DEVICE_NAME: self._name,
                },
            )

        return self.async_show_form(
            step_id="confirm",
            description_placeholders={"name": self._name, "mac": self._mac},
            data_schema=vol.Schema({}),
        )

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle the initial step."""
        if WALKINGPAD_SERVICE_UUID:
            discovered = bluetooth.async_discovered_service_info(self.hass)
            for info in discovered:
                if WALKINGPAD_SERVICE_UUID.lower() in [s.lower() for s in info.service_uuids]:
                    self._discovered_devices[info.address] = info.name or info.address

        return await self.async_step_manual(user_input)

    async def async_step_manual(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle manual MAC address entry."""
        errors: dict[str, str] = {}

        if user_input is not None:
            mac = user_input[CONF_MAC_ADDRESS].upper().strip()
            if not _MAC_RE.match(mac):
                errors[CONF_MAC_ADDRESS] = "invalid_mac"
            else:
                await self.async_set_unique_id(mac)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=user_input.get(CONF_DEVICE_NAME, DEFAULT_DEVICE_NAME),
                    data={
                        CONF_MAC_ADDRESS: mac,
                        CONF_DEVICE_NAME: user_input.get(CONF_DEVICE_NAME, DEFAULT_DEVICE_NAME),
                    },
                )

        return self.async_show_form(
            step_id="manual",
            errors=errors,
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_MAC_ADDRESS): str,
                    vol.Optional(CONF_DEVICE_NAME, default=DEFAULT_DEVICE_NAME): str,
                }
            ),
        )
