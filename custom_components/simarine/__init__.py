"""The Simarine integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.device_registry import DeviceEntry

from .coordinator import SimarineConfigEntry, SimarineCoordinator


_LOGGER = logging.getLogger(__name__)

_PLATFORMS: list[Platform] = [
  Platform.SENSOR,
]


async def async_setup_entry(hass: HomeAssistant, config_entry: SimarineConfigEntry) -> bool:
  """Set up Simarine Integration from a config entry."""

  coordinator = SimarineCoordinator(hass, config_entry)
  await coordinator.async_config_entry_first_refresh()

  if not coordinator.data:
    raise ConfigEntryNotReady

  config_entry.async_on_unload(coordinator.close)

  config_entry.runtime_data = coordinator
  await hass.config_entries.async_forward_entry_setups(config_entry, _PLATFORMS)
  return True


async def async_remove_config_entry_device(hass: HomeAssistant, config_entry: ConfigEntry, device_entry: DeviceEntry) -> bool:
  """Delete device if selected from UI."""
  return True


async def async_unload_entry(hass: HomeAssistant, config_entry: SimarineConfigEntry) -> bool:
  """Unload a config entry."""
  return await hass.config_entries.async_unload_platforms(config_entry, _PLATFORMS)
