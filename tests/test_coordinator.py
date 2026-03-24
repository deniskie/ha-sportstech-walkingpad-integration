"""Tests for WalkingPadCoordinator – protocol parsing and notification routing."""

from __future__ import annotations

import asyncio

import pytest

from custom_components.sportstech_walkingpad.const import (
    STATE_ERROR,
    STATE_IDLE,
    STATE_PAUSED,
    STATE_RUNNING,
    STATE_SLEEP,
    STATE_STARTING,
    STATE_UNKNOWN,
)
from custom_components.sportstech_walkingpad.coordinator import (
    WalkingPadCoordinator,
    WalkingPadData,
    _build_frame,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _state_frame(
    raw_state: int,
    speed_x10: int = 0,
    incline: int = 0,
    time_lo: int = 0,
    time_hi: int = 0,
    dist_lo: int = 0,
    dist_hi: int = 0,
    cal_lo: int = 0,
    cal_hi: int = 0,
    steps_lo: int = 0,
    steps_hi: int = 0,
    heart: int = 0,
    extra: bytes = b"\x00\x00",
) -> bytes:
    """Build a fully valid 0x51 STATE response frame."""
    payload = bytes([
        0x51, raw_state, speed_x10, incline,
        time_lo, time_hi,
        dist_lo, dist_hi,
        cal_lo, cal_hi,
        steps_lo, steps_hi,
        heart,
    ]) + extra
    return _build_frame(payload)


# ---------------------------------------------------------------------------
# _parse_state_response  (tested via _on_notification for realism)
# ---------------------------------------------------------------------------

class TestParseStateResponse:
    def test_idle_state(self, make_coordinator: object) -> None:
        c: WalkingPadCoordinator = make_coordinator()
        c._on_notification(0, _state_frame(0))
        assert c.data.state == STATE_IDLE
        assert c.data.available is True

    def test_finish_maps_to_idle(self, make_coordinator: object) -> None:
        c: WalkingPadCoordinator = make_coordinator()
        c._on_notification(0, _state_frame(1))
        assert c.data.state == STATE_IDLE

    def test_starting_state(self, make_coordinator: object) -> None:
        c: WalkingPadCoordinator = make_coordinator()
        c._on_notification(0, _state_frame(2))
        assert c.data.state == STATE_STARTING

    def test_running_state(self, make_coordinator: object) -> None:
        c: WalkingPadCoordinator = make_coordinator()
        c._on_notification(0, _state_frame(3, speed_x10=35))
        assert c.data.state == STATE_RUNNING
        assert c.data.speed == pytest.approx(3.5)

    def test_stop_maps_to_idle(self, make_coordinator: object) -> None:
        c: WalkingPadCoordinator = make_coordinator()
        c._on_notification(0, _state_frame(4))
        assert c.data.state == STATE_IDLE

    def test_error_state(self, make_coordinator: object) -> None:
        c: WalkingPadCoordinator = make_coordinator()
        c._on_notification(0, _state_frame(5))
        assert c.data.state == STATE_ERROR

    def test_safety_key_maps_to_error(self, make_coordinator: object) -> None:
        c: WalkingPadCoordinator = make_coordinator()
        c._on_notification(0, _state_frame(6))
        assert c.data.state == STATE_ERROR

    def test_sleep_state(self, make_coordinator: object) -> None:
        c: WalkingPadCoordinator = make_coordinator()
        c._on_notification(0, _state_frame(7))
        assert c.data.state == STATE_SLEEP

    def test_paused_state(self, make_coordinator: object) -> None:
        c: WalkingPadCoordinator = make_coordinator()
        c._on_notification(0, _state_frame(10, speed_x10=20))
        assert c.data.state == STATE_PAUSED
        assert c.data.speed == pytest.approx(2.0)

    def test_unknown_raw_state(self, make_coordinator: object) -> None:
        c: WalkingPadCoordinator = make_coordinator()
        c._on_notification(0, _state_frame(99))
        assert c.data.state == STATE_UNKNOWN

    def test_running_full_metrics(self, make_coordinator: object) -> None:
        """All session-cumulative metrics decoded correctly."""
        c: WalkingPadCoordinator = make_coordinator()
        # time = 300 s (lo=0x2C, hi=0x01), dist = 500 m (lo=0xF4, hi=0x01)
        # cal = 12.3 kcal (123 → lo=0x7B, hi=0x00), steps = 600 (lo=0x58, hi=0x02), heart = 75
        frame = _state_frame(
            raw_state=3,
            speed_x10=40,
            incline=3,
            time_lo=0x2C, time_hi=0x01,
            dist_lo=0xF4, dist_hi=0x01,
            cal_lo=0x7B, cal_hi=0x00,
            steps_lo=0x58, steps_hi=0x02,
            heart=75,
        )
        c._on_notification(0, frame)
        assert c.data.state == STATE_RUNNING
        assert c.data.speed == pytest.approx(4.0)
        assert c.data.incline == 3
        assert c.data.time == 300
        assert c.data.distance == 500
        assert c.data.calories == pytest.approx(12.3)
        assert c.data.steps == 600
        assert c.data.heart == 75

    def test_idle_resets_speed(self, make_coordinator: object) -> None:
        """After RUNNING → IDLE, speed should be cleared to 0."""
        c: WalkingPadCoordinator = make_coordinator()
        c._on_notification(0, _state_frame(3, speed_x10=30))
        assert c.data.speed == pytest.approx(3.0)
        c._on_notification(0, _state_frame(0))
        assert c.data.speed == pytest.approx(0.0)

    def test_two_byte_little_endian_max(self, make_coordinator: object) -> None:
        """16-bit LE values max out at 65535."""
        c: WalkingPadCoordinator = make_coordinator()
        frame = _state_frame(3, dist_lo=0xFF, dist_hi=0xFF)
        c._on_notification(0, frame)
        assert c.data.distance == 65535

    def test_calories_resolution(self, make_coordinator: object) -> None:
        """Calories have 0.1 kcal resolution."""
        c: WalkingPadCoordinator = make_coordinator()
        frame = _state_frame(3, cal_lo=1, cal_hi=0)  # 1 * 0.1 = 0.1 kcal
        c._on_notification(0, frame)
        assert c.data.calories == pytest.approx(0.1)


# ---------------------------------------------------------------------------
# _on_notification routing
# ---------------------------------------------------------------------------

class TestNotificationRouting:
    def test_bad_frame_ignored(self, make_coordinator: object) -> None:
        c: WalkingPadCoordinator = make_coordinator()
        c._on_notification(0, b"\x02\xFF\xFF\x03")  # wrong checksum
        assert c.data.available is False  # never updated

    def test_wrong_msg_type_ignored(self, make_coordinator: object) -> None:
        """A valid frame with msg_type != 0x51 must not update data."""
        c: WalkingPadCoordinator = make_coordinator()
        frame = _build_frame(bytes([0x50, 0x02, 0x00]))  # param response, not state
        c._on_notification(0, frame)
        assert c.data.available is False

    def test_notification_sets_event(self, make_coordinator: object) -> None:
        c: WalkingPadCoordinator = make_coordinator()
        assert not c._notification_ready.is_set()
        c._on_notification(0, _state_frame(0))
        assert c._notification_ready.is_set()

    def test_bad_frame_does_not_set_event(self, make_coordinator: object) -> None:
        c: WalkingPadCoordinator = make_coordinator()
        c._on_notification(0, b"\x00\x00\x00\x00")
        assert not c._notification_ready.is_set()


# ---------------------------------------------------------------------------
# Disconnect callback
# ---------------------------------------------------------------------------

class TestDisconnectCallback:
    def test_on_disconnected_marks_unavailable(self, make_coordinator: object) -> None:
        from unittest.mock import MagicMock

        c: WalkingPadCoordinator = make_coordinator()
        c.data.available = True
        c._on_disconnected(MagicMock())
        assert c.data.available is False
        assert c._client is None

    def test_on_disconnected_wakes_poll(self, make_coordinator: object) -> None:
        from unittest.mock import MagicMock

        c: WalkingPadCoordinator = make_coordinator()
        c._on_disconnected(MagicMock())
        assert c._notification_ready.is_set()


# ---------------------------------------------------------------------------
# async_set_speed encoding
# ---------------------------------------------------------------------------

class TestSpeedEncoding:
    async def test_speed_clamped_to_255(self, make_coordinator: object) -> None:
        import sys
        from unittest.mock import AsyncMock, MagicMock

        c: WalkingPadCoordinator = make_coordinator()
        mock_client = MagicMock()
        mock_client.is_connected = True
        mock_client.write_gatt_char = AsyncMock()
        c._client = mock_client

        # Patch _ensure_connected to be a no-op
        async def _noop() -> None: ...
        c._ensure_connected = _noop  # type: ignore[method-assign]

        await c.async_set_speed(999.9)
        call_args = mock_client.write_gatt_char.call_args
        frame: bytes = call_args[0][1]
        # frame = STX + [0x53, 0x02, speed_byte, incline] + XOR + ETX
        speed_byte = frame[3]
        assert speed_byte == 255

    async def test_speed_encoding(self, make_coordinator: object) -> None:
        from unittest.mock import AsyncMock, MagicMock

        c: WalkingPadCoordinator = make_coordinator()
        mock_client = MagicMock()
        mock_client.is_connected = True
        mock_client.write_gatt_char = AsyncMock()
        c._client = mock_client

        async def _noop() -> None: ...
        c._ensure_connected = _noop  # type: ignore[method-assign]

        await c.async_set_speed(3.5)
        frame: bytes = mock_client.write_gatt_char.call_args[0][1]
        assert frame[3] == 35  # 3.5 * 10


# ---------------------------------------------------------------------------
# async_set_incline encoding
# ---------------------------------------------------------------------------

class TestInclineEncoding:
    async def test_incline_encoding(self, make_coordinator: object) -> None:
        from unittest.mock import AsyncMock, MagicMock

        c: WalkingPadCoordinator = make_coordinator()
        mock_client = MagicMock()
        mock_client.is_connected = True
        mock_client.write_gatt_char = AsyncMock()
        c._client = mock_client
        c.data.speed = 3.0

        async def _noop() -> None: ...
        c._ensure_connected = _noop  # type: ignore[method-assign]

        await c.async_set_incline(5)
        frame: bytes = mock_client.write_gatt_char.call_args[0][1]
        assert frame[3] == 30  # current speed 3.0 * 10
        assert frame[4] == 5   # incline

    async def test_incline_clamped_to_max(self, make_coordinator: object) -> None:
        from unittest.mock import AsyncMock, MagicMock

        c: WalkingPadCoordinator = make_coordinator()
        mock_client = MagicMock()
        mock_client.is_connected = True
        mock_client.write_gatt_char = AsyncMock()
        c._client = mock_client
        c.data.max_incline = 10

        async def _noop() -> None: ...
        c._ensure_connected = _noop  # type: ignore[method-assign]

        await c.async_set_incline(99)
        frame: bytes = mock_client.write_gatt_char.call_args[0][1]
        assert frame[4] == 10  # clamped to max_incline


# ---------------------------------------------------------------------------
# _parse_param_response
# ---------------------------------------------------------------------------

class TestParamResponse:
    def test_speed_limits_parsed(self, make_coordinator: object) -> None:
        c: WalkingPadCoordinator = make_coordinator()
        # sub_cmd=0x02, maxSpeed=60 (6.0 km/h), minSpeed=5 (0.5 km/h)
        frame = _build_frame(bytes([0x50, 0x02, 60, 5, 0x00, 0x00]))
        c._on_notification(0, frame)
        assert c.data.max_speed == pytest.approx(6.0)
        assert c.data.min_speed == pytest.approx(0.5)
        assert c.data.params_received is True

    def test_incline_limits_parsed(self, make_coordinator: object) -> None:
        c: WalkingPadCoordinator = make_coordinator()
        # sub_cmd=0x03, maxIncline=12, minIncline=0
        frame = _build_frame(bytes([0x50, 0x03, 12, 0, 0x00, 0x00]))
        c._on_notification(0, frame)
        assert c.data.max_incline == 12
        assert c.data.min_incline == 0
        assert c.data.params_received is True

    def test_param_event_set(self, make_coordinator: object) -> None:
        c: WalkingPadCoordinator = make_coordinator()
        c._param_ready.clear()
        frame = _build_frame(bytes([0x50, 0x02, 60, 5, 0x00, 0x00]))
        c._on_notification(0, frame)
        assert c._param_ready.is_set()

    def test_too_short_ignored(self, make_coordinator: object) -> None:
        c: WalkingPadCoordinator = make_coordinator()
        # Frame too short — params_received must stay False
        frame = _build_frame(bytes([0x50, 0x02]))
        c._on_notification(0, frame)
        assert c.data.params_received is False

    def test_disconnect_wakes_param_event(self, make_coordinator: object) -> None:
        from unittest.mock import MagicMock

        c: WalkingPadCoordinator = make_coordinator()
        c._param_ready.clear()
        c._on_disconnected(MagicMock())
        assert c._param_ready.is_set()
