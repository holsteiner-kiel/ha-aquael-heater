from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.const import EntityCategory, UnitOfTemperature

from .entity import AquaelEntity


@dataclass(frozen=True, kw_only=True)
class AquaelSensorEntityDescription(SensorEntityDescription):
    display_name: str
    value_key: str


SENSORS: tuple[AquaelSensorEntityDescription, ...] = (
    AquaelSensorEntityDescription(
        key="raw_temperature",
        name="Aquael Flow Heater BT Raw temperature",
        display_name="Aquael Flow Heater BT Raw temperature",
        value_key="current_temp_raw_c",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    AquaelSensorEntityDescription(
        key="night_temperature",
        name="Aquael Flow Heater BT Night temperature",
        display_name="Aquael Flow Heater BT Night temperature",
        value_key="night_temp_c",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    AquaelSensorEntityDescription(
        key="sunrise_minutes",
        name="Aquael Flow Heater BT Sunrise",
        display_name="Aquael Flow Heater BT Sunrise",
        value_key="sunrise_minutes",
        native_unit_of_measurement="min",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    AquaelSensorEntityDescription(
        key="sunset_minutes",
        name="Aquael Flow Heater BT Sunset",
        display_name="Aquael Flow Heater BT Sunset",
        value_key="sunset_minutes",
        native_unit_of_measurement="min",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    AquaelSensorEntityDescription(
        key="transition_minutes",
        name="Aquael Flow Heater BT Transition duration",
        display_name="Aquael Flow Heater BT Transition duration",
        value_key="transition_minutes",
        native_unit_of_measurement="min",
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
        self._attr_name = description.display_name

    @property
    def native_value(self) -> Any:
        return self.coordinator.data.get(self.entity_description.value_key)
