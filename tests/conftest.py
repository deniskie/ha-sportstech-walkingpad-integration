"""Stub homeassistant and BLE dependencies so tests run without the full HA stack."""

from __future__ import annotations

import asyncio
import sys
import types
from dataclasses import dataclass, field
from datetime import timedelta
from unittest.mock import MagicMock

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mod(name: str, **attrs: object) -> types.ModuleType:
    m = types.ModuleType(name)
    for k, v in attrs.items():
        setattr(m, k, v)
    sys.modules[name] = m
    return m


# ---------------------------------------------------------------------------
# bleak
# ---------------------------------------------------------------------------

class _BleakClient:
    def __init__(self, *a: object, **kw: object) -> None:
        self.is_connected = False

    async def start_notify(self, *a: object, **kw: object) -> None: ...
    async def write_gatt_char(self, *a: object, **kw: object) -> None: ...
    async def disconnect(self) -> None: ...


_mod("bleak", BleakClient=_BleakClient)


# ---------------------------------------------------------------------------
# bleak_retry_connector
# ---------------------------------------------------------------------------

async def _establish_connection(
    client_class: type,
    device: object,
    name: str,
    disconnected_callback: object = None,
    **kw: object,
) -> _BleakClient:
    client = client_class()
    client.is_connected = True
    return client


_mod("bleak_retry_connector", establish_connection=_establish_connection)


# ---------------------------------------------------------------------------
# homeassistant.*
# ---------------------------------------------------------------------------

class _HomeAssistant:
    pass


_mod("homeassistant.core", HomeAssistant=_HomeAssistant)

_bluetooth_mod = _mod(
    "homeassistant.components.bluetooth",
    BluetoothServiceInfoBleak=MagicMock,
    async_ble_device_from_address=MagicMock(return_value=MagicMock()),
    async_discovered_service_info=MagicMock(return_value=[]),
)
_mod("homeassistant.components", bluetooth=_bluetooth_mod)


class UpdateFailed(Exception):
    pass


class _DataUpdateCoordinator:
    def __init__(
        self,
        hass: object,
        logger: object,
        *,
        name: str,
        update_interval: timedelta,
    ) -> None:
        self.hass = hass
        self.logger = logger
        self.name = name
        self.update_interval = update_interval
        self.data: object = None

    def __class_getitem__(cls, item: object) -> type:
        return cls

    async def _async_update_data(self) -> object:
        raise NotImplementedError


class _CoordinatorEntity:
    def __init__(self, coordinator: object) -> None:
        self.coordinator = coordinator

    def __class_getitem__(cls, item: object) -> type:
        return cls


_mod(
    "homeassistant.helpers.update_coordinator",
    DataUpdateCoordinator=_DataUpdateCoordinator,
    UpdateFailed=UpdateFailed,
    CoordinatorEntity=_CoordinatorEntity,
)
_mod("homeassistant.helpers.entity", DeviceInfo=dict)
_mod("homeassistant.helpers.entity_platform", AddEntitiesCallback=MagicMock)
_mod("homeassistant.helpers", update_coordinator=MagicMock(), entity=MagicMock())


class _SensorDeviceClass:
    SPEED = "speed"
    DISTANCE = "distance"
    DURATION = "duration"
    HEART_RATE = "heart_rate"


class _SensorStateClass:
    MEASUREMENT = "measurement"
    TOTAL_INCREASING = "total_increasing"


@dataclass(frozen=True)
class _SensorEntityDescription:
    """Minimal dataclass stub matching HA's SensorEntityDescription."""

    key: str = ""
    name: str | None = None
    translation_key: str | None = None
    icon: str | None = None
    device_class: str | None = None
    state_class: str | None = None
    native_unit_of_measurement: str | None = None
    suggested_display_precision: int | None = None
    entity_registry_enabled_default: bool = True


class _SensorEntity:
    pass


_mod(
    "homeassistant.components.sensor",
    SensorEntity=_SensorEntity,
    SensorDeviceClass=_SensorDeviceClass,
    SensorStateClass=_SensorStateClass,
    SensorEntityDescription=_SensorEntityDescription,
)


class _Platform:
    SENSOR = "sensor"


class _UnitOfSpeed:
    KILOMETERS_PER_HOUR = "km/h"


class _UnitOfLength:
    METERS = "m"


class _UnitOfTime:
    SECONDS = "s"


_mod(
    "homeassistant.const",
    Platform=_Platform,
    UnitOfSpeed=_UnitOfSpeed,
    UnitOfLength=_UnitOfLength,
    UnitOfTime=_UnitOfTime,
)


class _ConfigEntry:
    def __init__(self, entry_id: str = "test_entry", data: dict | None = None) -> None:
        self.entry_id = entry_id
        self.data = data or {}


_mod(
    "homeassistant.config_entries",
    ConfigEntry=_ConfigEntry,
    ConfigFlow=object,
)
_mod("homeassistant.data_entry_flow", FlowResult=dict)
_mod(
    "homeassistant",
    core=sys.modules["homeassistant.core"],
    components=sys.modules["homeassistant.components"],
    helpers=sys.modules["homeassistant.helpers"],
    config_entries=sys.modules["homeassistant.config_entries"],
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

import pytest  # noqa: E402 — must come after sys.modules setup


@pytest.fixture
def hass() -> _HomeAssistant:
    return _HomeAssistant()


@pytest.fixture
def make_coordinator(hass: _HomeAssistant):
    from custom_components.sportstech_walkingpad.coordinator import WalkingPadCoordinator

    def _make(mac: str = "AA:BB:CC:DD:EE:FF", name: str = "TestPad") -> WalkingPadCoordinator:
        c = WalkingPadCoordinator(hass, mac=mac, device_name=name, poll_interval=5)
        c._notification_ready = asyncio.Event()
        return c

    return _make
