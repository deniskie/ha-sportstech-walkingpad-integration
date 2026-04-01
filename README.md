# Sportstech WalkingPad – Home Assistant Integration (unofficial)

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/v/release/deniskie/ha-sportstech-walkingpad-integration)](https://github.com/deniskie/ha-sportstech-walkingpad-integration/releases)
[![License](https://img.shields.io/github/license/deniskie/ha-sportstech-walkingpad-integration)](LICENSE)
[![Tests](https://img.shields.io/github/actions/workflow/status/deniskie/ha-sportstech-walkingpad-integration/tests.yaml?label=tests)](https://github.com/deniskie/ha-sportstech-walkingpad-integration/actions)
[![hassfest](https://img.shields.io/github/actions/workflow/status/deniskie/ha-sportstech-walkingpad-integration/hassfest.yaml?label=hassfest)](https://github.com/deniskie/ha-sportstech-walkingpad-integration/actions/workflows/hassfest.yaml)
[![validate](https://img.shields.io/github/actions/workflow/status/deniskie/ha-sportstech-walkingpad-integration/validate.yaml?label=validate)](https://github.com/deniskie/ha-sportstech-walkingpad-integration/actions/workflows/validate.yaml)

> **Unofficial community integration.** This project is not affiliated with, endorsed by,
> or connected to Sportstech Brands GmbH. "Sportstech" is a registered trademark of its respective owner.

Custom integration for **Sportstech WalkingPad** treadmills.
Connects via Bluetooth Low Energy, reads live metrics, and allows belt control.
No cloud, no account, fully local.

> **Protocol:** Reverse-engineered from the Sportstech Live APK (v5.1.9) — `com.fithome.bluetooth.BLEDevice`

---

## Installation

### Option A – HACS (recommended)

1. Open **HACS** in Home Assistant.
2. Click **⋮ → Custom repositories**.
3. Add `https://github.com/deniskie/ha-sportstech-walkingpad-integration` as **Integration**.
4. Search for **Sportstech WalkingPad** and install.
5. Restart Home Assistant.

### Option B – Manual

1. Download or clone this repository.
2. Copy the `custom_components/sportstech_walkingpad/` folder to your HA config directory:
   ```
   /config/custom_components/sportstech_walkingpad/
   ```
3. Restart Home Assistant.

### Setup

After restart, go to **Settings → Integrations → Add Integration** and search for **Sportstech WalkingPad**.

- If your WalkingPad is powered on and nearby, it may be **auto-discovered** via Bluetooth.
- Otherwise, enter the **MAC address** manually (visible in your router's device list or a BLE scanner app).

---

## Entities

### Sensors

| Entity | Unit | Description |
|--------|------|-------------|
| `sensor.walkingpad_state` | — | Belt state: `idle`, `starting`, `running`, `paused`, `sleep`, `error` |
| `sensor.walkingpad_speed` | km/h | Current belt speed |
| `sensor.walkingpad_incline` | % | Current incline level |
| `sensor.walkingpad_heart_rate` | bpm | Heart rate (requires accessory; `unavailable` if no sensor) |
| `sensor.walkingpad_workout_time` | min | Elapsed time of current session |
| `sensor.walkingpad_distance` | m | Distance covered in current session |
| `sensor.walkingpad_calories` | kcal | Calories burned in current session |
| `sensor.walkingpad_steps` | — | Step count of current session |

Session metrics (time, distance, calories, steps) reset when the belt is stopped.

> **Note:** The device timer resets after ~99:59 min. The integration detects this and continues accumulating the correct elapsed time.

### Total sensors

| Entity | Unit | Description |
|--------|------|-------------|
| `sensor.walkingpad_total_workout_time` | min | Lifetime accumulated workout time |
| `sensor.walkingpad_total_distance` | m | Lifetime accumulated distance |
| `sensor.walkingpad_total_calories` | kcal | Lifetime accumulated calories |
| `sensor.walkingpad_total_steps` | — | Lifetime accumulated step count |

Total sensors persist across HA restarts and accumulate each completed session.

### Switch

| Entity | Description |
|--------|-------------|
| `switch.walkingpad_led_light` | Turn the WalkingPad LED light on or off |

---

## Services

| Service | Parameter | Description |
|---------|-----------|-------------|
| `sportstech_walkingpad.start` | — | Start the belt |
| `sportstech_walkingpad.stop` | — | Stop the belt |
| `sportstech_walkingpad.pause` | — | Pause the belt |
| `sportstech_walkingpad.set_speed` | `speed` (float, km/h) | Set belt speed, e.g. `3.5` |

---

## Supported Devices

Any Sportstech WalkingPad that advertises the FitHome/F37 BLE service (`0000fff0-...`):

- Sportstech WalkingPad WP100
- Sportstech WalkingPad WP200
- Other FitHome-based OEM treadmills

> **Note:** This integration uses the proprietary FitHome BLE protocol and is **not** compatible
> with treadmills using the standard Bluetooth FTMS profile.

---

## Protocol

**BLE profile (FitHome/F37):**

| Role | UUID |
|------|------|
| Service | `0000fff0-0000-1000-8000-00805f9b34fb` |
| Notify (device → phone) | `0000fff1-0000-1000-8000-00805f9b34fb` |
| Write (phone → device) | `0000fff2-0000-1000-8000-00805f9b34fb` |

**Frame format:** `[0x02]` + payload + XOR(payload) + `[0x03]`

---

## Requirements

- Home Assistant **2024.1** or newer
- HA **Bluetooth** integration enabled (requires a compatible Bluetooth adapter or ESPHome proxy)
- `bleak-retry-connector` (declared in `manifest.json`, installed automatically by HA)

---

## Contributing & Feedback

Feedback and contributions are welcome.

- **Bug reports / feature requests:** [Open an issue](https://github.com/deniskie/ha-sportstech-walkingpad-integration/issues)
- **Pull requests:** PRs are welcome – please include a brief description of what was tested

---

## License

MIT – see [LICENSE](LICENSE)
