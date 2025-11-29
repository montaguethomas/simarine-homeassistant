from homeassistant import config_entries
import voluptuous as vol
import time

from simarine.client import SimarineClient

from .const import (
  DOMAIN,
  CONF_HOST,
  CONF_TCP_PORT,
  CONF_UDP_PORT,
  CONF_UPDATE_INTERVAL,
  DEFAULT_TCP_PORT,
  DEFAULT_UDP_PORT,
  DEFAULT_UPDATE_INTERVAL,
  DISCOVERY_CACHE_TTL,
)


class SimarineConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
  VERSION = 1

  def __init__(self):
    self._discovered_device = None
    self._last_discovery = 0
    self._manual_overrides = {}

  async def async_step_user(self, user_input=None):
    """Initial configuration step (manual or trigger discovery)."""

    if user_input is not None:
      # Save manual overrides (even if host is blank)
      self._manual_overrides = user_input

      # Blank host → discovery flow
      if not user_input.get(CONF_HOST):
        return await self.async_step_discover()

      # Manual configuration
      return self.async_create_entry(
        title=f"Simarine @ {user_input[CONF_HOST]}",
        data=user_input,
      )

    schema = vol.Schema(
      {
        vol.Optional(CONF_HOST): str,
        vol.Optional(CONF_TCP_PORT, default=DEFAULT_TCP_PORT): int,
        vol.Optional(CONF_UDP_PORT, default=DEFAULT_UDP_PORT): int,
        vol.Optional(CONF_UPDATE_INTERVAL, default=DEFAULT_UPDATE_INTERVAL): vol.All(int, vol.Range(min=2, max=600)),
      }
    )

    return self.async_show_form(step_id="user", data_schema=schema)

  async def async_step_discover(self, user_input=None):
    """Auto-discovery flow using SimarineClient.discover()."""

    # Retry pressed
    if user_input is not None and user_input.get("retry"):
      self._discovered_device = None
      self._last_discovery = 0
      return await self.async_step_discover()

    # Run discovery if cache expired
    now = time.time()
    if not self._discovered_device or (now - self._last_discovery) > DISCOVERY_CACHE_TTL:
      self._discovered_device = await self.hass.async_add_executor_job(
        SimarineClient.discover(udp_kwargs={"port": self._manual_overrides.get(CONF_UDP_PORT, DEFAULT_UDP_PORT)})
      )
      self._last_discovery = now

    # Returns: (host, serial_number, firmware_version)
    host, serial_number, firmware_version = self._discovered_device

    if not host:
      return self.async_show_form(
        step_id="discover",
        errors={"base": "no_devices_found"},
        data_schema=vol.Schema({vol.Optional("retry"): bool}),
      )

    # Merge overrides with discovered values
    config_data = {
      CONF_HOST: host,
      CONF_TCP_PORT: self._manual_overrides.get(CONF_TCP_PORT, DEFAULT_TCP_PORT),
      CONF_UDP_PORT: self._manual_overrides.get(CONF_UDP_PORT, DEFAULT_UDP_PORT),
      CONF_UPDATE_INTERVAL: self._manual_overrides.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL),
    }

    if serial_number:
      await self.async_set_unique_id(serial_number)
      self._abort_if_unique_id_configured()

    return self.async_create_entry(
      title=f"Simarine {serial_number} ({host})",
      data=config_data,
    )
