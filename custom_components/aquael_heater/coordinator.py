from __future__ import annotations

import asyncio
from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .ble import AquaelBluetoothClient
from .const import CONF_ADDRESS, CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)

BLE_READ_ATTEMPTS = 3
BLE_RETRY_DELAY_SECONDS = 2


class AquaelDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator for Aquael Flow Heater BT."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.entry = entry
        self.client = AquaelBluetoothClient(hass, entry.data[CONF_ADDRESS])
        poll_interval = int(entry.options.get(CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL))

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=poll_interval),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        last_error: Exception | None = None

        for attempt in range(1, BLE_READ_ATTEMPTS + 1):
            try:
                return await self.client.read_state()
            except Exception as err:  # noqa: BLE001
                last_error = err
                _LOGGER.warning(
                    "Failed to update Aquael Heater on attempt %s/%s: %s",
                    attempt,
                    BLE_READ_ATTEMPTS,
                    err,
                )

                if attempt < BLE_READ_ATTEMPTS:
                    await asyncio.sleep(BLE_RETRY_DELAY_SECONDS)

        if self.data:
            _LOGGER.warning(
                "Keeping last known Aquael Heater state after temporary BLE failure: %s",
                last_error,
            )
            return self.data

        raise UpdateFailed(f"Failed to update Aquael Heater: {last_error}")
