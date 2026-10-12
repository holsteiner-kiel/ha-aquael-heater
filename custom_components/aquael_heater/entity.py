from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER, MODEL
from .coordinator import AquaelDataUpdateCoordinator


class AquaelEntity(CoordinatorEntity[AquaelDataUpdateCoordinator]):
    """Base class for Aquael entities."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: AquaelDataUpdateCoordinator, entry, key: str) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._key = key
        self._attr_unique_id = f"{entry.unique_id}_{key}"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.unique_id)},
            name="Aquael Flow Heater BT",
            manufacturer=MANUFACTURER,
            model=MODEL,
        )
