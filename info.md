# Aquael Heater

Home Assistant custom integration for the **Aquael Flow Heater BT** via Home Assistant Bluetooth or ESPHome Bluetooth Proxy.

Version 0.1.0 provides Bluetooth discovery, manual setup, climate control, max power, mode, night temperature, sunrise/sunset, transition duration, temperature calibration and a disabled-by-default raw temperature diagnostic sensor.

A connectable Bluetooth path is required because the heater is controlled through BLE/GATT reads and writes. For ESPHome Bluetooth Proxy, enable active connections:

```yaml
bluetooth_proxy:
  active: true
```
