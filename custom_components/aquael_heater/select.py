from __future__ import annotations

from homeassistant.components.select import SelectEntity

from .const import MODES
from .entity import AquaelEntity


async def async_setup_entry(hass, entry, async_add_entities) -> None:
    coordinator = hass.data["aquael_heater"][entry.entry_id]
    async_add_entities([AquaelModeSelect(coordinator, entry)])


class AquaelModeSelect(AquaelEntity, SelectEntity):
    """Mode select for Aquael Flow Heater BT."""

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator, entry, "mode")
        self._attr_name = "Mode"
        self._attr_translation_key = "mode"
        self._attr_options = list(MODES)

    @property
    def current_option(self) -> str | None:
        mode = self.coordinator.data.get("mode")
        if mode in MODES:
            return mode
        return None

    async def async_select_option(self, option: str) -> None:
        if option not in MODES:
            return

        await self.coordinator.client.set_mode(option)
        await self.coordinator.async_request_refresh()
