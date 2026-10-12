from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .ble import AquaelBluetoothClient
from .const import CONF_ADDRESS, CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


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
        try:
            return await self.client.read_state()
        except Exception as err:
            raise UpdateFailed(f"Failed to update Aquael Heater: {err}") from err
