# Aquael Heater

Home Assistant custom integration for the **Aquael Flow Heater BT** using Home Assistant Bluetooth and ESPHome Bluetooth Proxy.

> Early development version. The integration is based on reverse engineered BLE/GATT characteristics and has been tested with one Aquael Flow Heater BT.

## Features

- Bluetooth discovery for `Flow Heater BT`
- Manual setup by BLE address as fallback
- Climate entity for on/off and target temperature
- Max power number entity
- Temperature calibration number entity
- Mode select entity (`fixed` / `day_night`)
- Optional diagnostic sensors disabled by default

## Requirements

- Home Assistant with Bluetooth support
- A connectable Bluetooth adapter or ESPHome Bluetooth Proxy with active connections enabled
- Aquael Flow Heater BT

Recommended ESPHome Bluetooth Proxy configuration:

```yaml
esp32_ble_tracker:

bluetooth_proxy:
  active: true
```

Shelly Bluetooth proxies may expose advertisements but are not expected to support the active GATT read/write workflow required by this integration.

## Installation

### HACS custom repository

1. Open HACS.
2. Add this repository as a custom repository.
3. Category: Integration.
4. Install **Aquael Heater**.
5. Restart Home Assistant.

### Manual installation

Copy `custom_components/aquael_heater` into your Home Assistant `custom_components` directory and restart Home Assistant.

## Setup

Home Assistant should discover the heater when it sees a connectable BLE advertisement named `Flow Heater BT`.

You can also add the integration manually and enter the BLE address.

## Entities

Enabled by default:

- `climate` - Aquael Flow Heater BT
- `number` - Max power
- `number` - Temperature calibration
- `select` - Mode

Disabled by default:

- Raw temperature sensor
- Sunrise minutes sensor
- Sunset minutes sensor
- Transition minutes sensor
- Night temperature sensor

## Migration from MQTT bridge

Do not run an existing BLE/MQTT bridge and this integration at the same time. BLE devices often only allow one active connection.

During testing, stop the old bridge first:

```bash
sudo systemctl stop aquael-heater.service
```

## Status

Current proof of concept status:

- Read over ESPHome Bluetooth Proxy: tested
- Write over ESPHome Bluetooth Proxy: tested
- Climate entity: tested

## Disclaimer

This project is not affiliated with AQUAEL. The protocol details are based on community testing and reverse engineering.
