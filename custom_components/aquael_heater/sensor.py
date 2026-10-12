from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.const import EntityCategory, UnitOfTemperature

from .entity import AquaelEntity


@dataclass(frozen=True, kw_only=True)
class AquaelSensorEntityDescription(SensorEntityDescription):
    value_key: str


SENSORS: tuple[AquaelSensorEntityDescription, ...] = (
    AquaelSensorEntityDescription(
        key="raw_temperature",
        translation_key="raw_temperature",
        value_key="current_temp_raw_c",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
)


async def async_setup_entry(hass, entry, async_add_entities) -> None:
    coordinator = hass.data["aquael_heater"][entry.entry_id]
    async_add_entities(AquaelSensor(coordinator, entry, description) for description in SENSORS)


class AquaelSensor(AquaelEntity, SensorEntity):
    entity_description: AquaelSensorEntityDescription

    def __init__(self, coordinator, entry, description: AquaelSensorEntityDescription) -> None:
        super().__init__(coordinator, entry, description.key)
        self.entity_description = description
        self._attr_translation_key = description.translation_key

    @property
    def native_value(self) -> Any:
        return self.coordinator.data.get(self.entity_description.value_key)
