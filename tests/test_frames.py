"""Tests for BLE frame helpers (pure functions, no HA/BLE deps needed)."""

from __future__ import annotations

import pytest

from custom_components.sportstech_walkingpad.coordinator import _build_frame, _validate_frame

# ---------------------------------------------------------------------------
# _build_frame
# ---------------------------------------------------------------------------

class TestBuildFrame:
    def test_state_query(self) -> None:
        """The well-known poll frame: 0x02 0x51 0x51 0x03."""
        frame = _build_frame(bytes([0x51]))
        assert frame == bytes([0x02, 0x51, 0x51, 0x03])

    def test_start_command(self) -> None:
        # payload [0x53, 0x01] → XOR = 0x52
        frame = _build_frame(bytes([0x53, 0x01]))
        assert frame[0] == 0x02
        assert frame[-1] == 0x03
        assert frame[1:-2] == bytes([0x53, 0x01])
        assert frame[-2] == 0x53 ^ 0x01  # 0x52

    def test_stop_command(self) -> None:
        # payload [0x53, 0x03] → XOR = 0x50
        frame = _build_frame(bytes([0x53, 0x03]))
        assert frame[-2] == 0x53 ^ 0x03  # 0x50

    def test_single_byte_xor_is_identity(self) -> None:
        """XOR of one byte equals itself."""
        for b in [0x00, 0x01, 0x7F, 0xFF]:
            frame = _build_frame(bytes([b]))
            assert frame[-2] == b

    def test_multi_byte_xor(self) -> None:
        payload = bytes([0x53, 0x02, 0x23, 0x00])  # set speed 3.5 km/h, incline 0
        frame = _build_frame(payload)
        expected_xor = 0x53 ^ 0x02 ^ 0x23 ^ 0x00
        assert frame[-2] == expected_xor

    def test_frame_length(self) -> None:
        payload = bytes([0xAA, 0xBB])
        assert len(_build_frame(payload)) == len(payload) + 3  # STX + payload + XOR + ETX


# ---------------------------------------------------------------------------
# _validate_frame
# ---------------------------------------------------------------------------

class TestValidateFrame:
    def test_valid_state_query(self) -> None:
        assert _validate_frame(bytes([0x02, 0x51, 0x51, 0x03])) is True

    def test_valid_multi_byte(self) -> None:
        frame = _build_frame(bytes([0x53, 0x01]))
        assert _validate_frame(frame) is True

    def test_wrong_stx(self) -> None:
        frame = bytearray(_build_frame(bytes([0x51])))
        frame[0] = 0x01
        assert _validate_frame(bytes(frame)) is False

    def test_wrong_etx(self) -> None:
        frame = bytearray(_build_frame(bytes([0x51])))
        frame[-1] = 0x02
        assert _validate_frame(bytes(frame)) is False

    def test_corrupt_checksum(self) -> None:
        frame = bytearray(_build_frame(bytes([0x51])))
        frame[-2] ^= 0xFF  # flip checksum
        assert _validate_frame(bytes(frame)) is False

    def test_too_short(self) -> None:
        assert _validate_frame(bytes([0x02, 0x03])) is False
        assert _validate_frame(bytes([0x02, 0x51, 0x03])) is False

    def test_empty(self) -> None:
        assert _validate_frame(b"") is False

    def test_roundtrip(self) -> None:
        """Any frame built by _build_frame must pass _validate_frame."""
        for payload in [bytes([b]) for b in range(256)]:
            assert _validate_frame(_build_frame(payload)) is True
