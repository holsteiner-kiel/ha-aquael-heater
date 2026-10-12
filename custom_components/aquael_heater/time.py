from __future__ import annotations

from dataclasses import dataclass
from datetime import time
from typing import Callable

from homeassistant.components.time import TimeEntity, TimeEntityDescription

from .entity import AquaelEntity


def minutes_to_time(minutes: int | None) -> time | None:
    if minutes is None:
        return None

    minutes = max(0, min(1439, int(minutes)))
    return time(hour=minutes // 60, minute=minutes % 60)


def time_to_minutes(value: time) -> int:
    return value.hour * 60 + value.minute


@dataclass(frozen=True, kw_only=True)
class AquaelTimeEntityDescription(TimeEntityDescription):
    display_name: str
    value_key: str
    setter: Callable[[object, int], object]


async def _set_sunrise(entity: object, minutes: int) -> None:
    await entity.coordinator.client.set_sunrise_minutes(minutes)


async def _set_sunset(entity: object, minutes: int) -> None:
    await entity.coordinator.client.set_sunset_minutes(minutes)


TIMES: tuple[AquaelTimeEntityDescription, ...] = (
    AquaelTimeEntityDescription(
        key="sunrise",
        name="Aquael Flow Heater BT Sunrise",
        display_name="Aquael Flow Heater BT Sunrise",
        value_key="sunrise_minutes",
        setter=_set_sunrise,
    ),
    AquaelTimeEntityDescription(
        key="sunset",
        name="Aquael Flow Heater BT Sunset",
        display_name="Aquael Flow Heater BT Sunset",
        value_key="sunset_minutes",
        setter=_set_sunset,
    ),
)


async def async_setup_entry(hass, entry, async_add_entities) -> None:
    coordinator = hass.data["aquael_heater"][entry.entry_id]
    async_add_entities(AquaelTime(coordinator, entry, description) for description in TIMES)


class AquaelTime(AquaelEntity, TimeEntity):
    entity_description: AquaelTimeEntityDescription

    def __init__(self, coordinator, entry, description: AquaelTimeEntityDescription) -> None:
        super().__init__(coordinator, entry, description.key)
        self.entity_description = description
        self._attr_name = description.display_name

    @property
    def native_value(self) -> time | None:
        return minutes_to_time(self.coordinator.data.get(self.entity_description.value_key))

    async def async_set_value(self, value: time) -> None:
        await self.entity_description.setter(self, time_to_minutes(value))
        await self.coordinator.async_request_refresh()
