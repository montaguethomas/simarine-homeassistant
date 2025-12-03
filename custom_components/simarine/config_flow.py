"""Config flow for the Simarine integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
  ConfigFlow,
  ConfigFlowResult,
)
from homeassistant.const import (
  CONF_HOST,
  CONF_SCAN_INTERVAL,
)
from homeassistant.helpers import config_validation as cv

from simarine.client import SimarineClient
from simarine.exceptions import TransportError
from simarine.transport import DEFAULT_TCP_PORT, DEFAULT_UDP_PORT

from .const import CONF_TCP_PORT, CONF_UDP_PORT, DEFAULT_SCAN_INTERVAL, DOMAIN, MIN_SCAN_INTERVAL


_LOGGER = logging.getLogger(__name__)

# ----------------------------------------------------------------------------
# Adjust the data schema to the data that you need
# ----------------------------------------------------------------------------
STEP_USER_DATA_SCHEMA = vol.Schema(
  {
    vol.Required(CONF_HOST): str,
    vol.Optional(CONF_TCP_PORT, default=DEFAULT_TCP_PORT): cv.port,
    vol.Optional(CONF_UDP_PORT, default=DEFAULT_UDP_PORT): cv.port,
    vol.Optional(
      CONF_SCAN_INTERVAL,
      default=DEFAULT_SCAN_INTERVAL,
    ): vol.All(vol.Coerce(int), vol.Clamp(min=MIN_SCAN_INTERVAL)),
  }
)


class SimarineConfigFlow(ConfigFlow, domain=DOMAIN):
  """Handle a config flow for the Simarine Integration."""

  VERSION = 1

  async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
    """Handle the initial step.

    Called when you initiate adding an integration via the UI
    """

    if user_input is not None:
      tcp_kwargs = {
        "host": user_input.get(CONF_HOST),
        "port": user_input.get(CONF_TCP_PORT),
      }
      udp_kwargs = {
        "port": user_input.get(CONF_UDP_PORT),
      }

      try:
        with SimarineClient(tcp_kwargs=tcp_kwargs, udp_kwargs=udp_kwargs, auto_discover=False) as client:
          serial_number, firmware_version = client.get_system_info()
      except TransportError:
        return self.async_abort(reason="cannot_connect")
      except Exception:
        _LOGGER.exception("Unexpected exception")
        return self.async_abort(reason="unknown")

      await self.async_set_unique_id(str(serial_number))
      self._abort_if_unique_id_configured()

      return self.async_create_entry(
        title=f"{DOMAIN.capitalize()} {serial_number} ({user_input.get(CONF_HOST)})",
        data=user_input,
      )

    return self.async_show_form(step_id="user", data_schema=STEP_USER_DATA_SCHEMA)
