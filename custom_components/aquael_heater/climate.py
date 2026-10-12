from __future__ import annotations

from typing import Any

from homeassistant.components.climate import ClimateEntity, ClimateEntityFeature, HVACMode
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature

from .const import MAX_TEMP_C, MIN_TEMP_C, TEMP_STEP
from .entity import AquaelEntity


async def async_setup_entry(hass, entry, async_add_entities) -> None:
    coordinator = hass.data["aquael_heater"][entry.entry_id]
    async_add_entities([AquaelHeaterClimate(coordinator, entry)])


class AquaelHeaterClimate(AquaelEntity, ClimateEntity):
    """Climate entity for Aquael Flow Heater BT."""

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator, entry, "climate")
        self._attr_name = None
        self._attr_translation_key = "heater"
        self._attr_temperature_unit = UnitOfTemperature.CELSIUS
        self._attr_min_temp = MIN_TEMP_C
        self._attr_max_temp = MAX_TEMP_C
        self._attr_target_temperature_step = TEMP_STEP
        self._attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE
        self._attr_hvac_modes = [HVACMode.OFF, HVACMode.HEAT]

    @property
    def current_temperature(self) -> float | None:
        return self.coordinator.data.get("current_temp_corrected_c")

    @property
    def target_temperature(self) -> float | None:
        return self.coordinator.data.get("day_or_fixed_temp_c")

    @property
    def hvac_mode(self) -> HVACMode:
        return HVACMode.HEAT if self.coordinator.data.get("enabled") else HVACMode.OFF

    async def async_set_temperature(self, **kwargs: Any) -> None:
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return

        target_temperature = float(temperature)
        await self.coordinator.async_write_and_refresh(
            lambda: self.coordinator.client.set_target_temperature(target_temperature),
            expected_key="day_or_fixed_temp_c",
            expected_value=target_temperature,
            tolerance=0.05,
        )

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        if hvac_mode == HVACMode.HEAT:
            enabled = True
        elif hvac_mode == HVACMode.OFF:
            enabled = False
        else:
            return

        await self.coordinator.async_write_and_refresh(
            lambda: self.coordinator.client.set_enabled(enabled),
            expected_key="enabled",
            expected_value=enabled,
        )
