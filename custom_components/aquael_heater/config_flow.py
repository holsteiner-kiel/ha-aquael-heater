from __future__ import annotations

import re
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components import bluetooth
from homeassistant.components.bluetooth import BluetoothServiceInfoBleak
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

from .const import CONF_ADDRESS, DEFAULT_NAME, DOMAIN

ADDRESS_RE = re.compile(r"^[0-9A-Fa-f]{2}(:[0-9A-Fa-f]{2}){5}$")
MANUAL_ENTRY = "__manual__"


def normalize_address(address: str) -> str:
    return address.strip().upper()


def is_aquael_heater(service_info: BluetoothServiceInfoBleak) -> bool:
    name = service_info.name or ""
    return name == "Flow Heater BT"


class AquaelConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle an Aquael Heater config flow."""

    VERSION = 1

    def __init__(self) -> None:
        self._discovered_devices: dict[str, BluetoothServiceInfoBleak] = {}
        self._discovery_info: BluetoothServiceInfoBleak | None = None

    async def async_step_bluetooth(
        self, discovery_info: BluetoothServiceInfoBleak
    ) -> FlowResult:
        address = normalize_address(discovery_info.address)

        await self.async_set_unique_id(address)
        self._abort_if_unique_id_configured()

        self._discovery_info = discovery_info
        self.context["title_placeholders"] = {
            "name": discovery_info.name or DEFAULT_NAME,
        }

        return await self.async_step_bluetooth_confirm()

    async def async_step_bluetooth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        if self._discovery_info is None:
            return await self.async_step_user()

        address = normalize_address(self._discovery_info.address)
        name = self._discovery_info.name or DEFAULT_NAME

        if user_input is not None:
            return self.async_create_entry(
                title=name,
                data={CONF_ADDRESS: address},
            )

        return self.async_show_form(
            step_id="bluetooth_confirm",
            description_placeholders={
                "name": name,
                "address": address,
            },
        )

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        if user_input is not None:
            selected = user_input["device"]
            if selected == MANUAL_ENTRY:
                return await self.async_step_manual()

            discovery_info = self._discovered_devices[selected]
            address = normalize_address(discovery_info.address)

            await self.async_set_unique_id(address)
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=discovery_info.name or DEFAULT_NAME,
                data={CONF_ADDRESS: address},
            )

        await self._async_refresh_discovered_devices()

        if not self._discovered_devices:
            return await self.async_step_manual()

        options: list[selector.SelectOptionDict] = []
        for address, service_info in sorted(self._discovered_devices.items()):
            name = service_info.name or DEFAULT_NAME
            options.append(
                selector.SelectOptionDict(
                    value=address,
                    label=f"{name} ({address})",
                )
            )

        options.append(
            selector.SelectOptionDict(
                value=MANUAL_ENTRY,
                label="Enter BLE address manually",
            )
        )

        schema = vol.Schema(
            {
                vol.Required("device"): selector.SelectSelector(
                    selector.SelectSelectorConfig(options=options)
                ),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
        )

    async def async_step_manual(
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
            step_id="manual",
            data_schema=schema,
            errors=errors,
        )

    async def _async_refresh_discovered_devices(self) -> None:
        await bluetooth.async_request_active_scan(self.hass)

        self._discovered_devices = {
            normalize_address(service_info.address): service_info
            for service_info in bluetooth.async_discovered_service_info(
                self.hass,
                connectable=True,
            )
            if is_aquael_heater(service_info)
        }
