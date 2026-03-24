# Sportstech WalkingPad – Home Assistant Integration (unofficial)

[\![Validate with hassfest](https://github.com/deniskie/ha-sportstech-walkingpad-integration/actions/workflows/hassfest.yaml/badge.svg)](https://github.com/deniskie/ha-sportstech-walkingpad-integration/actions/workflows/hassfest.yaml)
[\![Validate with HACS](https://github.com/deniskie/ha-sportstech-walkingpad-integration/actions/workflows/validate.yaml/badge.svg)](https://github.com/deniskie/ha-sportstech-walkingpad-integration/actions/workflows/validate.yaml)
[\![Tests](https://github.com/deniskie/ha-sportstech-walkingpad-integration/actions/workflows/tests.yaml/badge.svg)](https://github.com/deniskie/ha-sportstech-walkingpad-integration/actions/workflows/tests.yaml)

Unofficial Home Assistant integration for **Sportstech WalkingPad** treadmills using Bluetooth Low Energy (BLE). Reverse-engineered from the Sportstech Live app (v5.1.9).

## Features

- Auto-discovery via Bluetooth
- Live sensors: state, speed, incline, heart rate, workout time, distance, calories, steps
- Control services: start, stop, pause, set speed
- Persistent BLE connection with automatic reconnect

## Supported Devices

Any Sportstech WalkingPad treadmill that advertises the FitHome/F37 BLE service (`0000fff0-...`), including:

- Sportstech WalkingPad WP100
- Sportstech WalkingPad WP200
- Other FitHome-based OEM treadmills

> **Note:** This integration uses the proprietary FitHome BLE protocol (service `FFF0`, notify `FFF1`, write `FFF2`) and is not compatible with treadmills using the standard FTMS Bluetooth profile.

## Installation

### HACS (recommended)

1. Open HACS in Home Assistant
2. Go to **Integrations** → menu → **Custom repositories**
3. Add `https://github.com/deniskie/ha-sportstech-walkingpad-integration` with category **Integration**
4. Install **Sportstech WalkingPad (unofficial)**
5. Restart Home Assistant

### Manual

1. Copy the `custom_components/sportstech_walkingpad/` folder into your HA `config/custom_components/` directory
2. Restart Home Assistant

## Configuration

1. Make sure your WalkingPad is powered on and Bluetooth is enabled on your HA host
2. Go to **Settings → Devices & Services → Add Integration**
3. Search for **Sportstech WalkingPad**
4. Either confirm the auto-discovered device or enter the MAC address manually

## Sensors

| Entity | Unit | Description |
|---|---|---|
| `sensor.walkingpad_state` | — | Current state: `idle`, `starting`, `running`, `paused`, `sleep`, `error` |
| `sensor.walkingpad_speed` | km/h | Current belt speed |
| `sensor.walkingpad_incline` | % | Current incline level |
| `sensor.walkingpad_heart_rate` | bpm | Heart rate (requires chest strap accessory) |
| `sensor.walkingpad_workout_time` | s | Elapsed workout time (current session) |
| `sensor.walkingpad_distance` | m | Distance covered (current session) |
| `sensor.walkingpad_calories` | kcal | Calories burned (current session) |
| `sensor.walkingpad_steps` | — | Step count (current session) |

Session metrics (time, distance, calories, steps) reset when the belt is stopped.

## Services

| Service | Parameters | Description |
|---|---|---|
| `sportstech_walkingpad.start` | — | Start the belt |
| `sportstech_walkingpad.stop` | — | Stop the belt |
| `sportstech_walkingpad.pause` | — | Pause the belt |
| `sportstech_walkingpad.set_speed` | `speed` (km/h, e.g. `3.5`) | Set belt speed |

## Protocol

The integration uses the proprietary FitHome/F37 BLE protocol, reverse-engineered from `com.fithome.bluetooth.BLEDevice` in the Sportstech Live 5.1.9 APK.

**BLE profile:**
- Service: `0000fff0-0000-1000-8000-00805f9b34fb`
- Notify (device → phone): `0000fff1-0000-1000-8000-00805f9b34fb`
- Write (phone → device): `0000fff2-0000-1000-8000-00805f9b34fb`

**Frame format:** `[0x02]` + payload + XOR(payload) + `[0x03]`

## Contributing

Bug reports and pull requests are welcome at [GitHub Issues](https://github.com/deniskie/ha-sportstech-walkingpad-integration/issues).

## License

MIT
