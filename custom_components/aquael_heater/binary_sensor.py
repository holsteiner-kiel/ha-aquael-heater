from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.const import EntityCategory

from .entity import AquaelEntity


async def async_setup_entry(hass, entry, async_add_entities) -> None:
    coordinator = hass.data["aquael_heater"][entry.entry_id]
    async_add_entities([AquaelConnectivitySensor(coordinator, entry)])


class AquaelConnectivitySensor(AquaelEntity, BinarySensorEntity):
    """Whether the heater recently responded to a Bluetooth read."""

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_translation_key = "connectivity"

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator, entry, "connectivity")

    @property
    def available(self) -> bool:
        """Keep monitoring visible even when all heater control entities are stale."""
        return True

    @property
    def is_on(self) -> bool:
        """On means successful BLE communication within the freshness threshold."""
        return self.coordinator.data is not None and not self.coordinator.data_is_stale
