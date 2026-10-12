# Changelog

## 0.1.3

- Replace the empty brand icon with a visible integration icon.
- Reorder number entities so temperature calibration appears below transition duration.

## 0.1.2

- Add retries for temporary BLE read failures.
- Keep the last known state when a later polling update fails temporarily.

## 0.1.1

- Fix options flow crash when opening the integration configuration dialog.

## 0.1.0

- Initial HACS-ready development release
- Add Bluetooth discovery for `Flow Heater BT`
- Add manual setup flow with discovered-device selection and BLE address fallback
- Require user confirmation for Bluetooth-discovered devices
- Add climate entity for heater on/off and target temperature
- Add mode select entity (`fixed` / `day_night`)
- Add max power control
- Add night temperature control
- Add sunrise and sunset time controls
- Add transition duration control
- Add temperature calibration control
- Add configurable polling interval option
- Add raw temperature as disabled-by-default diagnostic sensor
- Add diagnostics support
- Add English and German config flow translations
- Add validation workflow for HACS and hassfest
