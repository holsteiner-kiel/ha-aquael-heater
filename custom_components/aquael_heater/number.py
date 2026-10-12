from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from homeassistant.components.number import NumberEntity, NumberEntityDescription
from homeassistant.const import UnitOfPower, UnitOfTemperature

from .const import (
    CALIBRATION_STEP,
    MAX_CALIBRATION_C,
    MAX_WATT,
    MIN_CALIBRATION_C,
    MIN_WATT,
    WATT_STEP,
)
from .entity import AquaelEntity


@dataclass(frozen=True, kw_only=True)
class AquaelNumberEntityDescription(NumberEntityDescription):
    display_name: str
    value_key: str
    setter: Callable[[object, float], object]


async def _set_max_power(entity: object, value: float) -> None:
    await entity.coordinator.client.set_max_watt(int(value))


async def _set_calibration(entity: object, value: float) -> None:
    await entity.coordinator.client.set_calibration(float(value))


NUMBERS: tuple[AquaelNumberEntityDescription, ...] = (
    AquaelNumberEntityDescription(
        key="max_power",
        name="Aquael Flow Heater BT Max power",
        display_name="Aquael Flow Heater BT Max power",
        value_key="max_watt",
        native_min_value=MIN_WATT,
        native_max_value=MAX_WATT,
        native_step=WATT_STEP,
        native_unit_of_measurement=UnitOfPower.WATT,
        setter=_set_max_power,
    ),
    AquaelNumberEntityDescription(
        key="temperature_calibration",
        name="Aquael Flow Heater BT Temperature calibration",
        display_name="Aquael Flow Heater BT Temperature calibration",
        value_key="calibration_c",
        native_min_value=MIN_CALIBRATION_C,
        native_max_value=MAX_CALIBRATION_C,
        native_step=CALIBRATION_STEP,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        setter=_set_calibration,
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
        self._attr_name = description.display_name

    @property
    def native_value(self) -> float | None:
        value = self.coordinator.data.get(self.entity_description.value_key)
        if value is None:
            return None
        return float(value)

    async def async_set_native_value(self, value: float) -> None:
        await self.entity_description.setter(self, value)
        await self.coordinator.async_request_refresh()
