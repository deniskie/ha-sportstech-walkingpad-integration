"""Constants for the Sportstech WalkingPad integration."""

DOMAIN = "sportstech_walkingpad"

# Config entry keys
CONF_MAC_ADDRESS = "mac_address"
CONF_DEVICE_NAME = "device_name"

# Defaults
DEFAULT_DEVICE_NAME = "WalkingPad"

# ---------------------------------------------------------------------------
# BLE GATT UUIDs (from APK: com.fithome.bluetooth.BLEDevice)
# ---------------------------------------------------------------------------

# Primary service (FFF0) – standard FitHome/F37 treadmill protocol
WALKINGPAD_SERVICE_UUID = "0000fff0-0000-1000-8000-00805f9b34fb"

# Characteristics
CHAR_RECV_UUID = "0000fff1-0000-1000-8000-00805f9b34fb"  # Notify – device → phone
CHAR_SEND_UUID = "0000fff2-0000-1000-8000-00805f9b34fb"  # Write  – phone  → device

# Alternative FitHome service (some firmware variants)
FITHOME_SERVICE_UUID = "0000f100-0000-1000-8000-00805f9b34fb"
FITHOME_DATA_UUID    = "0000f101-0000-1000-8000-00805f9b34fb"

# ---------------------------------------------------------------------------
# Protocol frame bytes (from APK: com.fithome.bluetooth.BLEDevice constants)
# ---------------------------------------------------------------------------

# Command type bytes (first byte of payload sent to device)
CMD_DEVICE_INFO    = 0x41  # 65  – request device info / parameters
CMD_DEVICE_STATE   = 0x42  # 66  – request current state
CMD_DEVICE_DATA    = 0x43  # 67  – request sport data
CMD_DEVICE_CONTROL = 0x44  # 68  – send control command
CMD_PERIPHERAL     = 0x5C  # 92  – light / fan control

# Control sub-commands (second byte when CMD_DEVICE_CONTROL)
CTRL_READY  = 0x01  # device ready / wake
CTRL_START  = 0x02  # start belt
CTRL_PAUSE  = 0x03  # pause belt
CTRL_STOP   = 0x04  # stop / emergency stop
CTRL_LEVEL  = 0x05  # set resistance level

# Info sub-commands (second byte when CMD_DEVICE_INFO)
INFO_MODEL  = 0x00  # model identifier
INFO_PARAM  = 0x02  # speed / incline limits + feature flags

# ---------------------------------------------------------------------------
# Device state values reported by notifications (from BLEDevice)
# ---------------------------------------------------------------------------
STATE_NORMAL  = 0   # idle / standby
STATE_START   = 1   # starting up
STATE_RUNNING = 2   # belt running
STATE_PAUSED  = 3   # paused
STATE_SLEEP   = 20  # 0x14 – deep sleep
STATE_ERROR   = 21  # 0x15 – error / safety key removed

# ---------------------------------------------------------------------------
# Device types (from BLEDevice.type field)
# ---------------------------------------------------------------------------
TYPE_TREADMILL = 0
TYPE_TRAINER   = 1
TYPE_BICYCLE   = 2
TYPE_ROWER     = 3
TYPE_STEPPER   = 4
TYPE_STAIRER   = 5
TYPE_STRENGTH  = 6
TYPE_VIBRATOR  = 7
