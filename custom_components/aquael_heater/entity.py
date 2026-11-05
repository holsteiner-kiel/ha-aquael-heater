from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_MODEL, DOMAIN, MANUFACTURER, MODEL_FLOW
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
    def available(self) -> bool:
        """Return availability based on fresh coordinator data."""
        return self.coordinator.data is not None and not self.coordinator.data_is_stale

    @property
    def device_info(self) -> DeviceInfo:
        model = self._entry.data.get(CONF_MODEL, MODEL_FLOW)

        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.unique_id)},
            name=self._entry.title or model,
            manufacturer=MANUFACTURER,
            model=model,
        )
