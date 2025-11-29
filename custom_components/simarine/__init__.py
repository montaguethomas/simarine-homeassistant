from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import (
  DOMAIN,
  PLATFORMS,
  CONF_UPDATE_INTERVAL,
  CONF_HOST,
  CONF_TCP_PORT,
  CONF_UDP_PORT,
  DEFAULT_UPDATE_INTERVAL,
)
from .coordinator import SimarineCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
  coordinator = SimarineCoordinator(
    hass=hass,
    host=entry.data.get(CONF_HOST),
    tcp_port=entry.data.get(CONF_TCP_PORT),
    udp_port=entry.data.get(CONF_UDP_PORT),
    update_interval=entry.data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL),
  )

  await coordinator.async_config_entry_first_refresh()

  hass.data.setdefault(DOMAIN, {})
  hass.data[DOMAIN][entry.entry_id] = coordinator

  title = f"Simarine {coordinator.data['system_info']['serial_number']} ({entry.data.get(CONF_HOST)})"

  hass.config_entries.async_update_entry(entry, title=title)
  await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
  return True
