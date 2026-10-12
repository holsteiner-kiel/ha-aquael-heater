from __future__ import annotations

import re
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components.bluetooth import BluetoothServiceInfoBleak
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

from .const import CONF_ADDRESS, DEFAULT_NAME, DOMAIN

ADDRESS_RE = re.compile(r"^[0-9A-Fa-f]{2}(:[0-9A-Fa-f]{2}){5}$")


def normalize_address(address: str) -> str:
    return address.strip().upper()


class AquaelConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle an Aquael Heater config flow."""

    VERSION = 1

    async def async_step_bluetooth(
        self, discovery_info: BluetoothServiceInfoBleak
    ) -> FlowResult:
        address = normalize_address(discovery_info.address)

        await self.async_set_unique_id(address)
        self._abort_if_unique_id_configured()

        self.context["title_placeholders"] = {
            "name": discovery_info.name or DEFAULT_NAME,
        }

        return self.async_create_entry(
            title=discovery_info.name or DEFAULT_NAME,
            data={CONF_ADDRESS: address},
        )

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            address = normalize_address(user_input[CONF_ADDRESS])

            if not ADDRESS_RE.match(address):
                errors[CONF_ADDRESS] = "invalid_address"
            else:
                await self.async_set_unique_id(address)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=DEFAULT_NAME,
                    data={CONF_ADDRESS: address},
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_ADDRESS): selector.TextSelector(
                    selector.TextSelectorConfig(type=selector.TextSelectorType.TEXT)
                ),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )
