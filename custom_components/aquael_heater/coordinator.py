from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from datetime import timedelta
import logging
import time
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .ble import AquaelBluetoothClient
from .const import CONF_ADDRESS, CONF_POLL_INTERVAL, DEFAULT_NAME, DEFAULT_POLL_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)

BLE_READ_ATTEMPTS = 3
BLE_RETRY_DELAY_SECONDS = 2
BLE_FAILURE_BACKOFF_BASE_SECONDS = 60
BLE_FAILURE_BACKOFF_MAX_SECONDS = 300
WRITE_REFRESH_ATTEMPTS = 3
WRITE_REFRESH_RETRY_DELAY_SECONDS = 1
STALE_DATA_TIMEOUT_SECONDS = 5 * 60
BLE_UNAVAILABLE_ISSUE_ID = "ble_unavailable"


class AquaelDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator for Aquael Flow Heater BT."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.entry = entry
        self.client = AquaelBluetoothClient(hass, entry.data[CONF_ADDRESS])
        self._last_successful_update: float | None = None
        self._failed_update_cycles = 0
        self._next_ble_retry_at = 0.0
        poll_interval = int(entry.options.get(CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL))

        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(seconds=poll_interval),
        )

    @property
    def data_is_stale(self) -> bool:
        """Return True when the last successful BLE read is too old."""
        if self._last_successful_update is None:
            return True
        return time.monotonic() - self._last_successful_update > STALE_DATA_TIMEOUT_SECONDS

    async def _async_update_data(self) -> dict[str, Any]:
        # Avoid hammering a heater that has stopped advertising over Bluetooth.
        if self.data and time.monotonic() < self._next_ble_retry_at:
            return self.data

        last_error: Exception | None = None

        for attempt in range(1, BLE_READ_ATTEMPTS + 1):
            try:
                data = await self.client.read_state()
            except Exception as err:  # noqa: BLE001
                last_error = err
                _LOGGER.debug(
                    "Failed to update Aquael Heater on attempt %s/%s: %s",
                    attempt,
                    BLE_READ_ATTEMPTS,
                    err,
                )

                if attempt < BLE_READ_ATTEMPTS:
                    await asyncio.sleep(BLE_RETRY_DELAY_SECONDS)
                continue

            self._mark_successful_update()
            return data

        self._failed_update_cycles += 1
        backoff = min(
            BLE_FAILURE_BACKOFF_BASE_SECONDS * (2 ** min(self._failed_update_cycles - 1, 3)),
            BLE_FAILURE_BACKOFF_MAX_SECONDS,
        )
        self._next_ble_retry_at = time.monotonic() + backoff
        if self._failed_update_cycles == 1:
            _LOGGER.warning(
                "Aquael Heater Bluetooth communication failed; retrying in %ss: %s",
                backoff,
                last_error,
            )
        else:
            _LOGGER.debug(
                "Aquael Heater still unreachable (failure cycle %s, retry in %ss): %s",
                self._failed_update_cycles,
                backoff,
                last_error,
            )

        if self.data and not self.data_is_stale:
            _LOGGER.debug(
                "Keeping last known Aquael Heater state after temporary BLE failure: %s",
                last_error,
            )
            return self.data

        self._async_create_ble_unavailable_issue(last_error)

        if self.data:
            _LOGGER.debug(
                "Aquael Heater data is stale after repeated BLE failures: %s",
                last_error,
            )
            return self.data

        raise UpdateFailed(f"Failed to update Aquael Heater: {last_error}")

    async def async_write_and_refresh(
        self,
        write_call: Callable[[], Awaitable[None]],
        *,
        expected_key: str | None = None,
        expected_value: Any | None = None,
        tolerance: float | None = None,
    ) -> None:
        """Write a value to the heater and refresh state directly afterwards."""
        await write_call()

        last_error: Exception | None = None
        latest_data: dict[str, Any] | None = None

        for attempt in range(1, WRITE_REFRESH_ATTEMPTS + 1):
            try:
                latest_data = await self.client.read_state()
            except Exception as err:  # noqa: BLE001
                last_error = err
                _LOGGER.warning(
                    "Failed to refresh Aquael Heater after write on attempt %s/%s: %s",
                    attempt,
                    WRITE_REFRESH_ATTEMPTS,
                    err,
                )
            else:
                self._mark_successful_update()
                self.async_set_updated_data(latest_data)

                if expected_key is None or self._matches_expected_value(
                    latest_data.get(expected_key),
                    expected_value,
                    tolerance,
                ):
                    return

                _LOGGER.debug(
                    "Aquael Heater write verification pending for %s: expected %r, got %r",
                    expected_key,
                    expected_value,
                    latest_data.get(expected_key),
                )

            if attempt < WRITE_REFRESH_ATTEMPTS:
                await asyncio.sleep(WRITE_REFRESH_RETRY_DELAY_SECONDS)

        if latest_data is not None:
            _LOGGER.warning(
                "Aquael Heater write did not verify after %s refresh attempts for %s: expected %r, got %r",
                WRITE_REFRESH_ATTEMPTS,
                expected_key,
                expected_value,
                latest_data.get(expected_key) if expected_key else None,
            )
            return

        self._async_create_ble_unavailable_issue(last_error)
        await self.async_request_refresh()

    @staticmethod
    def _matches_expected_value(
        actual: Any,
        expected: Any,
        tolerance: float | None,
    ) -> bool:
        """Return True when an actual value matches the expected value."""
        if expected is None:
            return actual is None

        if tolerance is not None:
            try:
                return abs(float(actual) - float(expected)) <= tolerance
            except (TypeError, ValueError):
                return False

        return actual == expected

    def _mark_successful_update(self) -> None:
        """Record successful communication and clear any stale repair issue."""
        self._last_successful_update = time.monotonic()
        if self._failed_update_cycles:
            _LOGGER.info("Aquael Heater Bluetooth communication recovered")
        self._failed_update_cycles = 0
        self._next_ble_retry_at = 0.0
        self._async_delete_ble_unavailable_issue()

    def _async_create_ble_unavailable_issue(self, error: Exception | None) -> None:
        """Create a Home Assistant repair issue for persistent BLE failures."""
        ir.async_create_issue(
            self.hass,
            DOMAIN,
            f"{self.entry.entry_id}_{BLE_UNAVAILABLE_ISSUE_ID}",
            is_fixable=False,
            severity=ir.IssueSeverity.WARNING,
            translation_key=BLE_UNAVAILABLE_ISSUE_ID,
            translation_placeholders={
                "device": DEFAULT_NAME,
                "error": str(error) if error else "unknown error",
            },
        )

    def _async_delete_ble_unavailable_issue(self) -> None:
        """Delete the BLE repair issue when communication works again."""
        ir.async_delete_issue(
            self.hass,
            DOMAIN,
            f"{self.entry.entry_id}_{BLE_UNAVAILABLE_ISSUE_ID}",
        )
