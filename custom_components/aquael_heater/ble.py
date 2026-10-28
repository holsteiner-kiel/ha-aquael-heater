from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

from bleak_retry_connector import BleakClientWithServiceCache, establish_connection
from homeassistant.components import bluetooth
from homeassistant.core import HomeAssistant

from .const import (
    DEFAULT_NAME,
    MODE_DAY_NIGHT,
    MODE_FIXED,
    UUID_CALIBRATION,
    UUID_CURRENT_TEMP_CORRECTED,
    UUID_CURRENT_TEMP_RAW,
    UUID_DAY_OR_FIXED_TEMP,
    UUID_ENABLED,
    UUID_MAX_WATT,
    UUID_MODE,
    UUID_NIGHT_TEMP,
    UUID_SUNRISE,
    UUID_SUNSET,
    UUID_TRANSITION_MINUTES,
)

_LOGGER = logging.getLogger(__name__)


class AquaelBluetoothError(Exception):
    """Base Aquael Bluetooth error."""


class AquaelDeviceNotFoundError(AquaelBluetoothError):
    """Aquael device was not found by Home Assistant Bluetooth."""


def u32le_to_int(data: bytes) -> int:
    if len(data) != 4:
        raise ValueError(f"Expected 4 bytes, got {len(data)}: {data.hex(' ')}")
    return int.from_bytes(data, byteorder="little", signed=False)


def s32le_to_int(data: bytes) -> int:
    if len(data) != 4:
        raise ValueError(f"Expected 4 bytes, got {len(data)}: {data.hex(' ')}")
    return int.from_bytes(data, byteorder="little", signed=True)


def int_to_u32le(value: int) -> bytes:
    if value < 0:
        raise ValueError("Value must be >= 0")
    return value.to_bytes(4, byteorder="little", signed=False)


def int_to_s32le(value: int) -> bytes:
    return value.to_bytes(4, byteorder="little", signed=True)


def device_to_temp(data: bytes) -> float:
    return u32le_to_int(data) / 100.0


def temp_to_device(temp_c: float) -> bytes:
    return int_to_u32le(int(round(temp_c * 100)))


def device_to_calibration(data: bytes) -> float:
    return s32le_to_int(data) / 100.0


def calibration_to_device(calibration_c: float) -> bytes:
    return int_to_s32le(int(round(calibration_c * 100)))


def device_to_mode(data: bytes) -> str:
    if len(data) != 1:
        raise ValueError(f"Unexpected mode payload: {data.hex(' ')}")
    return MODE_DAY_NIGHT if data[0] == 1 else MODE_FIXED


def mode_to_device(mode: str) -> bytes:
    if mode == MODE_FIXED:
        return bytes([0])
    if mode == MODE_DAY_NIGHT:
        return bytes([1])
    raise ValueError(f"Unsupported Aquael mode: {mode}")


def device_to_minutes(data: bytes) -> int:
    return u32le_to_int(data) // 60


def minutes_to_device(value_minutes: int) -> bytes:
    return int_to_u32le(int(value_minutes) * 60)


class AquaelBluetoothClient:
    """Bluetooth client for Aquael Flow Heater BT."""

    def __init__(self, hass: HomeAssistant, address: str) -> None:
        self.hass = hass
        self.address = address
        # One GATT connection at a time, including post-write verification.
        self._operation_lock = asyncio.Lock()

    async def _connect(self) -> BleakClientWithServiceCache:
        ble_device = bluetooth.async_ble_device_from_address(
            self.hass,
            self.address,
            connectable=True,
        )

        if ble_device is None:
            raise AquaelDeviceNotFoundError(
                f"Aquael Heater not found by HA Bluetooth: {self.address}"
            )

        _LOGGER.debug("Connecting to Aquael Heater %s (BLE device %r)", self.address, ble_device)
        started = time.monotonic()
        try:
            client = await establish_connection(
                BleakClientWithServiceCache,
                ble_device,
                DEFAULT_NAME,
                timeout=20,
            )
        except Exception:
            _LOGGER.debug(
                "Aquael BLE connection failed after %.2fs", time.monotonic() - started,
                exc_info=True,
            )
            raise
        _LOGGER.debug("Aquael BLE connection established in %.2fs", time.monotonic() - started)
        return client

    async def read_state(self) -> dict[str, Any]:
        async with self._operation_lock:
            started = time.monotonic()
            client = await self._connect()

            try:
                enabled_raw = await client.read_gatt_char(UUID_ENABLED)
                mode_raw = await client.read_gatt_char(UUID_MODE)
                day_temp_raw = await client.read_gatt_char(UUID_DAY_OR_FIXED_TEMP)
                night_temp_raw = await client.read_gatt_char(UUID_NIGHT_TEMP)
                max_watt_raw = await client.read_gatt_char(UUID_MAX_WATT)
                calibration_raw = await client.read_gatt_char(UUID_CALIBRATION)
                current_corrected_raw = await client.read_gatt_char(UUID_CURRENT_TEMP_CORRECTED)
                current_raw = await client.read_gatt_char(UUID_CURRENT_TEMP_RAW)
                sunrise_raw = await client.read_gatt_char(UUID_SUNRISE)
                sunset_raw = await client.read_gatt_char(UUID_SUNSET)
                transition_raw = await client.read_gatt_char(UUID_TRANSITION_MINUTES)

                state = {
                    "enabled": enabled_raw[0] == 1,
                    "mode": device_to_mode(mode_raw),
                    "day_or_fixed_temp_c": device_to_temp(day_temp_raw),
                    "night_temp_c": device_to_temp(night_temp_raw),
                    "max_watt": u32le_to_int(max_watt_raw),
                    "calibration_c": device_to_calibration(calibration_raw),
                    "current_temp_corrected_c": device_to_temp(current_corrected_raw),
                    "current_temp_raw_c": device_to_temp(current_raw),
                    "sunrise_minutes": device_to_minutes(sunrise_raw),
                    "sunset_minutes": device_to_minutes(sunset_raw),
                    "transition_minutes": device_to_minutes(transition_raw),
                }

                _LOGGER.debug("Read Aquael Heater state in %.2fs: %s", time.monotonic() - started, state)
                return state

            except Exception:
                _LOGGER.debug(
                    "Aquael BLE read failed after %.2fs", time.monotonic() - started,
                    exc_info=True,
                )
                raise
            finally:
                try:
                    await client.disconnect()
                except Exception:
                    _LOGGER.warning("Aquael BLE disconnect after read failed", exc_info=True)

    async def write_char(self, uuid: str, payload: bytes) -> None:
        async with self._operation_lock:
            started = time.monotonic()
            client = await self._connect()

            try:
                _LOGGER.debug(
                    "Writing Aquael Heater characteristic %s payload=%s",
                    uuid,
                    payload.hex(" "),
                )
                await client.write_gatt_char(uuid, payload, response=True)
                _LOGGER.debug("Aquael BLE write completed in %.2fs", time.monotonic() - started)
            except Exception:
                _LOGGER.debug(
                    "Aquael BLE write failed after %.2fs", time.monotonic() - started,
                    exc_info=True,
                )
                raise
            finally:
                try:
                    await client.disconnect()
                except Exception:
                    _LOGGER.warning("Aquael BLE disconnect after write failed", exc_info=True)

    async def set_enabled(self, enabled: bool) -> None:
        await self.write_char(UUID_ENABLED, bytes([1 if enabled else 0]))

    async def set_target_temperature(self, temperature: float) -> None:
        await self.write_char(UUID_DAY_OR_FIXED_TEMP, temp_to_device(temperature))

    async def set_night_temperature(self, temperature: float) -> None:
        await self.write_char(UUID_NIGHT_TEMP, temp_to_device(temperature))

    async def set_max_watt(self, watt: int) -> None:
        await self.write_char(UUID_MAX_WATT, int_to_u32le(watt))

    async def set_calibration(self, calibration: float) -> None:
        await self.write_char(UUID_CALIBRATION, calibration_to_device(calibration))

    async def set_mode(self, mode: str) -> None:
        await self.write_char(UUID_MODE, mode_to_device(mode))

    async def set_sunrise_minutes(self, minutes: int) -> None:
        await self.write_char(UUID_SUNRISE, minutes_to_device(minutes))

    async def set_sunset_minutes(self, minutes: int) -> None:
        await self.write_char(UUID_SUNSET, minutes_to_device(minutes))

    async def set_transition_minutes(self, minutes: int) -> None:
        await self.write_char(UUID_TRANSITION_MINUTES, minutes_to_device(minutes))
