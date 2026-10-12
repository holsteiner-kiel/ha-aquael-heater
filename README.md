# Aquael Heater

![Aquael Heater banner](docs/banner.svg)

Home Assistant custom integration for the **Aquael Flow Heater BT** using Home Assistant Bluetooth and ESPHome Bluetooth Proxy.

> Version 0.1.x is an early release based on community testing and reverse engineered BLE/GATT characteristics. It has been tested with one Aquael Flow Heater BT.

## Features

- Bluetooth discovery for `Flow Heater BT`
- Manual setup by discovered device or BLE address
- Climate entity for on/off and target temperature
- Mode select entity (`fixed` / `day_night`)
- Night temperature number entity
- Sunrise and sunset time entities
- Configurable polling interval
- Raw temperature diagnostic sensor, disabled by default
- Configuration entities for maximum power, temperature calibration, and transition duration

## Requirements

- Home Assistant with Bluetooth support
- A Bluetooth adapter supported by Home Assistant, or an ESPHome Bluetooth Proxy
- For ESPHome Bluetooth Proxy, active connections must be enabled:

```yaml
bluetooth_proxy:
  active: true
```

## Installation via HACS custom repository

1. Open HACS
2. Go to **Integrations**
3. Open the three-dot menu
4. Choose **Custom repositories**
5. Add this repository URL
6. Category: **Integration**
7. Install **Aquael Heater**
8. Restart Home Assistant
9. Add the integration from **Settings → Devices & services**

## Setup

The integration supports Bluetooth discovery for devices advertising as:

```text
Flow Heater BT
```

If discovery does not find the device, you can add it manually by BLE address, for example:

```text
AA:BB:CC:DD:EE:FF
```

## Entities

Enabled by default:

- `climate` - Aquael Flow Heater BT
- `select` - Mode
- `number` - Night temperature
- `time` - Sunrise
- `time` - Sunset

Configuration entities:

- `number` - Maximum power
- `number` - Temperature calibration
- `number` - Transition duration

Disabled by default:

- `sensor` - Raw temperature

## Notes

The integration has currently only been tested with one Aquael Flow Heater BT. Multiple heater support is not a goal for the initial release.

## Status

Current 0.1.x status:

- HACS custom repository installation: tested
- Bluetooth discovery: tested
- Manual setup: tested
- Climate entity: tested
- Max power write: tested
- Options flow: tested
- Long-term Bluetooth stability: under observation
