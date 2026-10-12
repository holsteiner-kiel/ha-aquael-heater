from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from homeassistant.components.number import NumberEntity, NumberEntityDescription
from homeassistant.const import UnitOfPower, UnitOfTemperature

from .const import (
    CALIBRATION_STEP,
    MAX_CALIBRATION_C,
    MAX_TEMP_C,
    MAX_TRANSITION_MINUTES,
    MAX_WATT,
    MIN_CALIBRATION_C,
    MIN_TEMP_C,
    MIN_TRANSITION_MINUTES,
    MIN_WATT,
    TEMP_STEP,
    TRANSITION_STEP,
    WATT_STEP,
)
from .entity import AquaelEntity


@dataclass(frozen=True, kw_only=True)
class AquaelNumberEntityDescription(NumberEntityDescription):
    value_key: str
    setter: Callable[[object, float], object]


async def _set_max_power(entity: object, value: float) -> None:
    await entity.coordinator.client.set_max_watt(int(value))


async def _set_calibration(entity: object, value: float) -> None:
    await entity.coordinator.client.set_calibration(float(value))


async def _set_night_temperature(entity: object, value: float) -> None:
    await entity.coordinator.client.set_night_temperature(float(value))


async def _set_transition_duration(entity: object, value: float) -> None:
    await entity.coordinator.client.set_transition_minutes(int(value))


NUMBERS: tuple[AquaelNumberEntityDescription, ...] = (
    AquaelNumberEntityDescription(
        key="night_temperature",
        translation_key="night_temperature",
        value_key="night_temp_c",
        native_min_value=MIN_TEMP_C,
        native_max_value=MAX_TEMP_C,
        native_step=TEMP_STEP,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        setter=_set_night_temperature,
    ),
    AquaelNumberEntityDescription(
        key="temperature_calibration",
        translation_key="temperature_calibration",
        value_key="calibration_c",
        native_min_value=MIN_CALIBRATION_C,
        native_max_value=MAX_CALIBRATION_C,
        native_step=CALIBRATION_STEP,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        setter=_set_calibration,
    ),
    AquaelNumberEntityDescription(
        key="transition_duration",
        translation_key="transition_duration",
        value_key="transition_minutes",
        native_min_value=MIN_TRANSITION_MINUTES,
        native_max_value=MAX_TRANSITION_MINUTES,
        native_step=TRANSITION_STEP,
        native_unit_of_measurement="min",
        setter=_set_transition_duration,
    ),
    AquaelNumberEntityDescription(
        key="max_power",
        translation_key="max_power",
        value_key="max_watt",
        native_min_value=MIN_WATT,
        native_max_value=MAX_WATT,
        native_step=WATT_STEP,
        native_unit_of_measurement=UnitOfPower.WATT,
        setter=_set_max_power,
    ),
)


async def async_setup_entry(hass, entry, async_add_entities) -> None:
    coordinator = hass.data["aquael_heater"][entry.entry_id]
    async_add_entities(AquaelNumber(coordinator, entry, description) for description in NUMBERS)


class AquaelNumber(AquaelEntity, NumberEntity):
    entity_description: AquaelNumberEntityDescription

    def __init__(self, coordinator, entry, description: AquaelNumberEntityDescription) -> None:
        super().__init__(coordinator, entry, description.key)
        self.entity_description = description
        self._attr_translation_key = description.translation_key

    @property
    def native_value(self) -> float | None:
        value = self.coordinator.data.get(self.entity_description.value_key)
        if value is None:
            return None
        return float(value)

    async def async_set_native_value(self, value: float) -> None:
        await self.entity_description.setter(self, value)
        await self.coordinator.async_request_refresh()
