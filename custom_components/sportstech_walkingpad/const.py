"""Constants for the Sportstech WalkingPad integration."""

DOMAIN = "sportstech_walkingpad"

# Config entry keys
CONF_MAC_ADDRESS = "mac_address"
CONF_DEVICE_NAME = "device_name"
CONF_POLL_INTERVAL = "poll_interval"

# Defaults
DEFAULT_DEVICE_NAME = "WalkingPad"
DEFAULT_POLL_INTERVAL = 5  # seconds

# ---------------------------------------------------------------------------
# BLE GATT UUIDs (from APK: com.fithome.bluetooth.BLEDevice)
# ---------------------------------------------------------------------------

# Primary service (FFF0) – standard FitHome/F37 treadmill protocol
WALKINGPAD_SERVICE_UUID = "0000fff0-0000-1000-8000-00805f9b34fb"

# Characteristics
CHAR_RECV_UUID = "0000fff1-0000-1000-8000-00805f9b34fb"  # Notify – device → phone
CHAR_SEND_UUID = "0000fff2-0000-1000-8000-00805f9b34fb"  # Write  – phone  → device

# Alternative FitHome service (some firmware variants, protocol 3)
FITHOME_SERVICE_UUID = "0000f100-0000-1000-8000-00805f9b34fb"
FITHOME_DATA_UUID    = "0000f101-0000-1000-8000-00805f9b34fb"

# ---------------------------------------------------------------------------
# Protocol frame
# ---------------------------------------------------------------------------

# Every BLE packet is wrapped: [STX] + payload + XOR(payload) + [ETX]
FRAME_STX = 0x02
FRAME_ETX = 0x03

# ---------------------------------------------------------------------------
# Protocol 1 – Treadmill (FFF0 service, TYPE_TREADMILL=0)
# Command bytes sent to CHAR_SEND_UUID
# ---------------------------------------------------------------------------

CMD_STATE = bytes([0x51])        # Request current state + metrics
CMD_PARAM = bytes([0x50, 0x02])  # Request speed/incline limits

CMD_START = bytes([0x53, 0x01])  # Start belt
CMD_STOP  = bytes([0x53, 0x03])  # Stop belt
CMD_PAUSE = bytes([0x53, 0x0A])  # Pause belt (only if supportPause)
# Set speed: bytes([0x53, 0x02, speed_x10, incline])

# ---------------------------------------------------------------------------
# Raw state bytes in STATE notification (bArr[2] of type-0x51 response)
# ---------------------------------------------------------------------------

RAW_STATE_NORMAL  = 0
RAW_STATE_FINISH  = 1
RAW_STATE_START   = 2   # belt is starting up
RAW_STATE_RUNNING = 3   # belt running – full metrics in response
RAW_STATE_STOP    = 4
RAW_STATE_ERROR   = 5
RAW_STATE_SAFE    = 6   # safety key removed
RAW_STATE_SLEEP   = 7
RAW_STATE_PAUSE   = 10

# ---------------------------------------------------------------------------
# High-level HA state strings
# ---------------------------------------------------------------------------

STATE_IDLE     = "idle"
STATE_STARTING = "starting"
STATE_RUNNING  = "running"
STATE_PAUSED   = "paused"
STATE_STOPPING = "stopping"
STATE_SLEEP    = "sleep"
STATE_ERROR    = "error"
STATE_UNKNOWN  = "unknown"

# Mapping: raw notification byte → HA state string
RAW_STATE_MAP: dict[int, str] = {
    RAW_STATE_NORMAL:  STATE_IDLE,
    RAW_STATE_FINISH:  STATE_IDLE,
    RAW_STATE_START:   STATE_STARTING,
    RAW_STATE_RUNNING: STATE_RUNNING,
    RAW_STATE_STOP:    STATE_IDLE,
    RAW_STATE_ERROR:   STATE_ERROR,
    RAW_STATE_SAFE:    STATE_ERROR,
    RAW_STATE_SLEEP:   STATE_SLEEP,
    RAW_STATE_PAUSE:   STATE_PAUSED,
}

# States that carry live metric data in the STATE response
DATA_STATES = {STATE_RUNNING, STATE_PAUSED, STATE_STOPPING}
