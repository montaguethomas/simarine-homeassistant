"""DataUpdateCoordinator for the Simarine integration."""

from dataclasses import dataclass
from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from simarine.client import SimarineClient
import simarine.types as simarinetypes

from .const import CONF_TCP_PORT, CONF_UDP_PORT, DOMAIN


_LOGGER = logging.getLogger(__name__)

type SimarineConfigEntry = ConfigEntry[SimarineCoordinator]


@dataclass
class SimarineData:
  """Class to hold your data."""

  firmware_version: str
  serial_number: str
  system_device: simarinetypes.Device
  devices: dict[int, simarinetypes.Device]
  sensors: dict[int, simarinetypes.Sensor]


class SimarineCoordinator(DataUpdateCoordinator[SimarineData]):
  """Simarine coordinator."""

  def __init__(self, hass: HomeAssistant, config_entry: SimarineConfigEntry) -> None:
    """Initialize coordinator."""

    super().__init__(
      hass,
      _LOGGER,
      config_entry=config_entry,
      name=f"{DOMAIN} ({config_entry.unique_id})",
      update_interval=timedelta(seconds=config_entry.data.get(CONF_SCAN_INTERVAL)),
    )

    self._client = None
    self._connected = False

  def _connect(self):
    try:
      _LOGGER.info(f"Connecting to Simarine @ {self.config_entry.data[CONF_HOST]}:{self.config_entry.data[CONF_TCP_PORT]}")
      self._client = SimarineClient(host=self.config_entry.data[CONF_HOST], port=self.config_entry.data[CONF_TCP_PORT], auto_discover=False)
      self._client.open()
      self._connected = True
      _LOGGER.info("Connected to Simarine")

    except Exception as e:
      self._client = None
      self._connected = False
      _LOGGER.warning("Simarine connection failed: %s", e)

  def _disconnect(self):
    if self._client:
      try:
        self._client.close()
      except Exception:
        pass
    self._client = None
    self._connected = False

  def close(self):
    self._disconnect()

  async def _async_setup(self):
    self._connect()
    serial_number, firmware_version = self._client.get_system_info()
    self.data = SimarineData(
      firmware_version=firmware_version,
      serial_number=str(serial_number),
      system_device=self._client.get_system_device(),
      devices=self._client.get_devices(),
      sensors=self._client.get_sensors(),
    )

  async def _async_update_data(self):
    try:
      if not self._connected or not self._client:
        self._connect()

      if not self._connected:
        raise UpdateFailed("Unable to connect to Simarine device")

      data = self.data
      sensors_state = self._client.get_sensors_state()
      for id, state_field in sensors_state.items():
        if id in data.sensors:
          data.sensors[id].state_field = state_field
        else:
          data.sensors[id] = self._client.get_sensor(id)
          if data.sensors[id].device_id not in data.devices:
            data.devices[id] = self._client.get_device(id)
      return data

    except Exception as e:
      _LOGGER.warning("Simarine update failed: %s", e)
      self._disconnect()
      raise UpdateFailed(f"Simarine connection lost: {e}")
