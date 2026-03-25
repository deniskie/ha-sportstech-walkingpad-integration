"""BLE coordinator for the Sportstech WalkingPad integration.

Protocol: FitHome/F37 proprietary BLE (service FFF0, notify FFF1, write FFF2).

Frame format (both directions):
    [0x02]  payload bytes  XOR(payload)  [0x03]

Periodic poll (protocol 1 – treadmill):
    TX: [0x02, 0x51, 0x51, 0x03]
    RX: [0x02, 0x51, state, speed, incline, time_lo, time_hi,
             dist_lo, dist_hi, cal_lo, cal_hi, steps_lo, steps_hi,
             heart, …, checksum, 0x03]

Param query (protocol 1):
    Speed limits TX:   [0x02, 0x50, 0x02, 0x52, 0x03]
    Speed limits RX:   [0x02, 0x50, 0x02, maxSpeed*10, minSpeed*10, …]
    Incline limits TX: [0x02, 0x50, 0x03, 0x53, 0x03]
    Incline limits RX: [0x02, 0x50, 0x03, maxIncline, minIncline, …]

Source: reverse-engineered from com.fithome.bluetooth.BLEDevice
        in Sportstech Live 5.1.9 APK.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import timedelta

from bleak import BleakClient
from bleak_retry_connector import establish_connection
from homeassistant.components import bluetooth
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CHAR_RECV_UUID,
    CHAR_SEND_UUID,
    CMD_PARAM_INCLINE,
    CMD_PARAM_SPEED,
    CMD_PAUSE,
    CMD_START,
    CMD_STOP,
    DATA_STATES,
    DOMAIN,
    FRAME_ETX,
    FRAME_STX,
    RAW_STATE_MAP,
    STATE_IDLE,
    STATE_RUNNING,
    STATE_UNKNOWN,
)

_LOGGER = logging.getLogger(__name__)

_POLL_TIMEOUT = 10.0   # seconds to wait for a STATE notification
_PARAM_TIMEOUT = 5.0   # seconds to wait for a PARAM notification


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class WalkingPadData:
    """Latest snapshot from the WalkingPad."""

    available: bool = False
    state: str = STATE_IDLE

    # Live metrics – only valid when state is RUNNING / PAUSED
    speed: float = 0.0      # km/h  (0.0–max, resolution 0.1)
    incline: int = 0        # %     (0–15)
    heart: int = 0          # bpm   (0 = no sensor)

    # Session-cumulative metrics (reset on STOP)
    time: int = 0           # s
    distance: int = 0       # m
    calories: float = 0.0   # kcal
    steps: int = 0          # step count

    # Device limits (populated from PARAM query on connect)
    max_speed: float = 6.0   # km/h
    min_speed: float = 0.5   # km/h
    max_incline: int = 15    # %
    min_incline: int = 0     # %
    params_received: bool = False

    # Peripheral state (optimistic – no feedback from device)
    light_on: bool = False


# ---------------------------------------------------------------------------
# Frame helpers
# ---------------------------------------------------------------------------


def _build_frame(payload: bytes) -> bytes:
    """Wrap *payload* in STX + payload + XOR(payload) + ETX."""
    checksum = 0
    for b in payload:
        checksum ^= b
    return bytes([FRAME_STX]) + payload + bytes([checksum & 0xFF, FRAME_ETX])


def _validate_frame(data: bytes) -> bool:
    """Return True if *data* has correct framing and XOR checksum."""
    if len(data) < 4 or data[0] != FRAME_STX or data[-1] != FRAME_ETX:
        return False
    xor = 0
    for b in data[1:-1]:
        xor ^= b
    return xor == 0


# Pre-built poll frame (sent to FFF2)
_FRAME_STATE_QUERY = _build_frame(bytes([0x51]))


# ---------------------------------------------------------------------------
# Coordinator
# ---------------------------------------------------------------------------


class WalkingPadCoordinator(DataUpdateCoordinator[WalkingPadData]):
    """Manages the BLE connection and periodic state polling.

    A persistent connection is held; the update loop sends a STATE query
    every *poll_interval* seconds and parses the FFF1 notification reply.
    On first connect, speed and incline limits are queried via CMD_PARAM.
    """

    def __init__(
        self,
        hass: HomeAssistant,
        mac: str,
        device_name: str,
        poll_interval: int = 5,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{mac}",
            update_interval=timedelta(seconds=poll_interval),
        )
        self.mac = mac
        self.device_name = device_name

        self._client: BleakClient | None = None
        self._notification_ready = asyncio.Event()
        self._param_ready = asyncio.Event()
        self.data: WalkingPadData = WalkingPadData()

    # ------------------------------------------------------------------
    # DataUpdateCoordinator interface
    # ------------------------------------------------------------------

    async def _async_update_data(self) -> WalkingPadData:
        """Called by HA every *update_interval* seconds."""
        try:
            await self._ensure_connected()
            await self._poll_state()
        except Exception as exc:  # noqa: BLE001
            _LOGGER.debug("Poll failed for %s: %s", self.mac, exc)
            self.data.available = False
        return self.data

    # ------------------------------------------------------------------
    # Connection management
    # ------------------------------------------------------------------

    async def _ensure_connected(self) -> None:
        """(Re-)connect to the device if needed."""
        if self._client and self._client.is_connected:
            return

        ble_device = bluetooth.async_ble_device_from_address(
            self.hass, self.mac, connectable=False
        )
        if ble_device is None:
            raise UpdateFailed(f"WalkingPad {self.mac} not found via BLE scanner")

        _LOGGER.debug("Connecting to %s (%s)", self.device_name, self.mac)
        self._client = await establish_connection(
            BleakClient,
            ble_device,
            self.mac,
            disconnected_callback=self._on_disconnected,
        )
        await self._client.start_notify(CHAR_RECV_UUID, self._on_notification)
        _LOGGER.debug("Connected to %s", self.device_name)
        await self._query_params()

    def _on_disconnected(self, _client: BleakClient) -> None:
        _LOGGER.debug("WalkingPad %s disconnected", self.mac)
        self.data.available = False
        self._client = None
        # Wake up any waiting poll so it doesn't hang
        self._notification_ready.set()
        self._param_ready.set()

    # ------------------------------------------------------------------
    # Param query (device limits)
    # ------------------------------------------------------------------

    async def _query_params(self) -> None:
        """Query speed and incline limits from the device."""
        if not self._client or not self._client.is_connected:
            return
        try:
            self._param_ready.clear()
            await self._client.write_gatt_char(
                CHAR_SEND_UUID, _build_frame(CMD_PARAM_SPEED), response=False
            )
            await asyncio.wait_for(self._param_ready.wait(), timeout=_PARAM_TIMEOUT)
            self._param_ready.clear()
            await self._client.write_gatt_char(
                CHAR_SEND_UUID, _build_frame(CMD_PARAM_INCLINE), response=False
            )
            await asyncio.wait_for(self._param_ready.wait(), timeout=_PARAM_TIMEOUT)
        except asyncio.TimeoutError:
            _LOGGER.debug("No PARAM reply from %s – using defaults", self.mac)

    # ------------------------------------------------------------------
    # Polling
    # ------------------------------------------------------------------

    async def _poll_state(self) -> None:
        """Send a STATE query and wait up to *_POLL_TIMEOUT* s for the reply."""
        if not self._client or not self._client.is_connected:
            return

        self._notification_ready.clear()
        await self._client.write_gatt_char(CHAR_SEND_UUID, _FRAME_STATE_QUERY, response=False)

        try:
            await asyncio.wait_for(self._notification_ready.wait(), timeout=_POLL_TIMEOUT)
        except asyncio.TimeoutError:
            _LOGGER.debug("No STATE reply from %s within %.0f s", self.mac, _POLL_TIMEOUT)

    # ------------------------------------------------------------------
    # Notification handler
    # ------------------------------------------------------------------

    def _on_notification(self, _handle: int, data: bytes) -> None:
        """Called by bleak on every FFF1 notification."""
        if not _validate_frame(data):
            _LOGGER.debug("Bad frame from %s: %s", self.mac, data.hex())
            return

        msg_type = data[1]
        if msg_type == 0x51:
            self._parse_state_response(data)
            self._notification_ready.set()
        elif msg_type == 0x50:
            self._parse_param_response(data)
            self._param_ready.set()

    def _parse_state_response(self, data: bytes) -> None:
        """Parse a protocol-1 STATE response frame.

        Frame layout (after STX, before checksum+ETX):
          [0x51, raw_state, speed_x10, incline,
           time_lo, time_hi, dist_lo, dist_hi,
           cal_lo, cal_hi, steps_lo, steps_hi, heart]

        Data fields only populated when raw_state == RAW_STATE_RUNNING (3).
        """
        if len(data) < 5:
            return

        raw_state = data[2] & 0xFF
        ha_state = RAW_STATE_MAP.get(raw_state, STATE_UNKNOWN)

        self.data.state = ha_state
        self.data.available = True

        if ha_state in DATA_STATES and len(data) > 15:
            self.data.speed    = round((data[3] & 0xFF) * 0.1, 1)
            self.data.incline  = data[4] & 0xFF
            self.data.heart    = data[13] & 0xFF

            if ha_state == STATE_RUNNING:
                # Only RUNNING carries full session-cumulative data
                self.data.time     = (data[5] & 0xFF) | ((data[6] & 0xFF) << 8)
                self.data.distance = (data[7] & 0xFF) | ((data[8] & 0xFF) << 8)
                self.data.calories = round(((data[9] & 0xFF) | ((data[10] & 0xFF) << 8)) * 0.1, 1)
                self.data.steps    = (data[11] & 0xFF) | ((data[12] & 0xFF) << 8)
        elif ha_state == STATE_IDLE:
            self.data.speed = 0.0
            self.data.time = 0
            self.data.distance = 0
            self.data.calories = 0.0
            self.data.steps = 0
            self.data.heart = 0

    def _parse_param_response(self, data: bytes) -> None:
        """Parse a protocol-1 PARAM response frame.

        Sub-command 0x02 (speed limits):
          [0x50, 0x02, maxSpeed*10, minSpeed*10, flags, light]
        Sub-command 0x03 (incline limits):
          [0x50, 0x03, maxIncline, minIncline, flags, light]
        """
        if len(data) < 6:
            return

        sub_cmd = data[2] & 0xFF

        if sub_cmd == 0x02 and len(data) >= 7:
            self.data.max_speed = round((data[3] & 0xFF) / 10.0, 1)
            self.data.min_speed = round((data[4] & 0xFF) / 10.0, 1)
            self.data.params_received = True
            _LOGGER.debug(
                "Params from %s: max_speed=%.1f min_speed=%.1f",
                self.mac, self.data.max_speed, self.data.min_speed,
            )
        elif sub_cmd == 0x03 and len(data) >= 7:
            self.data.max_incline = data[3] & 0xFF
            self.data.min_incline = data[4] & 0xFF
            self.data.params_received = True
            _LOGGER.debug(
                "Params from %s: max_incline=%d min_incline=%d",
                self.mac, self.data.max_incline, self.data.min_incline,
            )

    # ------------------------------------------------------------------
    # Control commands
    # ------------------------------------------------------------------

    async def async_start(self) -> None:
        """Start the walking belt."""
        await self._ensure_connected()
        await self._send(CMD_START)

    async def async_stop(self) -> None:
        """Stop the walking belt."""
        await self._ensure_connected()
        await self._send(CMD_STOP)

    async def async_pause(self) -> None:
        """Pause the walking belt."""
        await self._ensure_connected()
        await self._send(CMD_PAUSE)

    async def async_set_speed(self, speed_kmh: float) -> None:
        """Set belt speed in km/h (e.g. 3.5 → byte value 35)."""
        await self._ensure_connected()
        speed_byte = max(0, min(255, round(speed_kmh * 10)))
        incline_byte = self.data.incline & 0xFF
        await self._send(bytes([0x53, 0x02, speed_byte, incline_byte]))

    async def async_set_incline(self, incline: int) -> None:
        """Set belt incline level (0–max_incline), keeping current speed."""
        await self._ensure_connected()
        speed_byte = max(0, min(255, round(self.data.speed * 10)))
        incline_byte = max(0, min(self.data.max_incline, incline)) & 0xFF
        await self._send(bytes([0x53, 0x02, speed_byte, incline_byte]))

    async def async_set_light(self, on: bool) -> None:
        """Turn the LED light on or off. State is tracked optimistically."""
        await self._ensure_connected()
        value = 0x01 if on else 0x00
        await self._send(bytes([0x5C, 0x01, value, 0x00, 0x00, 0x00]))
        self.data.light_on = on

    async def _send(self, payload: bytes) -> None:
        if not self._client or not self._client.is_connected:
            _LOGGER.warning("Cannot send command – not connected to %s", self.mac)
            return
        frame = _build_frame(payload)
        _LOGGER.debug("TX → %s: %s", self.mac, frame.hex())
        await self._client.write_gatt_char(CHAR_SEND_UUID, frame, response=False)

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def async_disconnect(self) -> None:
        """Disconnect cleanly on integration unload."""
        if self._client and self._client.is_connected:
            await self._client.disconnect()
        self._client = None
